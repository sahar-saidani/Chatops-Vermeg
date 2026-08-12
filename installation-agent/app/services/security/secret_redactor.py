"""Detects and redacts secrets/tokens found while scanning config/ and
installation scripts.

This module never returns a raw secret value. Sensitive findings only carry
a fixed placeholder plus a non-reversible SHA-256 fingerprint (useful for
spotting duplicates without ever allowing the original value to be
recovered) - safe to log, publish to RabbitMQ, store in canonical_events,
or hand to the LLM.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any

# Variable/key names that mark a setting as sensitive by name alone.
# Deliberately does NOT include a bare "auth" - real properties files
# nest unrelated toggles under an "auth.*" namespace (e.g.
# solife.auth.sso.close, solife.auth.ssl.verifyDepth), which would turn
# almost every setting in that namespace into a false-positive "secret".
_SENSITIVE_NAME_PATTERN = re.compile(
    r"(token|secret|password|passwd|pwd|api[_-]?key|private[_-]?key|"
    r"access[_-]?key|client[_-]?secret|credential|jwt|bearer|"
    r"authtoken|auth[_-]?token|authorization|"
    r"keystore(?:password)?|truststore(?:password)?)",
    re.IGNORECASE,
)

# Value shapes that look like a live secret regardless of the key name.
# Ordered by specificity; category drives the reported sensitivity.
_VALUE_PATTERNS: list[tuple[str, str, re.Pattern[str]]] = [
    ("private_key_block", "CRITICAL", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("aws_access_key", "CRITICAL", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("github_token", "CRITICAL", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b")),
    ("openai_style_key", "CRITICAL", re.compile(r"\bsk-[A-Za-z0-9]{16,}\b")),
    ("slack_token", "HIGH", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")),
    ("jwt", "HIGH", re.compile(r"\bey[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b")),
    ("bearer_token", "HIGH", re.compile(r"\bBearer\s+[A-Za-z0-9\-_.=]{8,}", re.IGNORECASE)),
    ("credentials_in_url", "HIGH", re.compile(r"://[^\s/:@]+:[^\s/:@]+@")),
]

_PLACEHOLDER_VALUES = {
    "",
    "changeme",
    "change_me",
    "xxx",
    "yyy",
    "todo",
    "n/a",
    "none",
    "null",
    "***redacted***",
    "redacted",
    "<value>",
    "__placeholder__",
}


def _looks_like_placeholder(value: str) -> bool:
    """True for empty values, template placeholders, and already-redacted
    values - these carry no real secret and are safe to echo back."""
    stripped = value.strip().strip("\"'")
    if not stripped:
        return True
    if stripped.lower() in _PLACEHOLDER_VALUES:
        return True
    if stripped.startswith("$"):
        return True
    return False


def fingerprint(value: str) -> str:
    """Non-reversible short fingerprint of a value.

    Lets duplicate/rotated secrets be correlated across files without ever
    exposing or allowing recovery of the original value.
    """
    return hashlib.sha256(value.encode("utf-8", errors="ignore")).hexdigest()[:12]


def classify_value(value: str) -> tuple[str, str] | None:
    """Return (category, sensitivity) if the raw value itself looks like a
    live secret, independent of what the variable is named."""
    if not value or _looks_like_placeholder(value):
        return None
    for category, sensitivity, pattern in _VALUE_PATTERNS:
        if pattern.search(value):
            return category, sensitivity
    return None


def is_sensitive_name(name: str) -> bool:
    return bool(_SENSITIVE_NAME_PATTERN.search(name))


def evaluate_variable(
    name: str,
    value: Any,
    file: str,
    line: int | None = None,
) -> dict[str, Any]:
    """Build one safe `environment_variables` entry for a (name, value) pair.

    Never includes a raw value when the name or the value itself looks
    sensitive - only a fixed placeholder and a fingerprint.
    """
    value_str = "" if value is None else str(value)
    is_placeholder = _looks_like_placeholder(value_str)
    value_classification = classify_value(value_str)

    if value_classification is not None:
        category, sensitivity = value_classification
    elif is_sensitive_name(name):
        category = "credential"
        sensitivity = "LOW" if is_placeholder else "HIGH"
    else:
        category = "configuration"
        sensitivity = "LOW" if is_placeholder else "NONE"

    entry: dict[str, Any] = {
        "name": name,
        "file": file,
        "category": category,
        "sensitivity": sensitivity,
    }
    if line is not None:
        entry["line"] = line

    sensitive = sensitivity in {"CRITICAL", "HIGH", "MEDIUM"}
    entry["sensitive"] = sensitive

    if sensitive and not is_placeholder:
        entry["value_redacted"] = "********"
        entry["value_fingerprint"] = fingerprint(value_str)
    elif is_placeholder:
        entry["value_redacted"] = value_str if value_str else "(empty)"
    else:
        # Not flagged sensitive by name or shape: safe to display, still
        # capped to keep any one field from ballooning the payload.
        entry["value"] = value_str if len(value_str) <= 200 else value_str[:200] + "..."

    return entry


def collect_secrets(environment_variables: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Pull the sensitive findings out of an evaluated variable list."""
    return [
        {key: val for key, val in var.items() if key != "value"}
        for var in environment_variables
        if var.get("sensitive")
    ]


def redact_text(text: str) -> str:
    """Mask any secret-shaped substring inside free text (e.g. validation
    error messages) before it is logged, published, or printed."""
    redacted = text
    for _category, _sensitivity, pattern in _VALUE_PATTERNS:
        redacted = pattern.sub("[REDACTED]", redacted)
    return redacted
