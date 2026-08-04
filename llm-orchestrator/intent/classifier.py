from __future__ import annotations

import json
import logging
import re

from agents.registry import AGENT_REGISTRY
from routing.tenant_machine_registry import TenantMachineRegistry
from .models import Intent, RequestMode

logger = logging.getLogger(__name__)

# Keyword -> agent_key. Order doesn't matter; a request can match several
# agents (e.g. "Jenkins failures and Git activity this week").
AGENT_KEYWORDS: dict[str, list[str]] = {
    "git": ["git", "commit", "branch", "pull request", "merge request", "repository", "repo"],
    "jenkins": ["jenkins", "build", "pipeline", "ci/cd", "ci job", "job failed", "jenkins job"],
    "jira": ["jira", "ticket", "issue", "sprint", "backlog", "epic"],
    "installation": ["installation", "installed", "install", "deployment script", "deployed version"],
    "infrastructure": ["infrastructure", "cpu", "memory", "disk", "network", "server metrics", "uptime"],
    "log": ["log", "logs", "error rate", "prometheus", "metric"],
}

HISTORICAL_MARKERS = [
    r"\bthis week\b", r"\blast week\b", r"\bthis month\b", r"\blast month\b",
    r"\bthis year\b", r"\blast year\b", r"\bduring\b", r"\bsince\b",
    r"\blast release\b", r"\bhistory\b", r"\bhistorical\b", r"\bover the (last|past)\b",
    r"\bimported\b", r"\btrend\b", r"\bpast \d+ (day|days|week|weeks|month|months)\b",
]

REAL_TIME_MARKERS = [
    r"\bcurrent(ly)?\b", r"\bnow\b", r"\blatest\b", r"\btoday\b", r"\bright now\b",
    r"\bstatus\b", r"\blive\b",
]

ENVIRONMENT_PATTERN = re.compile(r"\b(DEV|UAT|QA|TEST|STAGING|STAGE|PROD|PRODUCTION)\b", re.IGNORECASE)

DAYS_PER_UNIT = {"day": 1, "week": 7, "month": 30, "year": 365}
RANGE_PATTERN = re.compile(
    r"\b(?:this|last|past)\s+(day|week|month|year)\b|\bpast\s+(\d+)\s+(day|days|week|weeks|month|months)\b",
    re.IGNORECASE,
)


class IntentClassifier:
    """Rule-based intent detection with an optional LLM fallback.

    The rule-based path is deterministic, fast and free of API calls -
    appropriate for the majority of ChatOps requests, which follow the
    predictable "<agent domain> + <time marker>" shape shown in the
    project's own examples. When no agent keyword matches at all, the
    request is routed to the LLM fallback (only used if an OpenRouter API
    key is configured) instead of guessing.
    """

    def __init__(self, llm_client=None, tenant_registry: TenantMachineRegistry | None = None):
        # llm_client is an intent.llm_fallback compatible object; kept
        # injectable so it can be mocked in tests without an API key.
        self._llm_client = llm_client
        self._tenant_registry = tenant_registry or TenantMachineRegistry.load_default()

    def classify(self, text: str) -> Intent:
        normalized = text.lower()

        agent_keys = self._match_agents(normalized)
        mode = self._match_mode(normalized)
        environment = self._match_environment(text)
        tenant = self._match_tenant(text)
        machine_reference = None
        if tenant:
            route = self._tenant_registry.resolve(tenant)
            machine_reference = route.machine_reference if route else None
        time_range_days = self._match_time_range(normalized) if mode is RequestMode.HISTORICAL else None
        action = self._match_action(normalized)

        if agent_keys:
            return Intent(
                mode=mode,
                tenant=tenant,
                agent_keys=agent_keys,
                action=action,
                environment=environment,
                machine_reference=machine_reference,
                time_range_days=time_range_days,
                confidence=1.0,
            )

        if self._llm_client is not None:
            logger.info("No agent keyword matched for %r, falling back to LLM intent detection", text)
            return self._llm_client.classify(text)

        logger.warning("No agent keyword matched for %r and no LLM fallback configured", text)
        return Intent(
            mode=mode,
            tenant=tenant,
            agent_keys=[],
            action=action,
            environment=environment,
            machine_reference=machine_reference,
            time_range_days=time_range_days,
            confidence=0.0,
        )

    @staticmethod
    def _match_agents(normalized_text: str) -> list[str]:
        matched: list[str] = []
        for agent_key, keywords in AGENT_KEYWORDS.items():
            if any(keyword in normalized_text for keyword in keywords):
                matched.append(agent_key)
        # Preserve registry order for deterministic execution order.
        return [key for key in AGENT_REGISTRY if key in matched]

    @staticmethod
    def _match_mode(normalized_text: str) -> RequestMode:
        historical_hit = any(re.search(p, normalized_text) for p in HISTORICAL_MARKERS)
        realtime_hit = any(re.search(p, normalized_text) for p in REAL_TIME_MARKERS)

        if historical_hit and not realtime_hit:
            return RequestMode.HISTORICAL
        if historical_hit and realtime_hit:
            # A historical time marker is the stronger, more specific signal
            # (e.g. "current status this week" is ambiguous wording for a
            # weekly historical rollup).
            return RequestMode.HISTORICAL
        # Default: real-time, matching every Mode 1 example in the spec,
        # none of which contain an explicit "current/now" marker either
        # (e.g. "What version is installed on DEV?").
        return RequestMode.REAL_TIME

    @staticmethod
    def _match_environment(text: str) -> str | None:
        match = ENVIRONMENT_PATTERN.search(text)
        return match.group(1).upper() if match else None

    def _match_tenant(self, text: str) -> str | None:
        tenant = self._tenant_registry.infer_tenant(text)
        return tenant.upper() if tenant else None

    @staticmethod
    def _match_action(normalized_text: str) -> str:
        if any(keyword in normalized_text for keyword in ["analysis", "analyze", "analyse"]):
            return "analysis"
        if any(keyword in normalized_text for keyword in ["status", "latest", "current", "show", "check"]):
            return "status"
        if any(keyword in normalized_text for keyword in ["install", "installed", "installation", "deploy"]):
            return "installation_analysis"
        if any(keyword in normalized_text for keyword in ["log", "logs", "error"]):
            return "log_analysis"
        if any(keyword in normalized_text for keyword in ["infrastructure", "cpu", "memory", "disk", "network"]):
            return "infrastructure_analysis"
        return "analysis"

    @staticmethod
    def _match_time_range(normalized_text: str) -> int | None:
        match = RANGE_PATTERN.search(normalized_text)
        if not match:
            return None
        if match.group(1):
            return DAYS_PER_UNIT[match.group(1)]
        count, unit = match.group(2), match.group(3)
        unit_key = unit.rstrip("s")
        return int(count) * DAYS_PER_UNIT[unit_key]


class LLMIntentFallback:
    """Uses an LLMProvider to classify intent when no keyword matches.

    Kept isolated from IntentClassifier so the common, deterministic path
    never needs network access or an API key. Only depends on the generic
    ``LLMProvider`` interface (see ``llm/provider.py``); the concrete
    provider (OpenRouter by default) is injected from ``api.py``.
    """

    def __init__(self, api_key: str, base_url: str, model: str):
        from llm.openrouter_provider import OpenRouterProvider

        self._provider = OpenRouterProvider(api_key=api_key, base_url=base_url, model=model)

    def classify(self, text: str) -> Intent:
        agent_list = "\n".join(f"- {k}: {v.description}" for k, v in AGENT_REGISTRY.items())
        system = (
            "You are an intent classifier for a ChatOps assistant. Given a user "
            "request, decide: (1) which of these agents are relevant, (2) whether "
            "the request is REAL_TIME (about the current/live state) or "
            "HISTORICAL (about past data already stored). Respond ONLY with JSON: "
            '{"mode": "REAL_TIME"|"HISTORICAL", "agent_keys": [...], '
            '"environment": string|null, "time_range_days": int|null}\n\n'
            f"Available agents:\n{agent_list}"
        )
        raw = self._provider.generate_response(system, text, max_tokens=300, temperature=0.2)
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            logger.error("LLM intent fallback returned non-JSON output: %s", raw)
            return Intent(mode=RequestMode.REAL_TIME, agent_keys=[], confidence=0.0)

        mode = RequestMode.HISTORICAL if parsed.get("mode") == "HISTORICAL" else RequestMode.REAL_TIME
        agent_keys = [key for key in parsed.get("agent_keys", []) if key in AGENT_REGISTRY]
        return Intent(
            mode=mode,
            tenant=parsed.get("tenant"),
            agent_keys=agent_keys,
            action=parsed.get("action", "analysis"),
            environment=parsed.get("environment"),
            time_range_days=parsed.get("time_range_days"),
            confidence=0.7,
        )
