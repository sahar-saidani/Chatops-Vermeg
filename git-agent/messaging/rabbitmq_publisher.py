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

    def publish(self, agent_key: str, data: dict[str, Any]) -> None:
        message = AgentMessage(agent=agent_key, data=data)
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
        finally:
            connection.close()