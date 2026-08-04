"""Real RabbitMQ publisher for the jenkins-agent.

Publishes to the same topic exchange declared by the Spring Boot
RabbitMQ Integration Layer: exchange "chatops.agents.exchange",
routing key "agent.jenkins.data" (must match chatops.rabbitmq.queues.jenkins).
"""

from __future__ import annotations

import json
import logging
from typing import Any

import pika

LOGGER = logging.getLogger(__name__)


class RabbitMqPublisher:
    def __init__(
        self,
        url: str,
        exchange: str = "chatops.agents.exchange",
        routing_key: str = "agent.jenkins.data",
    ) -> None:
        self._url = url
        self._exchange = exchange
        self._routing_key = routing_key

    def publish(self, message: dict[str, Any], identity: Any = None) -> None:
        if identity is not None:
            LOGGER.info("Identity class received: %s", type(identity))
            LOGGER.info("Identity methods: %s", dir(identity))
        body = json.dumps(message, ensure_ascii=False)

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
                "Published message for agent 'jenkins' to exchange '%s' with routing key '%s'",
                self._exchange, self._routing_key,
            )
            LOGGER.info("Message successfully published.")
        finally:
            connection.close()