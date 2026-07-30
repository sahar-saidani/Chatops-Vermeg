from __future__ import annotations

import logging
from dataclasses import dataclass

from agents.runner import AgentRunner
from config import Settings
from data.canonical_events_repository import CanonicalEventsRepository
from data.conversation_history_client import ConversationHistoryClient, ConversationTurn
from intent.classifier import IntentClassifier
from intent.models import Intent, RequestMode
from llm.analyzer import ResponseAnalyzer

logger = logging.getLogger(__name__)


@dataclass
class OrchestratorResponse:
    answer: str
    mode: RequestMode
    agent_keys: list[str]
    environment: str | None
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
    ):
        self._settings = settings
        self._classifier = classifier
        self._runner = runner
        self._events_repository = events_repository
        self._analyzer = analyzer
        self._conversation_client = conversation_client

    def handle_request(
        self,
        user_id: str,
        user_message: str,
    ) -> OrchestratorResponse:

        intent = self._classifier.classify(user_message)

        logger.info(
            "Detected intent mode=%s agents=%s environment=%s",
            intent.mode,
            intent.agent_keys,
            intent.environment,
        )

        if not intent.agent_keys:
            answer = (
                "I couldn't determine which system this request relates to "
                "(Git, Jenkins, Jira, Installation, Infrastructure or Logs). "
                "Please specify the target system."
            )

            return self._finalize(
                user_id,
                user_message,
                answer,
                intent,
                saved=False,
            )

        if intent.requires_agent_execution:
            events = self._run_realtime_workflow(intent)
        else:
            events = self._run_historical_workflow(intent)

        answer = self._analyzer.analyze(user_message, events)

        saved = self._save_conversation(
            user_id,
            user_message,
            answer,
            intent,
        )

        return self._finalize(
            user_id,
            user_message,
            answer,
            intent,
            saved,
        )

    # ------------------------------------------------------------------
    # REAL TIME
    # ------------------------------------------------------------------

    def _run_realtime_workflow(self, intent: Intent) -> list:

        all_events = []

        for agent_key in intent.agent_keys:

            params = dict(intent.raw_params)

            if intent.environment:
                params.setdefault("environment", intent.environment)

            result = self._runner.run(agent_key, params)

            if not result.success:

                logger.error(
                    "Agent '%s' failed (steps_run=%s). stderr=%s",
                    agent_key,
                    result.steps_run,
                    result.stderr_tail,
                )

                continue

            logger.info(
                "Waiting for canonical_events generated after %s",
                result.launched_at,
            )

            fresh_event = self._events_repository.wait_for_fresh_data(
                agent_key=agent_key,
                since=result.launched_at,
                environment=intent.environment,
            )

            #
            # Important:
            # if timeout occurs, perform one last read before giving up.
            #
            if fresh_event is None:

                logger.warning(
                    "Timeout waiting for fresh data for '%s'. "
                    "Checking database one final time...",
                    agent_key,
                )

                recent = self._events_repository.find_recent(
                    [agent_key],
                    environment=intent.environment,
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
                    agent_key,
                )

                continue

            logger.info(
                "Fresh event received for '%s'",
                agent_key,
            )

            all_events.extend(
                self._events_repository.find_recent(
                    [agent_key],
                    environment=intent.environment,
                    limit=20,
                )
            )

        return all_events

    # ------------------------------------------------------------------
    # HISTORICAL
    # ------------------------------------------------------------------

    def _run_historical_workflow(self, intent: Intent):

        since = None

        if intent.time_range_days:
            from datetime import timedelta

            from data.canonical_events_repository import utcnow

            since = utcnow() - timedelta(days=intent.time_range_days)

        return self._events_repository.find_recent(
            intent.agent_keys,
            since=since,
            environment=intent.environment,
            limit=200,
        )

    # ------------------------------------------------------------------

    def _save_conversation(
        self,
        user_id,
        user_message,
        answer,
        intent,
    ) -> bool:

        turn = ConversationTurn(
            user_id=user_id,
            request_mode=intent.mode.value,
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
    ) -> OrchestratorResponse:

        return OrchestratorResponse(
            answer=answer,
            mode=intent.mode,
            agent_keys=intent.agent_keys,
            environment=intent.environment,
            conversation_saved=saved,
        )