from __future__ import annotations

import json
import logging
import re

from agents.registry import AGENT_REGISTRY
from routing.tenant_machine_registry import TenantMachineRegistry
from .models import Intent, RequestMode

LOGGER = logging.getLogger(__name__)


AGENT_KEYWORDS: dict[str, list[str]] = {
    "git": [
        "git",
        "commit",
        "branch",
        "pull request",
        "merge request",
        "repository",
        "repo",
    ],
    "jenkins": [
        "jenkins",
        "build",
        "pipeline",
        "ci/cd",
        "ci job",
        "job failed",
        "jenkins job",
    ],
    "jira": [
        "jira",
        "ticket",
        "issue",
        "sprint",
        "backlog",
        "epic",
    ],
    "installation": [
        "installation",
        "installed",
        "install",
        "deployment script",
        "deployed version",
    ],
    "infrastructure": [
        "infrastructure",
        "cpu",
        "memory",
        "disk",
        "network",
        "server metrics",
        "uptime",
    ],
    "log": [
        "log",
        "logs",
        "error rate",
        "prometheus",
        "metric",
    ],
}


HISTORICAL_MARKERS = [
    r"\bthis week\b",
    r"\blast week\b",
    r"\bthis month\b",
    r"\blast month\b",
    r"\bthis year\b",
    r"\blast year\b",
    r"\bduring\b",
    r"\bsince\b",
    r"\blast release\b",
    r"\bhistory\b",
    r"\bhistorical\b",
    r"\bover the (last|past)\b",
    r"\bimported\b",
    r"\btrend\b",
    r"\bpast \d+ (day|days|week|weeks|month|months)\b",
]


REAL_TIME_MARKERS = [
    r"\bcurrent(ly)?\b",
    r"\bnow\b",
    r"\blatest\b",
    r"\btoday\b",
    r"\bright now\b",
    r"\bstatus\b",
    r"\blive\b",
]


ENVIRONMENT_PATTERN = re.compile(
    r"\b(DEV|UAT|QA|TEST|STAGING|STAGE|PROD|PRODUCTION)\b",
    re.IGNORECASE,
)


DAYS_PER_UNIT = {
    "day": 1,
    "week": 7,
    "month": 30,
    "year": 365,
}


RANGE_PATTERN = re.compile(
    r"\b(?:this|last|past)\s+(day|week|month|year)\b"
    r"|\bpast\s+(\d+)\s+(day|days|week|weeks|month|months)\b",
    re.IGNORECASE,
)


class IntentClassifier:

    def __init__(
        self,
        llm_client=None,
        tenant_registry: TenantMachineRegistry | None = None,
    ):
        self._llm_client = llm_client
        self._tenant_registry = (
            tenant_registry
            or TenantMachineRegistry.load_default()
        )


    def classify(self, text: str) -> Intent:

        normalized = text.lower()

        agent_keys = self._match_agents(normalized)

        mode = self._match_mode(normalized)

        environment = self._match_environment(text)

        tenant = self._match_tenant(text)
        route = None
        machine_reference = None

        if tenant:
            route = self._tenant_registry.resolve(tenant)
            machine_reference = (
                route.machine_reference
                if route
                else None
            )

        time_range_days = (
            self._match_time_range(normalized)
            if mode is RequestMode.HISTORICAL
            else None
        )

        action = self._match_action(normalized)

        # Nouveau : extraction path/repo
        raw_params = self._extract_params(text)

        if route:
            if "repo" not in raw_params and route.repo:
                raw_params["repo"] = route.repo

            if "branch" not in raw_params and route.branch:
                raw_params["branch"] = route.branch


        if agent_keys:
            return Intent(
                mode=mode,
                tenant=tenant,
                agent_keys=agent_keys,
                action=action,
                environment=environment,
                machine_reference=machine_reference,
                time_range_days=time_range_days,
                raw_params=raw_params,
                confidence=1.0,
            )


        if self._llm_client is not None:
            LOGGER.info(
                "No agent keyword matched for %r, using LLM fallback",
                text,
            )

            return self._llm_client.classify(text)


        return Intent(
            mode=mode,
            tenant=tenant,
            agent_keys=[],
            action=action,
            environment=environment,
            machine_reference=machine_reference,
            time_range_days=time_range_days,
            raw_params=raw_params,
            confidence=0.0,
        )


    @staticmethod
    def _extract_params(text: str) -> dict[str, str]:

        params: dict[str, str] = {}


        # Windows path
        path_match = re.search(
            r"([A-Za-z]:\\.+?)(?=\s|$)",
            text,
        )

        if path_match:
            params["path"] = path_match.group(1)


        # Linux path
        linux_match = re.search(
            r"(/[\w\-./]+)",
            text,
        )

        if linux_match and "path" not in params:
            params["path"] = linux_match.group(1)


        # GitHub owner/repository
        repo_match = re.search(
            r"([\w.-]+/[\w.-]+)",
            text,
        )

        if repo_match and "path" not in params:
            params["repo"] = repo_match.group(1)


        return params



    @staticmethod
    def _match_agents(normalized_text: str) -> list[str]:

        matched = []

        for agent_key, keywords in AGENT_KEYWORDS.items():

            if any(
                keyword in normalized_text
                for keyword in keywords
            ):
                matched.append(agent_key)

        return [
            key
            for key in AGENT_REGISTRY
            if key in matched
        ]



    @staticmethod
    def _match_mode(normalized_text: str) -> RequestMode:

        historical_hit = any(
            re.search(pattern, normalized_text)
            for pattern in HISTORICAL_MARKERS
        )

        realtime_hit = any(
            re.search(pattern, normalized_text)
            for pattern in REAL_TIME_MARKERS
        )


        if historical_hit and not realtime_hit:
            return RequestMode.HISTORICAL


        return RequestMode.REAL_TIME



    @staticmethod
    def _match_environment(text: str) -> str | None:

        match = ENVIRONMENT_PATTERN.search(text)

        return (
            match.group(1).upper()
            if match
            else None
        )



    def _match_tenant(self, text: str) -> str | None:

        tenant = self._tenant_registry.infer_tenant(text)

        return (
            tenant.upper()
            if tenant
            else None
        )



    @staticmethod
    def _match_action(normalized_text: str) -> str:

        if any(
            k in normalized_text
            for k in ["analysis", "analyze", "analyse"]
        ):
            return "analysis"


        if any(
            k in normalized_text
            for k in ["status", "latest", "current", "show", "check"]
        ):
            return "status"


        if any(
            k in normalized_text
            for k in ["install", "installed", "installation", "deploy"]
        ):
            return "installation_analysis"


        if any(
            k in normalized_text
            for k in ["log", "logs", "error"]
        ):
            return "log_analysis"


        if any(
            k in normalized_text
            for k in [
                "infrastructure",
                "cpu",
                "memory",
                "disk",
                "network",
            ]
        ):
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

        return int(count) * DAYS_PER_UNIT[unit.rstrip("s")]



class LLMIntentFallback:

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
    ):
        from llm.openrouter_provider import AgentRouterProvider

        self._provider = AgentRouterProvider(
            api_key=api_key,
            base_url=base_url,
            model=model,
        )


    def classify(self, text: str) -> Intent:

        raw = self._provider.generate_response(
            "",
            text,
            max_tokens=300,
            temperature=0.2,
        )
        LOGGER.info("LLM raw classification response: %r", raw)
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            LOGGER.error("Invalid LLM JSON response: %r", raw)
            raise RuntimeError(
                f"LLM returned invalid JSON: {raw!r}"
        )


        return Intent(
            mode=(
                RequestMode.HISTORICAL
                if parsed.get("mode") == "HISTORICAL"
                else RequestMode.REAL_TIME
            ),
            tenant=parsed.get("tenant"),
            agent_keys=[
                key
                for key in parsed.get("agent_keys", [])
                if key in AGENT_REGISTRY
            ],
            action=parsed.get(
                "action",
                "analysis",
            ),
            environment=parsed.get("environment"),
            time_range_days=parsed.get("time_range_days"),
            raw_params={
                k: v
                for k, v in parsed.items()
                if k in ["path", "repo"]
            },
            confidence=0.7,
        )