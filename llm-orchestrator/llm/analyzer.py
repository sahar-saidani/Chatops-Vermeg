
from __future__ import annotations

import json
import logging

from config import Settings
from data.canonical_events_repository import CanonicalEvent

from .openrouter_provider import OpenRouterProvider
from .provider import LLMProvider

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """
You are the ChatOps VERMEG assistant.

You are a practical, experienced technical colleague helping the user understand
the current state of their systems, repositories, environments, agents, CI/CD,
monitoring, logs, infrastructure, Jenkins, Git, installation, infrastructure,
and related technical components.

Your answer should feel natural, concise, useful, and tailored to the user's problem.

IMPORTANT BEHAVIOR:

1. LANGUAGE
- Answer in the same language as the user's latest message.
- If the user writes in French, answer in French.
- If the user writes in English, answer in English.
- If the user mixes French and English, follow that style naturally.

2. PERSONALIZATION
Use available context when it helps: tenant, environment, requested agents,
conversation history, user preferences, and recent troubleshooting context.
Do not invent user facts.

3. TECHNICAL ANALYSIS
When the user asks for diagnosis or explanation:
- explain what happened;
- identify relevant evidence;
- explain likely causes only when supported by evidence;
- explain impact;
- recommend concrete next steps;
- clearly separate facts from hypotheses;
- say when evidence is insufficient.

4. EVIDENCE
Use only the evidence present in the agent results, conversation history, and
provided context. Do not invent metrics, errors, commits, branches, tickets,
environments, machines, incidents, or personal facts.

5. ANSWER STYLE
For technical analysis, use a natural structure such as:
- What happened
- Evidence
- Likely cause
- Impact
- Recommended next steps

Do not force this structure for simple questions.
Prefer direct, human explanations over repetitive phrasing.

6. DETAIL LEVEL
- simple requests: short and direct;
- diagnosis or troubleshooting: detailed and practical;
- explicit analysis requests: comprehensive but concise.

7. SECURITY
Never expose API keys, passwords, tokens, secrets, or credentials.
""".strip()


class ResponseAnalyzer:
    """Generates the final natural-language answer from canonical_events data."""

    def __init__(
        self,
        settings: Settings,
        provider: LLMProvider | None = None,
    ):
        self._provider = provider or OpenRouterProvider(
            api_key=self._get_setting(settings, "openrouter_api_key"),
            base_url=self._get_setting(settings, "openrouter_base_url")
            or "https://openrouter.ai/api/v1",
            model=self._get_setting(settings, "openrouter_model")
            or "nvidia/nemotron-3-ultra-550b-a55b:free",
            fallback_model=self._get_setting(settings, "openrouter_fallback_model")
            or "openai/gpt-oss-120b:free",
        )

    @staticmethod
    def _get_setting(settings: Settings, *names: str) -> str | None:
        for name in names:
            value = getattr(settings, name, None)
            if value not in (None, ""):
                return value
        return None

    def analyze(
        self,
        user_message: str,
        events: list[CanonicalEvent],
        context: dict | None = None,
    ) -> str:
        """
        Generate the final response.

        Provider errors are handled here so that a temporary LLM/API problem
        does not crash the FastAPI endpoint.
        """

        try:
            return self._generate_with_provider(
                user_message,
                events,
                context,
            )

        except Exception as exc:
            logger.exception(
                "OpenRouter response generation failed: %s",
                exc,
            )

            return self._build_fallback_response(
                user_message,
                events,
                context,
                error=exc,
            )

    def _generate_with_provider(
        self,
        user_message: str,
        events: list[CanonicalEvent],
        context: dict | None = None,
    ) -> str:

        payload = self._build_events_payload(events)

        user_prompt = self._build_user_prompt(
            user_message,
            payload,
            context,
        )

        max_tokens = self._choose_max_tokens(
            user_message,
            len(events),
        )

        return self._provider.generate_response(
            SYSTEM_PROMPT,
            user_prompt,
            max_tokens=max_tokens,
            temperature=0.2,
        )

    def _build_events_payload(
        self,
        events: list[CanonicalEvent],
    ) -> str:

        if not events:
            return (
                "No matching data was found in canonical_events "
                "for this request."
            )

        payload = [
            {
                "agent_key": event.agent_key,
                "environment": event.environment,
                "message_timestamp": event.message_timestamp.isoformat(),
                "data": event.data,
            }
            for event in events
        ]

        return json.dumps(
            payload,
            default=str,
            ensure_ascii=False,
        )

    def _build_user_prompt(
        self,
        user_message: str,
        payload: str,
        context: dict | None,
    ) -> str:

        sections: list[str] = [
            "Current user message:",
            user_message,
        ]

        if context:
            history = self._extract_conversation_history(context)
            if history:
                sections.extend(
                    [
                        "Conversation history:",
                        history,
                    ]
                )

            user_context = self._extract_user_context(context)
            if user_context:
                sections.extend(
                    [
                        "User context:",
                        user_context,
                    ]
                )

            tenant_context = self._extract_tenant_context(context)
            if tenant_context:
                sections.extend(
                    [
                        "Tenant/context:",
                        tenant_context,
                    ]
                )

        event_count = len(self._parse_event_count(payload))

        sections.extend(
            [
                f"Agent results ({event_count} event(s)):",
                payload,
            ]
        )

        if context:
            execution_context = self._build_execution_context(context)
            if execution_context:
                sections.extend(
                    [
                        "Execution context:",
                        execution_context,
                    ]
                )

        sections.extend(
            [
                "Response requirements:",
                "- Answer the user's actual question first.",
                "- Use the available evidence.",
                "- Explain the reasoning when the question requires diagnosis.",
                "- Clearly separate confirmed facts from likely causes.",
                "- Mention relevant context when it improves the answer.",
                "- Give concrete next steps when appropriate.",
                "- Do not invent missing information.",
                "- Do not expose secrets or API keys.",
            ]
        )

        return "\n\n".join(sections)

    def _extract_conversation_history(
        self,
        context: dict,
    ) -> str:

        history = context.get("conversation_history") or []

        if not history:
            return ""

        formatted: list[str] = []

        for entry in history[-4:]:
            role = entry.get("role", "unknown")
            content = entry.get("content", "")
            if not content:
                continue
            formatted.append(f"{role}: {content}")

        return "\n".join(formatted)

    def _extract_user_context(
        self,
        context: dict,
    ) -> str:

        user_info: list[str] = []

        for key in (
            "preferred_language",
            "preferences",
            "user_profile",
        ):
            value = context.get(key)
            if value:
                user_info.append(f"{key}: {value}")

        return "\n".join(user_info)

    def _extract_tenant_context(
        self,
        context: dict,
    ) -> str:

        tenant_info: list[str] = []

        for key in ("tenant", "environment", "machine_reference"):
            value = context.get(key)
            if value:
                tenant_info.append(f"{key}: {value}")

        requested_agents = context.get("requested_agents")
        if requested_agents:
            filtered_agents = [
                str(agent)
                for agent in requested_agents
                if str(agent).lower() != "jira"
            ]
            if filtered_agents:
                tenant_info.append(
                    f"requested_agents: {', '.join(filtered_agents)}"
                )

        return "\n".join(tenant_info)

    def _build_execution_context(self, context: dict) -> str:
        summary: dict[str, object] = {}
        for key in ("tenant", "environment", "machine_reference", "preferred_language"):
            value = context.get(key)
            if value:
                summary[key] = value

        requested_agents = context.get("requested_agents")
        if requested_agents:
            filtered_agents = [
                str(agent)
                for agent in requested_agents
                if str(agent).lower() != "jira"
            ]
            if filtered_agents:
                summary["requested_agents"] = filtered_agents

        return json.dumps(summary, ensure_ascii=False)

    def _parse_event_count(
        self,
        payload: str,
    ) -> list[dict]:

        if payload.startswith("No matching"):
            return []

        try:
            parsed = json.loads(payload)
            if isinstance(parsed, list):
                return parsed
        except (json.JSONDecodeError, TypeError):
            return []

        return []

    def _choose_max_tokens(
        self,
        user_message: str,
        event_count: int,
    ) -> int:

        text = user_message.lower()

        detailed_keywords = [
            "detail",
            "detailed",
            "analyze",
            "analyse",
            "analysis",
            "diagnose",
            "diagnostic",
            "compare",
            "comparison",
            "summary",
            "résumé",
            "explain",
            "explique",
            "pourquoi",
            "why",
            "problem",
            "problème",
            "error",
            "erreur",
            "troubleshoot",
            "debug",
        ]

        short_keywords = [
            "brief",
            "short",
            "court",
            "courte",
            "résume",
            "resume",
            "only",
            "just",
            "commande",
            "command",
        ]

        if any(keyword in text for keyword in detailed_keywords):
            return 1000 if event_count > 0 else 800

        if any(keyword in text for keyword in short_keywords):
            return 350

        return 700

    def _build_fallback_response(
        self,
        user_message: str,
        events: list[CanonicalEvent],
        context: dict | None,
        error: Exception | None = None,
    ) -> str:

        context_parts: list[str] = []

        if context:
            tenant = context.get("tenant")
            if tenant:
                context_parts.append(f"tenant {tenant}")

            environment = context.get("environment")
            if environment:
                context_parts.append(f"environment {environment}")

            requested_agents = context.get("requested_agents")
            if requested_agents:
                filtered_agents = [
                    str(agent)
                    for agent in requested_agents
                    if str(agent).lower() != "jira"
                ]
                if filtered_agents:
                    context_parts.append(f"agents {', '.join(filtered_agents)}")

        is_french = any(
            token in user_message.lower()
            for token in [
                "bonjour",
                "salut",
                "pourquoi",
                "erreur",
                "problème",
                "résumé",
                "résume",
                "quoi",
                "s'il",
            ]
        )

        error_text = ""
        if error:
            error_name = type(error).__name__
            if "Authentication" in error_name or "401" in str(error):
                error_text = (
                    " The AI service rejected the configured authentication."
                    if not is_french
                    else " Le service d'IA a refusé l'authentification configurée."
                )
            elif "Timeout" in error_name or "timeout" in str(error).lower():
                error_text = (
                    " The AI service did not respond in time."
                    if not is_french
                    else " Le service d'IA n'a pas répondu dans le délai attendu."
                )
            else:
                error_text = (
                    " The AI service encountered an error while generating the response."
                    if not is_french
                    else " Le service d'IA a rencontré une erreur pendant la génération de la réponse."
                )

        if not events:
            if context_parts:
                if is_french:
                    return (
                        "Je n'ai pas pu générer l'analyse complète pour le moment."
                        + error_text
                        + " Je peux toutefois confirmer le contexte suivant : "
                        + "; ".join(context_parts)
                        + "."
                    )
                return (
                    "I could not generate a complete analysis right now."
                    + error_text
                    + " I could still confirm the context: "
                    + "; ".join(context_parts)
                    + "."
                )

            if is_french:
                return (
                    "Je n'ai pas pu générer l'analyse complète pour le moment."
                    + error_text
                )
            return "I could not generate a complete analysis right now." + error_text

        evidence_items: list[str] = []
        for event in events[:5]:
            environment = f" ({event.environment})" if event.environment else ""
            evidence_items.append(f"{event.agent_key}{environment}")
        evidence = ", ".join(evidence_items)

        if is_french:
            response = (
                "Le service de génération de réponse est temporairement indisponible."
                + error_text
                + "\n\n"
                f"Les données recueillies sont néanmoins disponibles via : {evidence}."
            )
        else:
            response = (
                "The response-generation service is temporarily unavailable."
                + error_text
                + "\n\n"
                f"The evidence that was collected is still available from: {evidence}."
            )

        if context_parts:
            if is_french:
                response += "\nLe contexte détecté est : " + "; ".join(context_parts) + "."
            else:
                response += "\nDetected context: " + "; ".join(context_parts) + "."

        return response

