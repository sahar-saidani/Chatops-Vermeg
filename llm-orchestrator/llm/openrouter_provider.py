
from __future__ import annotations
from openai import AuthenticationError, OpenAI
import logging

from openai import (
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    OpenAI,
    OpenAIError,
    RateLimitError,
)

from .provider import LLMProvider

logger = logging.getLogger(__name__)


class OpenRouterProvider(LLMProvider):
    """LLM provider using OpenRouter through its OpenAI-compatible API."""

    def __init__(
        self,
        api_key: str | None,
        base_url: str,
        model: str,
        fallback_model: str | None = None,
        timeout: float = 30.0,
    ):
        if not api_key:
            raise RuntimeError("OPENROUTER_API_KEY is not configured.")

        if not base_url:
            raise RuntimeError("OPENROUTER_BASE_URL is not configured.")

        if not model:
            raise RuntimeError("OPENROUTER_MODEL is not configured.")

        self._api_key = api_key.strip()
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._fallback_model = fallback_model.strip() if fallback_model else None
        self._timeout = timeout

        self._client = OpenAI(
            api_key=self._api_key,
            base_url=self._base_url,
            timeout=self._timeout,
        )

        logger.info(
            "OpenRouter provider initialized: model=%s base_url=%s",
            self._model,
            self._base_url,
        )

    def generate_response(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        max_tokens: int = 1024,
        temperature: float = 0.2,
    ) -> str:
        try:
            return self._generate_with_model(
                self._model,
                system_prompt,
                user_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
            )
        except Exception as exc:
            if self._is_configuration_error(exc):
                raise RuntimeError(
                    "OpenRouter authentication or configuration failed. "
                    "Check OPENROUTER_API_KEY, OPENROUTER_BASE_URL, and OPENROUTER_MODEL."
                ) from exc

            if self._fallback_model and self._fallback_model != self._model:
                logger.warning(
                    "Primary OpenRouter model failed; trying fallback model=%s",
                    self._fallback_model,
                )
                try:
                    return self._generate_with_model(
                        self._fallback_model,
                        system_prompt,
                        user_prompt,
                        max_tokens=max_tokens,
                        temperature=temperature,
                    )
                except Exception as fallback_exc:
                    if self._is_configuration_error(fallback_exc):
                        raise RuntimeError(
                            "OpenRouter authentication or configuration failed. "
                            "Check OPENROUTER_API_KEY, OPENROUTER_BASE_URL, and OPENROUTER_MODEL."
                        ) from fallback_exc
                    raise RuntimeError(
                        "OpenRouter response generation failed. Please try again shortly."
                    ) from fallback_exc

            raise RuntimeError(
                "OpenRouter response generation failed. Please try again shortly."
            ) from exc

    def _generate_with_model(
        self,
        model: str,
        system_prompt: str,
        user_prompt: str,
        *,
        max_tokens: int,
        temperature: float,
    ) -> str:
        logger.info("OpenRouter request using model=%s", model)

        response = self._client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
        )

        if not getattr(response, "choices", None):
            raise RuntimeError("OpenRouter returned no choices.")

        choice = response.choices[0]
        content = choice.message.content

        if not content or not str(content).strip():
            raise RuntimeError("OpenRouter returned an empty response.")

        return str(content).strip()

    @staticmethod
    def _is_configuration_error(exc: Exception) -> bool:
        if isinstance(exc, AuthenticationError):
            return True

        status_code = getattr(exc, "status_code", None)
        return status_code in {400, 401, 403, 404}


# Backward compatibility
AgentRouterProvider = OpenRouterProvider

