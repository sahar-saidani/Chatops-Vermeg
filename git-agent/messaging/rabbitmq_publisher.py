"""Real RabbitMQ publisher for the git-agent.

Publishes to the same topic exchange declared by the Spring Boot
RabbitMQ Integration Layer (see RabbitMqConfiguration / RabbitMqProperties):
exchange "chatops.agents.exchange", routing key "agent.<agentKey>.data".
"""

from __future__ import annotations

import json
import logging
from typing import Any

import pika

from .schemas import AgentMessage

LOGGER = logging.getLogger(__name__)


class RabbitMqPublisher:
    def __init__(
        self,
        url: str,
        exchange: str = "chatops.agents.exchange",
        routing_key: str = "agent.git.data",
    ) -> None:
        self._url = url
        self._exchange = exchange
        self._routing_key = routing_key

    def publish(self, agent_key: str, data: dict[str, Any], identity: Any = None) -> None:
        if identity is not None:
            LOGGER.info("%s", identity.publish_banner(agent_key))
        message = AgentMessage(
            agent=agent_key,
            data=data,
            tenant=identity.tenant_name if identity is not None else None,
            environment=identity.environment_name if identity is not None else None,
            environment_name=identity.environment_name if identity is not None else None,
            environment_type=identity.environment_type if identity is not None else None,
            machine_reference=identity.machine_reference if identity is not None else None,
            node_role=identity.node_role if identity is not None else None,
        )
        body = json.dumps(message.to_json_dict(), ensure_ascii=False)

        params = pika.URLParameters(self._url)
        connection = pika.BlockingConnection(params)
        try:
            channel = connection.channel()
            channel.exchange_declare(
                exchange=self._exchange, exchange_type="topic", durable=True, passive=True
            )
            channel.basic_publish(
                exchange=self._exchange,
                routing_key=self._routing_key,
                body=body.encode("utf-8"),
                properties=pika.BasicProperties(
                    content_type="application/json",
                    delivery_mode=2,  # persistent
                ),
            )
            LOGGER.info(
                "Published message for agent '%s' to exchange '%s' with routing key '%s'",
                agent_key, self._exchange, self._routing_key,
            )
            LOGGER.info("Message successfully published.")
        finally:
            connection.close()