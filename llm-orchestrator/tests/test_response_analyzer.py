from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import httpx

from data.canonical_events_repository import CanonicalEvent
from llm.analyzer import ResponseAnalyzer
from llm.openrouter_provider import OpenRouterProvider
from llm.provider import LLMProvider


class StubProvider(LLMProvider):
    def __init__(self, response: str = ""):
        self.response = response
        self.calls: list[dict] = []

    def generate_response(self, system_prompt: str, user_prompt: str, *, max_tokens: int = 1024, temperature: float = 0.2) -> str:
        self.calls.append(
            {
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "max_tokens": max_tokens,
                "temperature": temperature,
            }
        )
        return self.response


class FailingProvider(LLMProvider):
    def generate_response(self, system_prompt: str, user_prompt: str, *, max_tokens: int = 1024, temperature: float = 0.2) -> str:
        raise RuntimeError("OpenRouter unavailable")


def make_event(agent_key: str = "jenkins") -> CanonicalEvent:
    return CanonicalEvent(
        id="event-1",
        agent_key=agent_key,
        message_timestamp=datetime.now(timezone.utc),
        environment="DEV",
        data={"status": "FAILED", "error": "Job aborted before execution"},
        created_at=datetime.now(timezone.utc),
    )


def test_provider_uses_primary_model_and_returns_text():
    fake_client = MagicMock()
    fake_client.chat.completions.create.return_value = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="Primary answer"))]
    )

    with patch("llm.openrouter_provider.OpenAI", return_value=fake_client):
        provider = OpenRouterProvider(
            api_key="sk-test",
            base_url="https://openrouter.ai/api/v1",
            model="primary-model",
            fallback_model="fallback-model",
        )
        result = provider.generate_response("system", "user")

    assert result == "Primary answer"
    assert fake_client.chat.completions.create.call_count == 1


def test_provider_falls_back_to_secondary_model_on_timeout():
    fake_client = MagicMock()
    fake_client.chat.completions.create.side_effect = [
        APITimeoutError(request=httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions")),
        SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="Fallback answer"))]),
    ]

    with patch("llm.openrouter_provider.OpenAI", return_value=fake_client):
        provider = OpenRouterProvider(
            api_key="sk-test",
            base_url="https://openrouter.ai/api/v1",
            model="primary-model",
            fallback_model="fallback-model",
        )
        result = provider.generate_response("system", "user")

    assert result == "Fallback answer"
    assert fake_client.chat.completions.create.call_count == 2


def test_analyzer_returns_fallback_when_provider_fails():
    analyzer = ResponseAnalyzer(
        settings=SimpleNamespace(
            openrouter_api_key="test-key",
            openrouter_base_url="https://openrouter.ai/api/v1",
            openrouter_model="primary-model",
            openrouter_fallback_model="fallback-model",
        ),
        provider=FailingProvider(),
    )

    result = analyzer.analyze("Explain this failure", [], context={"tenant": "MAIF"})

    assert "temporarily unavailable" in result.lower()


def test_provider_raises_on_authentication_error():
    fake_client = MagicMock()
    fake_client.chat.completions.create.side_effect = AuthenticationError(
        message="bad key",
        response=httpx.Response(401, request=httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions")),
        body=None,
    )

    with patch("llm.openrouter_provider.OpenAI", return_value=fake_client):
        provider = OpenRouterProvider(
            api_key="sk-test",
            base_url="https://openrouter.ai/api/v1",
            model="primary-model",
            fallback_model="fallback-model",
        )

        try:
            provider.generate_response("system", "user")
        except RuntimeError as exc:
            assert "authentication or configuration" in str(exc).lower()
        else:
            raise AssertionError("Expected RuntimeError")


def test_provider_raises_on_empty_response():
    fake_client = MagicMock()
    fake_client.chat.completions.create.return_value = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="   "))]
    )

    with patch("llm.openrouter_provider.OpenAI", return_value=fake_client):
        provider = OpenRouterProvider(
            api_key="sk-test",
            base_url="https://openrouter.ai/api/v1",
            model="primary-model",
            fallback_model="fallback-model",
        )

        try:
            provider.generate_response("system", "user")
        except RuntimeError as exc:
            assert "empty response" in str(exc).lower()
        else:
            raise AssertionError("Expected RuntimeError")


def test_analyzer_includes_conversation_and_context_blocks_in_prompt(caplog):
    provider = StubProvider(response="short answer")
    analyzer = ResponseAnalyzer(
        settings=SimpleNamespace(
            openrouter_api_key="test-key",
            openrouter_base_url="https://openrouter.ai/api/v1",
            openrouter_model="primary-model",
            openrouter_fallback_model="fallback-model",
        ),
        provider=provider,
    )

    context = {
        "tenant": "MAIF",
        "environment": "PROD",
        "conversation_history": [
            {"role": "user", "content": "Earlier I asked about Jenkins"},
            {"role": "assistant", "content": "I checked Jenkins and found a failure"},
        ],
    }

    analyzer.analyze("What caused this error?", [make_event()], context=context)

    prompt = provider.calls[0]["user_prompt"]
    assert "Current user message" in prompt
    assert "Conversation history" in prompt
    assert "Tenant/context" in prompt
    assert "MAIF" in prompt
    assert "PROD" in prompt


def test_analyzer_uses_tenant_environment_context_when_available():
    provider = StubProvider(response="short answer")
    analyzer = ResponseAnalyzer(
        settings=SimpleNamespace(
            openrouter_api_key="test-key",
            openrouter_base_url="https://openrouter.ai/api/v1",
            openrouter_model="primary-model",
            openrouter_fallback_model="fallback-model",
        ),
        provider=provider,
    )

    analyzer.analyze("Explain this failure", [make_event()], context={"tenant": "MAIF", "environment": "PROD"})

    prompt = provider.calls[0]["user_prompt"]
    assert "tenant: MAIF" in prompt
    assert "environment: PROD" in prompt


def test_analyzer_does_not_include_jira_in_prompt():
    provider = StubProvider(response="short answer")
    analyzer = ResponseAnalyzer(
        settings=SimpleNamespace(
            openrouter_api_key="test-key",
            openrouter_base_url="https://openrouter.ai/api/v1",
            openrouter_model="primary-model",
            openrouter_fallback_model="fallback-model",
        ),
        provider=provider,
    )

    analyzer.analyze(
        "Explain this",
        [make_event()],
        context={"requested_agents": ["jira", "git", "jenkins"]},
    )

    prompt = provider.calls[0]["user_prompt"]
    assert "jira" not in prompt.lower()
    assert "git" in prompt.lower()


def test_provider_does_not_log_api_key(caplog):
    fake_client = MagicMock()
    fake_client.chat.completions.create.return_value = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="ok"))]
    )

    with patch("llm.openrouter_provider.OpenAI", return_value=fake_client):
        provider = OpenRouterProvider(
            api_key="sk-secret-value",
            base_url="https://openrouter.ai/api/v1",
            model="primary-model",
            fallback_model="fallback-model",
        )
        provider.generate_response("system", "user")

    assert "sk-secret-value" not in caplog.text
