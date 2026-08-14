from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from agents.runner import AgentRunner
from config import Settings
from data.canonical_events_repository import CanonicalEventsRepository
from data.conversation_history_client import (
    ConversationHistoryClient,
    ConversationTurn,
)
from execution.aggregator import ResultAggregator
from execution.gateway import SubprocessAgentExecutionGateway
from execution.models import ExecutionPlan
from intent.classifier import IntentClassifier
from intent.models import Intent, RequestMode
from llm.analyzer import ResponseAnalyzer
from routing.tenant_machine_registry import (
    TenantMachineRegistry,
    TenantMachineRoute,
)

logger = logging.getLogger(__name__)


@dataclass
class OrchestratorResponse:
    answer: str
    mode: RequestMode
    tenant: str | None
    machine_reference: str | None
    agent_keys: list[str]
    environment: str | None
    task_id: str | None
    conversation_saved: bool
    # Per-agent outcome: [{"agent": "git", "status": "FAILED", "error": "..."}].
    # Agent failures were previously only logged server-side, so a client
    # received an answer with no way to distinguish "the agent broke" from
    # "the agent found nothing". Empty for Mode 2 (no agents launched).
    agent_statuses: list[dict] = field(default_factory=list)


class Orchestrator:
    """
    LLM Orchestrator.

    Flow:

        User request
            ↓
        Intent classification
            ↓
        Tenant + environment + machine + OS routing
            ↓
        ExecutionPlan
            ↓
        Python Agent
            ↓
        RabbitMQ / processing pipeline
            ↓
        canonical_events
            ↓
        Strict scope filtering
            ↓
        LLM
            ↓
        Final answer

    Important:
        A realtime request must only use data generated for the
        current execution and matching the current routing scope.

        Scope:
            tenant
            environment
            machine_reference
            operating_system
            agent
    """

    def __init__(
        self,
        settings: Settings,
        classifier: IntentClassifier,
        runner: AgentRunner,
        events_repository: CanonicalEventsRepository,
        analyzer: ResponseAnalyzer,
        conversation_client: ConversationHistoryClient,
        tenant_registry: TenantMachineRegistry,
    ):
        self._settings = settings
        self._classifier = classifier
        self._runner = runner
        self._events_repository = events_repository
        self._analyzer = analyzer
        self._conversation_client = conversation_client
        self._tenant_registry = tenant_registry

        self._execution_gateway = SubprocessAgentExecutionGateway(
            runner
        )

        self._result_aggregator = ResultAggregator()

    # ============================================================
    # REQUEST
    # ============================================================

    def handle_request(
        self,
        user_id: str,
        user_message: str,
    ) -> OrchestratorResponse:

        intent = self._classifier.classify(user_message)

        route = self._resolve_route(intent)

        if route is None:
            answer = self._clarify_tenant()

            return self._finalize(
                user_id=user_id,
                user_message=user_message,
                answer=answer,
                intent=intent,
                saved=False,
                tenant=intent.tenant,
                task_id=None,
                machine_reference=None,
                environment=intent.environment,
            )

        resolved_tenant = route.tenant

        logger.info(
            "Detected intent "
            "mode=%s tenant=%s agents=%s environment=%s "
            "machine=%s os=%s",
            intent.mode,
            resolved_tenant,
            intent.agent_keys,
            intent.environment,
            route.machine_reference,
            route.operating_system,
        )

        # ========================================================
        # No agent detected
        # ========================================================

        if not intent.agent_keys:
            answer = (
                "I couldn't determine which system this request relates to "
                "(Git, Jenkins, Installation, Infrastructure or Logs). "
                "Please specify the target system."
            )

            return self._finalize(
                user_id=user_id,
                user_message=user_message,
                answer=answer,
                intent=intent,
                saved=False,
                tenant=resolved_tenant,
                task_id=None,
                machine_reference=route.machine_reference,
                environment=intent.environment or route.environment,
            )

        # ========================================================
        # Build execution plan
        # ========================================================

        plan = self._build_plan(
            intent=intent,
            route=route,
        )

        logger.info(
            "Execution plan created | "
            "task_id=%s tenant=%s environment=%s "
            "machine=%s os=%s agents=%s",
            plan.task_id,
            plan.tenant,
            plan.environment,
            plan.machine_reference,
            plan.operating_system,
            plan.agent_keys,
        )

        # ========================================================
        # Execute workflow
        # ========================================================

        if intent.requires_agent_execution:
            events = self._run_realtime_workflow(
                plan=plan,
                intent=intent,
            )
        else:
            events = self._run_historical_workflow(
                plan=plan,
                intent=intent,
            )

        # ========================================================
        # Build isolated LLM context
        # ========================================================

        context = self._result_aggregator.build_context(
            plan.task_id
        )

        context = dict(context or {})

        # The resolved routing scope is authoritative.
        #
        # Do NOT rely only on the intent because values such as
        # DEV can come from TenantMachineRegistry.

        context.update(
            {
                "tenant": plan.tenant,
                "environment": plan.environment,
                "machine_reference": plan.machine_reference,
                "operating_system": plan.operating_system,
                "requested_agents": plan.agent_keys,
                "request_mode": intent.mode.value,
                "task_id": plan.task_id,
            }
        )

        logger.info(
            "Generating LLM response | "
            "tenant=%s | environment=%s | machine=%s | "
            "os=%s | agents=%s | events=%d",
            plan.tenant,
            plan.environment,
            plan.machine_reference,
            plan.operating_system,
            plan.agent_keys,
            len(events),
        )

        # ========================================================
        # LLM analysis
        # ========================================================

        answer = self._analyzer.analyze(
            user_message=user_message,
            events=events,
            context=context,
        )

        # ========================================================
        # Save conversation
        # ========================================================

        saved = self._save_conversation(
            user_id=user_id,
            user_message=user_message,
            answer=answer,
            intent=intent,
            tenant=plan.tenant,
            environment=plan.environment,
        )

        # ========================================================
        # Final response
        # ========================================================

        return self._finalize(
            user_id=user_id,
            user_message=user_message,
            answer=answer,
            intent=intent,
            saved=saved,
            tenant=plan.tenant,
            task_id=plan.task_id,
            machine_reference=plan.machine_reference,
            environment=plan.environment,
            agent_statuses=self._result_aggregator.agent_statuses(plan.task_id),
        )

    # ============================================================
    # REAL TIME
    # ============================================================

    def _run_realtime_workflow(
        self,
        plan: ExecutionPlan,
        intent: Intent,
    ) -> list:

        all_events = []

        self._result_aggregator.register(plan)

        results = self._execution_gateway.execute(plan)

        for result in results:

            self._result_aggregator.record(result)

            if result.status != "SUCCESS":

                logger.error(
                    "Agent '%s' failed for task '%s'. error=%s",
                    result.agent,
                    result.task_id,
                    result.error,
                )

                continue

            launched_at_raw = result.data.get("launched_at")

            if not launched_at_raw:
                logger.error(
                    "Agent '%s' succeeded but did not provide "
                    "'launched_at'. Cannot safely identify fresh events.",
                    result.agent,
                )
                continue

            try:
                launched_at = datetime.fromisoformat(
                    launched_at_raw
                )
            except (TypeError, ValueError):
                logger.exception(
                    "Invalid launched_at value from agent '%s': %r",
                    result.agent,
                    launched_at_raw,
                )
                continue

            logger.info(
                "Waiting for canonical_events generated after %s "
                "for tenant=%s environment=%s machine=%s os=%s agent=%s",
                launched_at,
                plan.tenant,
                plan.environment,
                plan.machine_reference,
                plan.operating_system,
                result.agent,
            )

            # ====================================================
            # Wait for fresh event
            # ====================================================

            fresh_event = self._events_repository.wait_for_fresh_data(
                agent_key=result.agent,
                since=launched_at,
                environment=plan.environment,
                tenant=plan.tenant,
            )

            if fresh_event is not None:

                # ------------------------------------------------
                # IMPORTANT
                #
                # wait_for_fresh_data currently filters by:
                #   agent
                #   timestamp
                #   environment
                #   tenant
                #
                # We perform an additional scope validation here
                # before passing anything to the LLM.
                # ------------------------------------------------

                if self._event_matches_plan(
                    event=fresh_event,
                    plan=plan,
                ):
                    logger.info(
                        "Fresh event accepted for '%s' | "
                        "tenant=%s environment=%s machine=%s os=%s",
                        result.agent,
                        plan.tenant,
                        plan.environment,
                        plan.machine_reference,
                        plan.operating_system,
                    )

                    all_events.append(fresh_event)

                else:
                    logger.warning(
                        "Fresh event rejected because it does not "
                        "match the current execution scope | "
                        "tenant=%s environment=%s machine=%s os=%s",
                        plan.tenant,
                        plan.environment,
                        plan.machine_reference,
                        plan.operating_system,
                    )

                continue

            # ====================================================
            # Timeout fallback
            # ====================================================

            logger.warning(
                "Timeout waiting for fresh data for '%s'. "
                "Checking database one final time...",
                result.agent,
            )

            recent = self._events_repository.find_recent(
                [result.agent],
                environment=plan.environment,
                tenant=plan.tenant,
                limit=20,
            )

            fresh_recent = []

            for event in recent:

                if not self._event_is_newer_than(
                    event,
                    launched_at,
                ):
                    continue

                if not self._event_matches_plan(
                    event,
                    plan,
                ):
                    logger.warning(
                        "Ignoring stale/out-of-scope event during "
                        "realtime fallback | "
                        "tenant=%s environment=%s machine=%s os=%s",
                        plan.tenant,
                        plan.environment,
                        plan.machine_reference,
                        plan.operating_system,
                    )
                    continue

                fresh_recent.append(event)

            if fresh_recent:

                logger.info(
                    "Found %d fresh event(s) after timeout "
                    "for the current execution.",
                    len(fresh_recent),
                )

                all_events.extend(
                    fresh_recent
                )

                continue

            logger.warning(
                "No fresh canonical_events found for '%s' "
                "within the current execution scope.",
                result.agent,
            )

        return all_events

    # ============================================================
    # EVENT VALIDATION
    # ============================================================

    @staticmethod
    def _event_is_newer_than(
        event,
        launched_at: datetime,
    ) -> bool:

        try:
            event_timestamp = event.message_timestamp

            if event_timestamp.tzinfo is None:
                event_timestamp = event_timestamp.replace(
                    tzinfo=launched_at.tzinfo
                )

            return event_timestamp >= launched_at

        except Exception:
            logger.warning(
                "Unable to validate canonical event timestamp. "
                "Ignoring event."
            )
            return False

    @staticmethod
    def _event_matches_plan(
        event,
        plan: ExecutionPlan,
    ) -> bool:
        """
        Validate that a canonical event belongs to the current
        execution scope.

        This prevents contamination such as:

            MAIF / CentOS / Linux / Prometheus

        being returned for:

            MAIF / DEV / windows-local / Windows / psutil
        """

        event_data = event.data or {}

        event_tenant = (
            event_data.get("tenant")
            or getattr(event, "tenant", None)
        )

        event_environment = (
            event.environment
            or event_data.get("environment")
        )

        event_machine = (
            event_data.get("machine_reference")
            or event_data.get("machine")
            or event_data.get("target")
        )

        event_os = (
            event_data.get("operating_system")
            or event_data.get("os")
        )

        # --------------------------------------------------------
        # Tenant
        # --------------------------------------------------------

        if (
            event_tenant
            and plan.tenant
            and str(event_tenant).lower()
            != str(plan.tenant).lower()
        ):
            return False

        # --------------------------------------------------------
        # Environment
        # --------------------------------------------------------

        if (
            event_environment
            and plan.environment
            and str(event_environment).lower()
            != str(plan.environment).lower()
        ):
            return False

        # --------------------------------------------------------
        # Machine
        # --------------------------------------------------------
        #
        # For realtime requests, if the event contains a machine
        # identifier, it MUST match the requested machine.
        #
        # This is the critical protection against:
        #
        #   MAIF-WINDOWS-01
        #
        # receiving:
        #
        #   MAIF-CENTOS-01
        #

        if event_machine and plan.machine_reference:

            expected_machine = str(
                plan.machine_reference
            ).lower()

            actual_machine = str(
                event_machine
            ).lower()

            # Registry may use "windows-local" while the
            # infrastructure event contains a concrete target
            # such as MAIF-DEV-01 or MAIF-WINDOWS-01.
            #
            # Therefore accept windows-local only when the event
            # itself is explicitly marked as local Windows.
            if expected_machine == "windows-local":

                local_machine_values = {
                    "windows-local",
                    "windows",
                    "maif-windows-01",
                    "maif-dev-01",
                }

                if actual_machine not in local_machine_values:
                    return False

            elif actual_machine != expected_machine:
                return False

        # --------------------------------------------------------
        # Operating system
        # --------------------------------------------------------

        if event_os and plan.operating_system:

            if (
                str(event_os).upper()
                != str(plan.operating_system).upper()
            ):
                return False

        return True

    # ============================================================
    # HISTORICAL
    # ============================================================

    def _run_historical_workflow(
        self,
        plan: ExecutionPlan,
        intent: Intent,
    ):

        since = None

        if intent.time_range_days:

            from data.canonical_events_repository import utcnow

            since = utcnow() - timedelta(
                days=intent.time_range_days
            )

        events = self._events_repository.find_recent(
            intent.agent_keys,
            since=since,
            environment=plan.environment,
            tenant=plan.tenant,
            limit=200,
        )

        # Historical data can contain multiple machines.
        # Keep only events belonging to the requested scope when
        # the event exposes machine / OS information.

        filtered_events = []

        for event in events:

            if self._event_matches_plan(
                event,
                plan,
            ):
                filtered_events.append(event)

        logger.info(
            "Historical workflow returned %d/%d events "
            "after scope filtering.",
            len(filtered_events),
            len(events),
        )

        return filtered_events

    # ============================================================
    # PLAN
    # ============================================================

    def _build_plan(
        self,
        intent: Intent,
        route: TenantMachineRoute,
    ) -> ExecutionPlan:

        environment = (
            intent.environment
            or route.environment
        )

        operating_system = (
            route.operating_system
        )

        return ExecutionPlan.create(
            tenant=route.tenant,
            machine_reference=route.machine_reference,
            environment=environment,
            agent_keys=intent.agent_keys,
            operating_system=operating_system,
            action=intent.action,
            parameters={
                **intent.raw_params,

                # Routing is authoritative.
                "tenant": route.tenant,
                "environment": environment,
                "environment_type": route.environment_type,
                "machine_reference": route.machine_reference,
                "operating_system": operating_system,

                # Repo/branch for the git agent. The classifier only injects
                # these when the tenant is named explicitly in the message
                # text; when it falls back to DEFAULT_TENANT here instead,
                # intent.raw_params never had them. route is always resolved
                # by this point regardless of how tenant was determined, so
                # this is the one place guaranteed not to skip them.
                **({"repo": route.repo} if route.repo else {}),
                **({"branch": route.branch} if route.branch else {}),

                # Transport, kept separate from machine identity so the
                # identity can stay the real one recorded in canonical_events.
                "local_execution": route.local_execution,
            },
        )

    # ============================================================
    # ROUTING
    # ============================================================

    def _resolve_route(
        self,
        intent: Intent,
    ) -> TenantMachineRoute | None:

        if intent.tenant:

            return self._tenant_registry.resolve(
                intent.tenant
            )

        if self._settings.default_tenant:

            return self._tenant_registry.resolve(
                self._settings.default_tenant
            )

        return None

    def _clarify_tenant(self) -> str:

        tenants = ", ".join(
            self._tenant_registry.available_tenants
        )

        return (
            "I need a tenant/client to route this request. "
            f"Available tenants: {tenants}."
        )

    # ============================================================
    # CONVERSATION
    # ============================================================

    def _save_conversation(
        self,
        user_id,
        user_message,
        answer,
        intent,
        tenant,
        environment,
    ) -> bool:

        turn = ConversationTurn(
            user_id=user_id,
            request_mode=intent.mode.value,
            tenant=tenant,
            agent_keys=intent.agent_keys,
            user_message=user_message,
            assistant_response=answer,
            environment=environment,
        )

        return self._conversation_client.save(
            turn
        )

    # ============================================================
    # FINAL RESPONSE
    # ============================================================

    @staticmethod
    def _finalize(
        user_id,
        user_message,
        answer,
        intent,
        saved,
        tenant,
        task_id,
        machine_reference,
        environment,
        agent_statuses=None,
    ) -> OrchestratorResponse:

        return OrchestratorResponse(
            answer=answer,
            mode=intent.mode,
            tenant=tenant,
            machine_reference=machine_reference,
            agent_keys=intent.agent_keys,
            environment=environment,
            task_id=task_id,
            conversation_saved=saved,
            agent_statuses=agent_statuses or [],
        )