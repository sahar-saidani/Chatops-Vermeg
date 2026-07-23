"""Service metric collection."""

from __future__ import annotations

from typing import Any

from prometheus_client import PrometheusClient


class ServicesCollector:
    """Collect service states from systemd-related node exporter metrics when available."""

    QUERIES: dict[str, str] = {
        "active": 'count(node_systemd_unit_state{state="active",name!=""} == 1)',
        "failed": 'count(node_systemd_unit_state{state="failed",name!=""} == 1)',
        "running": 'count(node_systemd_unit_state{state="active",type="service",name!=""} == 1)',
    }

    def __init__(self, client: PrometheusClient) -> None:
        self._client = client

    def collect(self) -> dict[str, Any]:
        """Collect service availability metrics, if exported by Prometheus targets."""

        return {
            "running_services": self._client.query_scalar_or_none(self.QUERIES["running"]),
            "failed_services": self._client.query_scalar_or_none(self.QUERIES["failed"]),
            "active_services": self._client.query_scalar_or_none(self.QUERIES["active"]),
        }