from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from typing import Any


def get_nested(value: Any, path: list[str], default: Any = None) -> Any:
    current = value
    for key in path:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
        if current is None:
            return default
    return current


def to_text(value: Any, default: str = "") -> str:
    if value is None or isinstance(value, (dict, list)):
        return default
    text = str(value).strip()
    return text if text else default


def flatten_tags(*groups: Any) -> list[str]:
    tags: list[str] = []
    for group in groups:
        if group is None:
            continue
        if isinstance(group, str):
            candidates = [group]
        elif isinstance(group, (list, tuple, set)):
            candidates = [str(item) for item in group]
        else:
            candidates = [str(group)]
        for candidate in candidates:
            value = candidate.strip()
            if value and value not in tags:
                tags.append(value)
    return tags


def truncate_text(value: str, max_length: int) -> str:
    if max_length <= 0 or len(value) <= max_length:
        return value
    return value[: max_length - 3] + "..."


def normalize_level(value: Any, message: str = "") -> str:
    candidate = to_text(value).upper()
    if candidate in {"CRITICAL", "ALERT", "EMERGENCY"}:
        return "CRITICAL"
    if candidate in {"ERROR", "ERR", "FATAL"}:
        return "ERROR"
    if candidate in {"WARN", "WARNING"}:
        return "WARN"
    if candidate in {"INFO", "INFORMATION", "NOTICE"}:
        return "INFO"
    if candidate in {"DEBUG", "TRACE"}:
        return "DEBUG"

    message_text = message.lower()
    if any(word in message_text for word in ("fatal", "critical", "panic")):
        return "CRITICAL"
    if any(word in message_text for word in ("error", "failed", "failure", "exception")):
        return "ERROR"
    if any(word in message_text for word in ("warn", "warning")):
        return "WARN"
    if any(word in message_text for word in ("debug", "trace")):
        return "DEBUG"
    return "INFO"


def parse_timestamp(value: Any) -> datetime:
    now = datetime.now(timezone.utc)
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc) if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)

    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(float(value), tz=timezone.utc)

    text = to_text(value)
    if not text:
        return now

    normalized = text.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
        return parsed.astimezone(timezone.utc) if parsed.tzinfo is not None else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        pass

    syslog_formats = ["%b %d %H:%M:%S", "%b  %d %H:%M:%S"]
    for fmt in syslog_formats:
        try:
            parsed = datetime.strptime(text, fmt)
            parsed = parsed.replace(year=now.year, tzinfo=timezone.utc)
            return parsed
        except ValueError:
            continue

    return now


def dedup_key(payload: dict[str, Any]) -> str:
    import json

    serialized = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
    return sha256(serialized.encode("utf-8", errors="ignore")).hexdigest()