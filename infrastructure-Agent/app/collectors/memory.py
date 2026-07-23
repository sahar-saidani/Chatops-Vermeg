"""Memory metric collection."""

from __future__ import annotations

from typing import Any

from prometheus_client import PrometheusClient


class MemoryCollector:
    """Collect memory and swap metrics from Prometheus."""

    QUERIES: dict[str, str] = {
        "total": "node_memory_MemTotal_bytes",
        "free": "node_memory_MemFree_bytes",
        "available": "node_memory_MemAvailable_bytes",
        "cached": "node_memory_Cached_bytes",
        "buffers": "node_memory_Buffers_bytes",
        "active": "node_memory_Active_bytes",
        "inactive": "node_memory_Inactive_bytes",
        "swap_total": "node_memory_SwapTotal_bytes",
        "swap_free": "node_memory_SwapFree_bytes",
        "usage_percent": '100 * (1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)',
    }

    def __init__(self, client: PrometheusClient) -> None:
        self._client = client

    def collect(self) -> dict[str, Any]:
        """Collect memory usage and swap metrics."""

        total = self._client.query_scalar_or_none(self.QUERIES["total"])
        free = self._client.query_scalar_or_none(self.QUERIES["free"])
        available = self._client.query_scalar_or_none(self.QUERIES["available"])
        cached = self._client.query_scalar_or_none(self.QUERIES["cached"])
        buffers = self._client.query_scalar_or_none(self.QUERIES["buffers"])
        active = self._client.query_scalar_or_none(self.QUERIES["active"])
        inactive = self._client.query_scalar_or_none(self.QUERIES["inactive"])
        swap_total = self._client.query_scalar_or_none(self.QUERIES["swap_total"])
        swap_free = self._client.query_scalar_or_none(self.QUERIES["swap_free"])
        usage_percent = self._client.query_scalar_or_none(self.QUERIES["usage_percent"])

        used = (total - available) if total is not None and available is not None else None
        swap_used = (swap_total - swap_free) if swap_total is not None and swap_free is not None else None

        return {
            "total": total,
            "used": used,
            "free": free,
            "available": available,
            "cached": cached,
            "buffers": buffers,
            "active": active,
            "inactive": inactive,
            "swap_total": swap_total,
            "swap_used": swap_used,
            "swap_free": swap_free,
            "usage_percent": usage_percent,
        }
