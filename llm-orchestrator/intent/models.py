from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class RequestMode(str, Enum):
    REAL_TIME = "REAL_TIME"
    HISTORICAL = "HISTORICAL"


@dataclass(frozen=True)
class Intent:
    """Result of intent detection for one user request."""

    mode: RequestMode
    agent_keys: list[str]
    environment: str | None = None
    time_range_days: int | None = None
    raw_params: dict[str, str] = field(default_factory=dict)
    confidence: float = 1.0

    @property
    def requires_agent_execution(self) -> bool:
        return self.mode is RequestMode.REAL_TIME
