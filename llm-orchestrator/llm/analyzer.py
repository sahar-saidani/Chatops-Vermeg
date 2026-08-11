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
monitoring, logs, infrastructure, Jenkins, Git, installation, and related
technical components.

IMPORTANT:

1. LANGUAGE

- Answer in the same language as the user's latest message.
- If the user writes in French, answer in French.
- If the user writes in English, answer in English.
- If the user mixes French and English, follow that style naturally.

2. SCOPE

The execution context provided by the orchestrator is authoritative.

Only use data matching the requested:
- tenant
- environment
- operating system
- agent

Do NOT introduce information from another tenant, environment, operating system,
machine, or agent.

IMPORTANT:
"machine_reference" identifies how the orchestrator reaches a machine.
It is NOT necessarily the same identifier as:
- hostname
- target
- machine_reference stored inside an agent event

Therefore, do NOT reject an event merely because the event's machine_reference
is different from the orchestrator's machine_reference.

For example:

orchestrator machine_reference = windows-local

may legitimately produce an event containing:

machine_reference = MAIF-DEV-01
target = MAIF-WINDOWS-01
hostname = DESKTOP-L2M3BF0

These values can all refer to the same execution target.

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

Use ONLY the evidence provided in the agent results and execution context.

Do not invent:
- metrics
- errors
- commits
- branches
- tickets
- environments
- machines
- incidents
- Prometheus data
- operating systems
- agent results

If Prometheus is NOT_USED in the infrastructure event,
do NOT claim that Prometheus targets are DOWN.

If the infrastructure event was collected using psutil,
base the infrastructure analysis on the psutil metrics actually present.

5. REAL-TIME REQUESTS

For REAL_TIME infrastructure requests:

- prioritize the fresh infrastructure event;
- do not mix it with historical events;
- do not mention older Linux/CentOS events;
- do not mention another machine;
- do not mention Prometheus unless the current event explicitly contains
  relevant Prometheus information.

6. ANSWER STYLE

For technical diagnosis, use a natural structure such as:

- What happened
- Evidence
- Likely cause
- Impact
- Recommended next steps

Do not force this structure for simple questions.

7. DETAIL LEVEL

- simple requests: short and direct;
- diagnosis or troubleshooting: detailed and practical;
- explicit analysis requests: comprehensive but concise.

8. SECURITY

Never expose API keys, passwords, tokens, secrets, or credentials.
""".strip()


class ResponseAnalyzer:
    """Generate the final natural-language answer from canonical_events data."""

    def __init__(
        self,
        settings: Settings,
        provider: LLMProvider | None = None,
    ):
        self._provider = provider or OpenRouterProvider(
            api_key=self._get_setting(
                settings,
                "openrouter_api_key",
            ),
            base_url=self._get_setting(
                settings,
                "openrouter_base_url",
            )
            or "https://openrouter.ai/api/v1",
            model=self._get_setting(
                settings,
                "openrouter_model",
            )
            or "nvidia/nemotron-3-ultra-550b-a55b:free",
            fallback_model=self._get_setting(
                settings,
                "openrouter_fallback_model",
            )
            or "openai/gpt-oss-120b:free",
        )

    # ------------------------------------------------------------------
    # SETTINGS
    # ------------------------------------------------------------------

    @staticmethod
    def _get_setting(
        settings: Settings,
        *names: str,
    ) -> str | None:

        for name in names:
            value = getattr(settings, name, None)

            if value not in (None, ""):
                return value

        return None

    # ------------------------------------------------------------------
    # PUBLIC API
    # ------------------------------------------------------------------

    def analyze(
        self,
        user_message: str,
        events: list[CanonicalEvent],
        context: dict | None = None,
    ) -> str:
        """
        Generate the final response.

        Events are scoped using tenant/environment/OS/agent.

        machine_reference is intentionally NOT used as a strict equality
        condition because it represents the routing mechanism rather than
        necessarily the identifier stored by the infrastructure agent.
        """

        scoped_events = self._filter_events_by_scope(
            events,
            context,
        )

        logger.info(
            "Generating LLM response | tenant=%s | environment=%s | "
            "machine=%s | os=%s | agents=%s | events=%d",
            context.get("tenant") if context else None,
            context.get("environment") if context else None,
            context.get("machine_reference") if context else None,
            context.get("operating_system") if context else None,
            tuple(context.get("requested_agents", []))
            if context
            else (),
            len(scoped_events),
        )

        try:
            return self._generate_with_provider(
                user_message,
                scoped_events,
                context,
            )

        except Exception as exc:
            logger.exception(
                "OpenRouter response generation failed: %s",
                exc,
            )

            return self._build_fallback_response(
                user_message,
                scoped_events,
                context,
                error=exc,
            )

    # ------------------------------------------------------------------
    # SCOPE FILTERING
    # ------------------------------------------------------------------

    def _filter_events_by_scope(
        self,
        events: list[CanonicalEvent],
        context: dict | None,
    ) -> list[CanonicalEvent]:
        """
        Keep only events belonging to the requested execution scope.

        Strict:
            tenant
            environment
            operating_system
            agent

        Not strict:
            machine_reference

        machine_reference is a routing identifier and may legitimately
        differ from the machine identifier stored in the event.
        """

        if not context:
            return events

        requested_tenant = self._normalize(
            context.get("tenant")
        )

        requested_environment = self._normalize(
            context.get("environment")
        )

        requested_os = self._normalize(
            context.get("operating_system")
        )

        requested_agents = {
            self._normalize(agent)
            for agent in context.get("requested_agents", [])
            if agent
        }

        filtered: list[CanonicalEvent] = []

        for event in events:

            event_tenant = self._normalize(
                getattr(event, "tenant", None)
                or self._event_data(event).get("tenant")
            )

            event_environment = self._normalize(
                getattr(event, "environment", None)
                or self._event_data(event).get("environment")
            )

            event_data = self._event_data(event)

            event_os = self._normalize(
                event_data.get("operating_system")
            )

            event_agent = self._normalize(
                event.agent_key
            )

            # ----------------------------------------------------------
            # Tenant
            # ----------------------------------------------------------

            if (
                requested_tenant
                and event_tenant
                and event_tenant != requested_tenant
            ):
                logger.warning(
                    "Ignoring event from another tenant: "
                    "event_tenant=%s requested_tenant=%s",
                    event_tenant,
                    requested_tenant,
                )
                continue

            # ----------------------------------------------------------
            # Environment
            # ----------------------------------------------------------

            if (
                requested_environment
                and event_environment
                and event_environment != requested_environment
            ):
                logger.warning(
                    "Ignoring event from another environment: "
                    "event_environment=%s requested_environment=%s",
                    event_environment,
                    requested_environment,
                )
                continue

            # ----------------------------------------------------------
            # Operating system
            # ----------------------------------------------------------

            if (
                requested_os
                and event_os
                and event_os != requested_os
            ):
                logger.warning(
                    "Ignoring event from another operating system: "
                    "event_os=%s requested_os=%s",
                    event_os,
                    requested_os,
                )
                continue

            # ----------------------------------------------------------
            # Agent
            # ----------------------------------------------------------

            if (
                requested_agents
                and event_agent not in requested_agents
            ):
                logger.warning(
                    "Ignoring event from another agent: "
                    "event_agent=%s requested_agents=%s",
                    event_agent,
                    requested_agents,
                )
                continue

            # ----------------------------------------------------------
            # IMPORTANT:
            #
            # Do NOT compare:
            #
            # context["machine_reference"]
            #
            # with:
            #
            # event.data["machine_reference"]
            #
            # because:
            #
            # windows-local
            #
            # can legitimately produce:
            #
            # MAIF-DEV-01
            #
            # ----------------------------------------------------------

            filtered.append(event)

        if len(filtered) != len(events):
            logger.warning(
                "Filtered %d out-of-scope event(s). "
                "Scope tenant=%s environment=%s machine=%s os=%s agents=%s",
                len(events) - len(filtered),
                context.get("tenant"),
                context.get("environment"),
                context.get("machine_reference"),
                context.get("operating_system"),
                context.get("requested_agents"),
            )

        return filtered

    @staticmethod
    def _normalize(value) -> str | None:
        if value is None:
            return None

        text = str(value).strip().lower()

        return text or None

    @staticmethod
    def _event_data(event: CanonicalEvent) -> dict:
        data = getattr(event, "data", None)

        if isinstance(data, dict):
            return data

        return {}

    # ------------------------------------------------------------------
    # PROVIDER
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # EVENT PAYLOAD
    # ------------------------------------------------------------------

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
                "message_timestamp": (
                    event.message_timestamp.isoformat()
                ),
                "data": event.data,
            }
            for event in events
        ]

        return json.dumps(
            payload,
            default=str,
            ensure_ascii=False,
        )

    # ------------------------------------------------------------------
    # USER PROMPT
    # ------------------------------------------------------------------

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

            history = self._extract_conversation_history(
                context
            )

            if history:
                sections.extend(
                    [
                        "Conversation history:",
                        history,
                    ]
                )

            user_context = self._extract_user_context(
                context
            )

            if user_context:
                sections.extend(
                    [
                        "User context:",
                        user_context,
                    ]
                )

            tenant_context = self._extract_tenant_context(
                context
            )

            if tenant_context:
                sections.extend(
                    [
                        "Tenant/execution context:",
                        tenant_context,
                    ]
                )

        event_count = len(
            self._parse_event_count(payload)
        )

        sections.extend(
            [
                f"Agent results ({event_count} event(s)):",
                payload,
            ]
        )

        if context:

            execution_context = (
                self._build_execution_context(context)
            )

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
                "- Use only the supplied evidence.",
                "- For REAL_TIME requests, use the fresh event only.",
                "- Do not introduce historical events.",
                "- Do not introduce CentOS/Linux information when the requested OS is Windows.",
                "- Do not introduce Prometheus information unless it exists in the current event.",
                "- Do not confuse machine_reference with hostname, target, or the machine identifier stored in the event.",
                "- Clearly separate confirmed facts from hypotheses.",
                "- Give concrete next steps when appropriate.",
                "- Do not invent missing information.",
                "- Do not expose secrets or API keys.",
            ]
        )

        return "\n\n".join(sections)

    # ------------------------------------------------------------------
    # CONTEXT
    # ------------------------------------------------------------------

    def _extract_conversation_history(
        self,
        context: dict,
    ) -> str:

        history = context.get(
            "conversation_history"
        ) or []

        if not history:
            return ""

        formatted: list[str] = []

        for entry in history[-4:]:

            role = entry.get(
                "role",
                "unknown",
            )

            content = entry.get(
                "content",
                "",
            )

            if not content:
                continue

            formatted.append(
                f"{role}: {content}"
            )

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
                user_info.append(
                    f"{key}: {value}"
                )

        return "\n".join(user_info)

    def _extract_tenant_context(
        self,
        context: dict,
    ) -> str:

        tenant_info: list[str] = []

        for key in (
            "tenant",
            "environment",
            "machine_reference",
            "operating_system",
        ):
            value = context.get(key)

            if value:
                tenant_info.append(
                    f"{key}: {value}"
                )

        requested_agents = context.get(
            "requested_agents"
        )

        if requested_agents:
            tenant_info.append(
                "requested_agents: "
                + ", ".join(
                    str(agent)
                    for agent in requested_agents
                )
            )

        return "\n".join(tenant_info)

    def _build_execution_context(
        self,
        context: dict,
    ) -> str:

        summary: dict[str, object] = {}

        for key in (
            "tenant",
            "environment",
            "machine_reference",
            "operating_system",
            "preferred_language",
        ):
            value = context.get(key)

            if value:
                summary[key] = value

        requested_agents = context.get(
            "requested_agents"
        )

        if requested_agents:
            summary["requested_agents"] = [
                str(agent)
                for agent in requested_agents
            ]

        return json.dumps(
            summary,
            ensure_ascii=False,
        )

    # ------------------------------------------------------------------
    # TOKEN SELECTION
    # ------------------------------------------------------------------

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

        if any(
            keyword in text
            for keyword in detailed_keywords
        ):
            return 1000 if event_count > 0 else 800

        if any(
            keyword in text
            for keyword in short_keywords
        ):
            return 350

        return 700

    # ------------------------------------------------------------------
    # FALLBACK
    # ------------------------------------------------------------------

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
                context_parts.append(
                    f"tenant {tenant}"
                )

            environment = context.get(
                "environment"
            )

            if environment:
                context_parts.append(
                    f"environment {environment}"
                )

            machine = context.get(
                "machine_reference"
            )

            if machine:
                context_parts.append(
                    f"machine {machine}"
                )

            operating_system = context.get(
                "operating_system"
            )

            if operating_system:
                context_parts.append(
                    f"OS {operating_system}"
                )

            requested_agents = context.get(
                "requested_agents"
            )

            if requested_agents:
                context_parts.append(
                    "agents "
                    + ", ".join(
                        str(agent)
                        for agent in requested_agents
                    )
                )

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
                "donne",
                "montre",
            ]
        )

        error_text = ""

        if error:

            error_name = type(error).__name__

            if (
                "Authentication" in error_name
                or "401" in str(error)
            ):
                error_text = (
                    " Le service d'IA a refusé "
                    "l'authentification configurée."
                    if is_french
                    else
                    " The AI service rejected "
                    "the configured authentication."
                )

            elif (
                "Timeout" in error_name
                or "timeout" in str(error).lower()
            ):
                error_text = (
                    " Le service d'IA n'a pas répondu "
                    "dans le délai attendu."
                    if is_french
                    else
                    " The AI service did not respond "
                    "in time."
                )

            else:
                error_text = (
                    " Le service d'IA a rencontré "
                    "une erreur pendant la génération "
                    "de la réponse."
                    if is_french
                    else
                    " The AI service encountered an error "
                    "while generating the response."
                )

        if not events:

            if is_french:
                response = (
                    "Aucune donnée d'infrastructure correspondant "
                    "au périmètre demandé n'est disponible."
                    + error_text
                )

            else:
                response = (
                    "No infrastructure data matching the "
                    "requested scope is available."
                    + error_text
                )

            if context_parts:
                response += (
                    "\nContexte : "
                    + "; ".join(context_parts)
                    + "."
                    if is_french
                    else
                    "\nContext: "
                    + "; ".join(context_parts)
                    + "."
                )

            return response

        evidence_items: list[str] = []

        for event in events[:5]:

            environment = (
                f" ({event.environment})"
                if event.environment
                else ""
            )

            evidence_items.append(
                f"{event.agent_key}{environment}"
            )

        evidence = ", ".join(
            evidence_items
        )

        if is_french:
            response = (
                "Le service de génération de réponse "
                "est temporairement indisponible."
                + error_text
                + "\n\n"
                f"Les données recueillies sont disponibles "
                f"via : {evidence}."
            )

        else:
            response = (
                "The response-generation service is "
                "temporarily unavailable."
                + error_text
                + "\n\n"
                f"The evidence that was collected is still "
                f"available from: {evidence}."
            )

        if context_parts:
            response += (
                "\nContexte détecté : "
                + "; ".join(context_parts)
                + "."
                if is_french
                else
                "\nDetected context: "
                + "; ".join(context_parts)
                + "."
            )

        return response

    # ------------------------------------------------------------------
    # HELPERS
    # ------------------------------------------------------------------

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

        except (
            json.JSONDecodeError,
            TypeError,
        ):
            return []

        return []