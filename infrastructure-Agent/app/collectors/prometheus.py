"""Prometheus and scrape health metric collection."""

from __future__ import annotations

from typing import Any

from prometheus_client import PrometheusClient


class PrometheusCollector:
    """Collect Prometheus target and scrape-level health metrics."""

    QUERIES: dict[str, str] = {
        "up": "up",
        "scrape_duration": "scrape_duration_seconds",
        "scrape_success_ratio": "avg(up) * 100",
    }

    def __init__(self, client: PrometheusClient) -> None:
        self._client = client

    def collect(self) -> dict[str, Any]:
        """Collect target-level availability and scrape metrics from Prometheus."""

        up_samples = self._client.query_or_empty(self.QUERIES["up"])
        scrape_duration_samples = self._client.query_or_empty(self.QUERIES["scrape_duration"])

        targets: list[dict[str, Any]] = []
        for sample in up_samples:
            targets.append(
                {
                    "job": sample.metric.get("job"),
                    "instance": sample.metric.get("instance"),
                    "status": "UP" if sample.value >= 1 else "DOWN",
                }
            )

        average_scrape_duration = None
        if scrape_duration_samples:
            average_scrape_duration = sum(sample.value for sample in scrape_duration_samples) / len(scrape_duration_samples)

        availability = "UP" if targets and all(target["status"] == "UP" for target in targets) else "DOWN"

        return {
            "availability": availability,
            "targets": targets,
            "scrape_duration_seconds": average_scrape_duration,
            "scrape_success_percent": self._client.query_scalar_or_none(self.QUERIES["scrape_success_ratio"]),
        }