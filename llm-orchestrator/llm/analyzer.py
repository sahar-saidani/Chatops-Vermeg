from __future__ import annotations

import json
import logging

from config import Settings
from data.canonical_events_repository import CanonicalEvent

from .openrouter_provider import OpenRouterProvider
from .provider import LLMProvider

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are the ChatOps VERMEG assistant. You analyze technical events "
    "collected by DevOps agents (Git, Jenkins, Jira, Installation, "
    "Infrastructure, Logs) and answer the user's question clearly and "
    "concisely, in the same language the user wrote in. Base your answer "
    "strictly on the provided event data; if the data does not answer the "
    "question, say so explicitly instead of guessing."
)


class ResponseAnalyzer:
    """Generates the final natural-language answer from canonical_events data.

    Depends only on the generic ``LLMProvider`` interface. By default it
    builds an ``OpenRouterProvider`` from ``settings``, but a provider can be
    injected directly (e.g. in tests, or to swap in a different vendor
    without touching this class or the orchestrator).
    """

    def __init__(self, settings: Settings, provider: LLMProvider | None = None):
        self._provider = provider or OpenRouterProvider(
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
            model=settings.openrouter_model,
        )

    def analyze(self, user_message: str, events: list[CanonicalEvent]) -> str:
        if not events:
            payload = "No matching data was found in canonical_events for this request."
        else:
            payload = json.dumps(
                [
                    {
                        "agent_key": event.agent_key,
                        "environment": event.environment,
                        "message_timestamp": event.message_timestamp.isoformat(),
                        "data": event.data,
                    }
                    for event in events
                ],
                default=str,
            )

        user_prompt = (
            f"User question: {user_message}\n\n"
            f"Event data (JSON, {len(events)} event(s)):\n{payload}"
        )

        return self._provider.generate_response(
            SYSTEM_PROMPT, user_prompt, max_tokens=1024, temperature=0.2
        )
