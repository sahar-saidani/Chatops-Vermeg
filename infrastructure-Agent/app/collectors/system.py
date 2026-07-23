"""System metric collection."""

from __future__ import annotations

from typing import Any

from prometheus_client import PrometheusClient


class SystemCollector:
    """Collect host-level metadata and uptime indicators."""

    QUERIES: dict[str, str] = {
        "uname": "node_uname_info",
        "boot_time": "node_boot_time_seconds",
        "uptime": "time() - node_boot_time_seconds",
        "cpu_logical": 'count(node_cpu_seconds_total{mode="idle"})',
        "cpu_cores": 'count(count(node_cpu_seconds_total{mode="idle"}) by (cpu))',
        "logged_users": "node_users_logged_in",
    }

    def __init__(self, client: PrometheusClient) -> None:
        self._client = client

    def collect(self) -> dict[str, Any]:
        """Collect system metadata and uptime metrics."""

        uname_samples = self._client.query_or_empty(self.QUERIES["uname"])
        uname_metric = uname_samples[0].metric if uname_samples else {}

        return {
            "hostname": uname_metric.get("nodename") or uname_metric.get("instance") or "unknown",
            "kernel_version": uname_metric.get("release"),
            "os_version": uname_metric.get("sysname"),
            "architecture": uname_metric.get("machine"),
            "boot_time": self._client.query_scalar_or_none(self.QUERIES["boot_time"]),
            "uptime_seconds": self._client.query_scalar_or_none(self.QUERIES["uptime"]),
            "cpu_logical": self._client.query_scalar_or_none(self.QUERIES["cpu_logical"]),
            "cpu_cores": self._client.query_scalar_or_none(self.QUERIES["cpu_cores"]),
            "logged_users": self._client.query_scalar_or_none(self.QUERIES["logged_users"]),
        }