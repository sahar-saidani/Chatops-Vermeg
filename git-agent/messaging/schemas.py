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
    tenant: str | None = None
    environment: str | None = None
    environment_name: str | None = None
    environment_type: str | None = None
    machine_reference: str | None = None
    node_role: str | None = None
    timestamp: datetime = None  # set in __post_init__ if not provided

    def __post_init__(self) -> None:
        if self.timestamp is None:
            self.timestamp = datetime.now(tz=timezone.utc)

    def to_json_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if self.tenant is not None:
            payload["tenant"] = self.tenant
            payload["environment"] = self.environment
            payload["environmentName"] = self.environment_name or self.environment
            payload["environmentType"] = self.environment_type
            payload["machineReference"] = self.machine_reference
        payload["agent"] = self.agent
        payload["timestamp"] = self.timestamp.isoformat().replace("+00:00", "Z")
        payload["data"] = self.data
        if self.node_role:
            payload["nodeRole"] = self.node_role
        return payload