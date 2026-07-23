"""RabbitMQ-ready payload preparation for multi-agent integration."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from models.schemas import AgentMessage


class MessageSender:
    """Prepare and optionally dispatch messages to external broker."""

    def build_message(self, data: dict[str, Any]) -> dict[str, Any]:
        """Build a standard multi-agent envelope payload."""
        envelope = AgentMessage(
            agent="jenkins-agent",
            timestamp=datetime.now(tz=timezone.utc),
            data=data,
        )
        return envelope.model_dump(mode="json")

    def send(self, data: dict[str, Any]) -> dict[str, Any]:
        """Return payload ready for RabbitMQ publication.

        This method intentionally avoids hard-coding broker dependencies.
        """
        return self.build_message(data)
