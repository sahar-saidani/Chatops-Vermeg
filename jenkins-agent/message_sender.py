"""RabbitMQ-ready payload preparation for multi-agent integration."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from agent.machine_identity import MachineIdentity
from models.schemas import AgentMessage
from rabbitmq_publisher import RabbitMqPublisher


class MessageSender:
    """Prepare and dispatch messages to the RabbitMQ broker."""

    def __init__(self, rabbitmq_url: str | None = None) -> None:
        self._publisher = RabbitMqPublisher(url=rabbitmq_url) if rabbitmq_url else None

    def build_message(self, data: dict[str, Any], identity: MachineIdentity) -> dict[str, Any]:
        """Build a standard multi-agent envelope payload, enriched with machine identity."""
        envelope = AgentMessage(
            tenant=identity.tenant_name,
            environment=identity.environment_name,
            environment_name=identity.environment_name,
            environment_type=identity.environment_type,
            machine_reference=identity.machine_reference,
            agent="jenkins",
            timestamp=datetime.now(tz=timezone.utc),
            data=data,
            node_role=identity.node_role,
            jenkins_purpose=identity.jenkins_purpose,
        )
        return envelope.model_dump(mode="json", by_alias=True, exclude_none=True)

    def send(self, data: dict[str, Any], identity: MachineIdentity) -> dict[str, Any]:
        """Build the envelope and publish it to RabbitMQ if configured."""
        message = self.build_message(data, identity)
        if self._publisher is not None:
            self._publisher.publish(message, identity=identity)
        return message