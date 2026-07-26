"""RabbitMQ-ready payload preparation for multi-agent integration."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from models.schemas import AgentMessage
from rabbitmq_publisher import RabbitMqPublisher


class MessageSender:
    """Prepare and dispatch messages to the RabbitMQ broker."""

    def __init__(self, rabbitmq_url: str | None = None) -> None:
        self._publisher = RabbitMqPublisher(url=rabbitmq_url) if rabbitmq_url else None

    def build_message(self, data: dict[str, Any]) -> dict[str, Any]:
        """Build a standard multi-agent envelope payload."""
        envelope = AgentMessage(
            agent="jenkins",
            timestamp=datetime.now(tz=timezone.utc),
            data=data,
        )
        return envelope.model_dump(mode="json")

    def send(self, data: dict[str, Any]) -> dict[str, Any]:
        """Build the envelope and publish it to RabbitMQ if configured."""
        message = self.build_message(data)
        if self._publisher is not None:
            self._publisher.publish(message)
        return message