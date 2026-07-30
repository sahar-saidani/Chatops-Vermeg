from __future__ import annotations

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Generic abstraction over a chat-completion LLM backend.

    The orchestrator (via ``ResponseAnalyzer`` and ``LLMIntentFallback``)
    only ever depends on this interface, never on a specific vendor SDK.
    Swapping providers (Anthropic, OpenRouter, OpenAI, a local model, ...)
    means writing a new ``LLMProvider`` implementation and wiring it up in
    ``api.py`` - nothing else in the orchestrator changes.
    """

    @abstractmethod
    def generate_response(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        max_tokens: int = 1024,
        temperature: float = 0.2,
    ) -> str:
        """Return the model's plain-text answer for a system/user prompt pair."""
        raise NotImplementedError
