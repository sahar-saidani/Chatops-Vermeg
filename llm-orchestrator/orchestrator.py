from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta

from agents.runner import AgentRunner
from config import Settings
from data.canonical_events_repository import CanonicalEventsRepository
from data.conversation_history_client import ConversationHistoryClient, ConversationTurn
from execution.aggregator import ResultAggregator
from execution.gateway import SubprocessAgentExecutionGateway
from execution.models import ExecutionPlan
from intent.classifier import IntentClassifier
from intent.models import Intent, RequestMode
from llm.analyzer import ResponseAnalyzer
from routing.tenant_machine_registry import TenantMachineRegistry, TenantMachineRoute

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


class Orchestrator:
    """
    LLM Orchestrator.

    Flow:

        Intent
            ↓
        Launch Python Agent
            ↓
        RabbitMQ
            ↓
        Java Data Processing Agent
            ↓
        canonical_events
            ↓
        LLM
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
        self._execution_gateway = SubprocessAgentExecutionGateway(runner)
        self._result_aggregator = ResultAggregator()

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
                user_id,
                user_message,
                answer,
                intent,
                saved=False,
                tenant=intent.tenant,
                task_id=None,
                machine_reference=None,
            )

        resolved_tenant = route.tenant

        logger.info(
            "Detected intent mode=%s tenant=%s agents=%s environment=%s",
            intent.mode,
            resolved_tenant,
            intent.agent_keys,
            intent.environment,
        )

        if not intent.agent_keys:
            answer = (
                "I couldn't determine which system this request relates to "
                "(Git, Jenkins, Installation, Infrastructure or Logs). "
                "Please specify the target system."
            )

            return self._finalize(
                user_id,
                user_message,
                answer,
                intent,
                saved=False,
                tenant=resolved_tenant,
                task_id=None,
                machine_reference=route.machine_reference,
            )

        plan = self._build_plan(intent, route)

        if intent.requires_agent_execution:
            events = self._run_realtime_workflow(plan, intent)
        else:
            events = self._run_historical_workflow(plan, intent)

        context = self._result_aggregator.build_context(plan.task_id)

        answer = self._analyzer.analyze(user_message, events, context=context)

        saved = self._save_conversation(
            user_id,
            user_message,
            answer,
            intent,
            tenant=resolved_tenant,
        )

        return self._finalize(
            user_id,
            user_message,
            answer,
            intent,
            saved,
            tenant=resolved_tenant,
            task_id=plan.task_id,
            machine_reference=route.machine_reference,
        )

    # ------------------------------------------------------------------
    # REAL TIME
    # ------------------------------------------------------------------

    def _run_realtime_workflow(self, plan: ExecutionPlan, intent: Intent) -> list:

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

            logger.info(
                "Waiting for canonical_events generated after %s",
                result.data["launched_at"],
            )

            launched_at = datetime.fromisoformat(result.data["launched_at"])

            fresh_event = self._events_repository.wait_for_fresh_data(
                agent_key=result.agent,
                since=launched_at,
                environment=intent.environment,
                tenant=plan.tenant,
            )

            #
            # Important:
            # if timeout occurs, perform one last read before giving up.
            #
            if fresh_event is None:

                logger.warning(
                    "Timeout waiting for fresh data for '%s'. "
                    "Checking database one final time...",
                    result.agent,
                )

                recent = self._events_repository.find_recent(
                    [result.agent],
                    environment=intent.environment,
                    tenant=plan.tenant,
                    limit=20,
                )

                if recent:
                    logger.info(
                        "Found %d event(s) after timeout. Continuing.",
                        len(recent),
                    )
                    all_events.extend(recent)
                    continue

                logger.warning(
                    "No canonical_events found for '%s'.",
                    result.agent,
                )

                continue

            logger.info(
                "Fresh event received for '%s'",
                result.agent,
            )

            all_events.extend(
                self._events_repository.find_recent(
                    [result.agent],
                    environment=intent.environment,
                    tenant=plan.tenant,
                    limit=20,
                )
            )

        return all_events

    # ------------------------------------------------------------------
    # HISTORICAL
    # ------------------------------------------------------------------

    def _run_historical_workflow(self, plan: ExecutionPlan, intent: Intent):

        since = None

        if intent.time_range_days:
            from data.canonical_events_repository import utcnow

            since = utcnow() - timedelta(days=intent.time_range_days)

        return self._events_repository.find_recent(
            intent.agent_keys,
            since=since,
            environment=intent.environment,
            tenant=plan.tenant,
            limit=200,
        )

    def _build_plan(self, intent: Intent, route: TenantMachineRoute) -> ExecutionPlan:
        return ExecutionPlan.create(
            tenant=route.tenant,
            machine_reference=route.machine_reference,
            environment=intent.environment or route.environment,
            agent_keys=intent.agent_keys,
            action=intent.action,
            parameters={**intent.raw_params, "environment": intent.environment or route.environment},
        )

    def _resolve_route(self, intent: Intent) -> TenantMachineRoute | None:
        if intent.tenant:
            return self._tenant_registry.resolve(intent.tenant)
        if self._settings.default_tenant:
            return self._tenant_registry.resolve(self._settings.default_tenant)
        return None

    def _clarify_tenant(self) -> str:
        tenants = ", ".join(self._tenant_registry.available_tenants)
        return (
            "I need a tenant/client to route this request. "
            f"Available tenants: {tenants}."
        )

    # ------------------------------------------------------------------

    def _save_conversation(
        self,
        user_id,
        user_message,
        answer,
        intent,
        tenant,
    ) -> bool:

        turn = ConversationTurn(
            user_id=user_id,
            request_mode=intent.mode.value,
            tenant=tenant,
            agent_keys=intent.agent_keys,
            user_message=user_message,
            assistant_response=answer,
            environment=intent.environment,
        )

        return self._conversation_client.save(turn)

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
    ) -> OrchestratorResponse:

        return OrchestratorResponse(
            answer=answer,
            mode=intent.mode,
            tenant=tenant,
            machine_reference=machine_reference,
            agent_keys=intent.agent_keys,
            environment=intent.environment,
            task_id=task_id,
            conversation_saved=saved,
        )