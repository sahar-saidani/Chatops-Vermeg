from __future__ import annotations

from typing import Any

from config import NormalizationConfig
from models import LogstashEvent, NormalizedLogEvent
from utils import (
    flatten_tags,
    get_nested,
    normalize_level,
    parse_timestamp,
    to_text,
    truncate_text,
)


class LogParser:
    def __init__(self, config: NormalizationConfig) -> None:
        self._config = config

    def parse(self, event: dict[str, Any]) -> NormalizedLogEvent:
        validated = LogstashEvent.model_validate(event)

        timestamp = parse_timestamp(
            validated.timestamp
            or get_nested(event, ["event", "created"])
            or get_nested(event, ["@timestamp"])
            or get_nested(event, ["timestamp"])
        )
        hostname = self._extract_hostname(event, validated.hostname)
        source = self._extract_source(event, validated.source)
        message = self._extract_message(event, validated.message)
        process = self._extract_process(event, validated.process, message)
        service = self._extract_service(event, validated.service, source, process, message)
        level = normalize_level(self._extract_level(event, validated.severity), message)
        tags = self._extract_tags(event, service, source)
        message = truncate_text(message, self._config.max_message_length)

        return NormalizedLogEvent(
            timestamp=timestamp,
            hostname=hostname,
            service=service,
            level=level,
            process=process,
            source=source,
            message=message,
            tags=tags,
        )

    def _extract_hostname(self, event: dict[str, Any], fallback: str | None) -> str:
        candidate = (
            fallback
            or get_nested(event, ["host", "name"])
            or get_nested(event, ["host", "hostname"])
            or get_nested(event, ["agent", "hostname"])
            or get_nested(event, ["fields", "hostname"])
            or get_nested(event, ["hostname"])
            or "unknown-host"
        )
        return to_text(candidate, "unknown-host")

    def _extract_source(self, event: dict[str, Any], fallback: str | None) -> str:
        candidate = (
            fallback
            or get_nested(event, ["log", "file", "path"])
            or get_nested(event, ["log", "source"])
            or get_nested(event, ["winlog", "channel"])
            or get_nested(event, ["source"])
            or "unknown-source"
        )
        return to_text(candidate, "unknown-source")

    def _extract_message(self, event: dict[str, Any], fallback: str | None) -> str:
        candidate = (
            fallback
            or get_nested(event, ["message"])
            or get_nested(event, ["log", "original"])
            or get_nested(event, ["syslog", "message"])
            or ""
        )
        return to_text(candidate, "")

    def _extract_process(self, event: dict[str, Any], fallback: Any, message: str) -> str | None:
        candidates = [
            fallback,
            get_nested(event, ["process", "name"]),
            get_nested(event, ["syslog", "appname"]),
            get_nested(event, ["service", "name"]),
            get_nested(event, ["winlog", "provider_name"]),
            get_nested(event, ["fields", "process"]),
        ]
        for candidate in candidates:
            text = to_text(candidate)
            if text:
                return text

        if message.startswith("sshd[") or message.startswith("sshd:"):
            return "sshd"
        return None

    def _extract_service(self, event: dict[str, Any], fallback: Any, source: str, process: str | None, message: str) -> str:
        candidates = [
            fallback,
            get_nested(event, ["service", "name"]),
            get_nested(event, ["fields", "service_name"]),
            get_nested(event, ["systemd", "unit"]),
            get_nested(event, ["winlog", "channel"]),
            process,
        ]
        for candidate in candidates:
            text = to_text(candidate)
            if text:
                return text.removesuffix(".service")

        lower_source = source.lower()
        if "secure" in lower_source:
            return "auth"
        if "cron" in lower_source:
            return "cron"
        if "maillog" in lower_source:
            return "mail"
        if "boot.log" in lower_source:
            return "boot"
        if "dmesg" in lower_source or "kernel" in lower_source:
            return "kernel"
        if "messages" in lower_source:
            return "system"
        return "system"

    def _extract_level(self, event: dict[str, Any], fallback: Any) -> str:
        candidates = [
            fallback,
            get_nested(event, ["log", "level"]),
            get_nested(event, ["winlog", "level"]),
            get_nested(event, ["level"]),
            get_nested(event, ["severity"]),
        ]
        for candidate in candidates:
            text = to_text(candidate)
            if text:
                return text
        return "INFO"

    def _extract_tags(self, event: dict[str, Any], service: str, source: str) -> list[str]:
        existing_tags = get_nested(event, ["tags"], [])
        source_tags = ["logs-agent", service, source.split("/")[-1]]
        if "secure" in source:
            source_tags.append("auth")
        if "cron" in source:
            source_tags.append("cron")
        if "dmesg" in source or "kernel" in source:
            source_tags.append("kernel")
        if get_nested(event, ["winlog", "channel"]):
            source_tags.append("windows")
        return flatten_tags(existing_tags, source_tags)