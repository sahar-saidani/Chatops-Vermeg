"""Real RabbitMQ publisher for the logs-agent."""

from __future__ import annotations

import json
import logging
import math
from datetime import datetime, timezone
from typing import Any

import pika

LOGGER = logging.getLogger(__name__)


def _sanitize(value: Any) -> Any:
    """Recursively replace NaN/Infinity floats with None (JSON-strict compliant)."""
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return value
    if isinstance(value, dict):
        return {k: _sanitize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_sanitize(v) for v in value]
    return value


class RabbitMqPublisher:
    def __init__(
        self,
        url: str,
        exchange: str = "chatops.agents.exchange",
        routing_key: str = "agent.log.data",
    ) -> None:
        self._url = url
        self._exchange = exchange
        self._routing_key = routing_key

    def publish(self, agent_key: str, data: dict[str, Any]) -> None:
        envelope = {
            "agent": agent_key,
            "timestamp": datetime.now(tz=timezone.utc).isoformat().replace("+00:00", "Z"),
            "data": _sanitize(data),
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