from __future__ import annotations

import logging

from .provider import LLMProvider

logger = logging.getLogger(__name__)


class OpenRouterProvider(LLMProvider):
    """LLMProvider backed by OpenRouter, called through the official OpenAI SDK
    (OpenRouter exposes an OpenAI-compatible ``/v1/chat/completions`` endpoint).
    """

    def __init__(self, api_key: str | None, base_url: str, model: str):
        if not api_key:
            raise RuntimeError(
                "OPENROUTER_API_KEY is not configured; the orchestrator cannot generate answers."
            )

        from openai import OpenAI

        self._client = OpenAI(api_key=api_key, base_url=base_url)
        self._model = model

    def generate_response(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        max_tokens: int = 1024,
        temperature: float = 0.2,
    ) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )

        choice = response.choices[0]
        content = choice.message.content
        if not content:
            logger.warning("OpenRouter model '%s' returned an empty response", self._model)
            return ""
        return content
