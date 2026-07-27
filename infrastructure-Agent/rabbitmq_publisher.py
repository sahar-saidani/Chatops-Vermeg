"""Real RabbitMQ publisher for the infrastructure-agent.

Publishes to the same topic exchange declared by the Spring Boot
RabbitMQ Integration Layer: exchange "chatops.agents.exchange",
routing key "agent.infrastructure.data" (must match chatops.rabbitmq.queues.infrastructure).
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

import pika

LOGGER = logging.getLogger(__name__)


class RabbitMqPublisher:
    def __init__(
        self,
        url: str,
        exchange: str = "chatops.agents.exchange",
        routing_key: str = "agent.infrastructure.data",
    ) -> None:
        self._url = url
        self._exchange = exchange
        self._routing_key = routing_key

    def publish(self, agent_key: str, data: dict[str, Any]) -> None:
        envelope = {
            "agent": agent_key,
            "timestamp": datetime.now(tz=timezone.utc).isoformat().replace("+00:00", "Z"),
            "data": data,
        }
        body = json.dumps(envelope, ensure_ascii=False, default=str)

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
                    delivery_mode=2,
                ),
            )
            LOGGER.info(
                "Published message for agent '%s' to exchange '%s' with routing key '%s'",
                agent_key, self._exchange, self._routing_key,
            )
        finally:
            connection.close()