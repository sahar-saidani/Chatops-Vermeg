"""Standard multi-agent message envelope (mirrors Java's AgentMessage record)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class AgentMessage:
    """agent / timestamp / data envelope published to RabbitMQ.

    Structurally compatible with com.vermeg.chatops.messaging.dto.AgentMessage
    on the Spring Boot side.
    """

    agent: str
    data: dict[str, Any]
    timestamp: datetime = None  # set in __post_init__ if not provided

    def __post_init__(self) -> None:
        if self.timestamp is None:
            self.timestamp = datetime.now(tz=timezone.utc)

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "agent": self.agent,
            "timestamp": self.timestamp.isoformat().replace("+00:00", "Z"),
            "data": self.data,
        }