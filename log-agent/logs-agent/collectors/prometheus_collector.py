from __future__ import annotations

from datetime import datetime, timezone
from socket import gethostname
from typing import Any

from config import AppConfig
from prometheus.client import PrometheusClientError
from prometheus.client import PrometheusHTTPClient
from prometheus.queries import PROMETHEUS_QUERIES, PrometheusQuery


class PrometheusMetricsCollector:
    def __init__(self, config: AppConfig, client: PrometheusHTTPClient | None = None) -> None:
        self._config = config
        self._client = client or PrometheusHTTPClient(config.prometheus.url)

    def collect(self) -> list[dict[str, Any]]:
        collected: list[dict[str, Any]] = []
        timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        hostname = self._config.prometheus_pipeline.host or gethostname()

        for query in PROMETHEUS_QUERIES:
            results = self._client.query(query.expression, timeout_seconds=self._config.prometheus_pipeline.query_timeout_seconds)
            if not results:
                collected.append(self._build_event(timestamp, hostname, query, value=None, labels={}))
                continue

            for result in results:
                value = self._parse_value(result.value)
                labels = dict(result.metric)
                collected.append(self._build_event(timestamp, hostname, query, value=value, labels=labels))

        return collected

    def sample_events(self) -> list[dict[str, Any]]:
        timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        hostname = self._config.prometheus_pipeline.host or gethostname()
        samples = {
            "cpu_usage": 72.5,
            "memory_usage": 65.4,
            "disk_usage": 41.2,
            "network_receive": 1048576.0,
            "network_transmit": 524288.0,
        }

        events: list[dict[str, Any]] = []
        for query in PROMETHEUS_QUERIES:
            events.append(
                self._build_event(
                    timestamp=timestamp,
                    hostname=hostname,
                    query=query,
                    value=samples.get(query.name),
                    labels={"sample": "offline"},
                )
            )
        return events

    def _build_event(
        self,
        timestamp: str,
        hostname: str,
        query: PrometheusQuery,
        value: float | None,
        labels: dict[str, Any],
    ) -> dict[str, Any]:
        event: dict[str, Any] = {
            "timestamp": timestamp,
            "source": "prometheus",
            "host": hostname,
            "metric": {
                "name": query.name,
                "category": query.category,
                "value": value,
                "unit": query.unit,
            },
            "collector": {
                "name": self._config.prometheus_pipeline.agent_name,
                "version": self._config.prometheus_pipeline.agent_version,
            },
        }
        if labels:
            event["labels"] = labels
        return event

    def _parse_value(self, value: list[Any]) -> float | None:
        if len(value) < 2:
            return None
        try:
            return float(value[1])
        except (TypeError, ValueError):
            return None
