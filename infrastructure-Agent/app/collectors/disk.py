"""Disk metric collection."""

from __future__ import annotations

from typing import Any

from prometheus_client import PrometheusClient


class DiskCollector:
    """Collect aggregate disk usage and IO metrics."""

    FILESYSTEM_FILTER = '{fstype!~"tmpfs|overlay|squashfs|devtmpfs|proc|sysfs"}'
    QUERIES: dict[str, str] = {
        "total": 'sum(node_filesystem_size_bytes{fstype!~"tmpfs|overlay|squashfs|devtmpfs|proc|sysfs"})',
        "free": 'sum(node_filesystem_avail_bytes{fstype!~"tmpfs|overlay|squashfs|devtmpfs|proc|sysfs"})',
        "usage_percent": '100 * (1 - (sum(node_filesystem_avail_bytes{fstype!~"tmpfs|overlay|squashfs|devtmpfs|proc|sysfs"}) / sum(node_filesystem_size_bytes{fstype!~"tmpfs|overlay|squashfs|devtmpfs|proc|sysfs"})))',
        "read_bytes_per_sec": "sum(rate(node_disk_read_bytes_total[5m]))",
        "write_bytes_per_sec": "sum(rate(node_disk_written_bytes_total[5m]))",
        "read_ops_per_sec": "sum(rate(node_disk_reads_completed_total[5m]))",
        "write_ops_per_sec": "sum(rate(node_disk_writes_completed_total[5m]))",
        "io_utilization_percent": "avg(rate(node_disk_io_time_seconds_total[5m])) * 100",
        "io_time_seconds_per_sec": "sum(rate(node_disk_io_time_seconds_total[5m]))",
        "read_time_per_sec": "sum(rate(node_disk_read_time_seconds_total[5m]))",
        "write_time_per_sec": "sum(rate(node_disk_write_time_seconds_total[5m]))",
    }

    def __init__(self, client: PrometheusClient) -> None:
        self._client = client

    def collect(self) -> dict[str, Any]:
        """Collect aggregate disk metrics and derived latency indicators."""

        total = self._client.query_scalar_or_none(self.QUERIES["total"])
        free = self._client.query_scalar_or_none(self.QUERIES["free"])
        usage_percent = self._client.query_scalar_or_none(self.QUERIES["usage_percent"])
        read_ops = self._client.query_scalar_or_none(self.QUERIES["read_ops_per_sec"])
        write_ops = self._client.query_scalar_or_none(self.QUERIES["write_ops_per_sec"])
        read_time = self._client.query_scalar_or_none(self.QUERIES["read_time_per_sec"])
        write_time = self._client.query_scalar_or_none(self.QUERIES["write_time_per_sec"])

        used = (total - free) if total is not None and free is not None else None
        read_latency_ms = ((read_time / read_ops) * 1000.0) if read_time is not None and read_ops and read_ops > 0 else None
        write_latency_ms = (
            ((write_time / write_ops) * 1000.0) if write_time is not None and write_ops and write_ops > 0 else None
        )

        return {
            "usage_percent": usage_percent,
            "total": total,
            "used": used,
            "free": free,
            "read_bytes_per_sec": self._client.query_scalar_or_none(self.QUERIES["read_bytes_per_sec"]),
            "write_bytes_per_sec": self._client.query_scalar_or_none(self.QUERIES["write_bytes_per_sec"]),
            "read_ops_per_sec": read_ops,
            "write_ops_per_sec": write_ops,
            "io_utilization_percent": self._client.query_scalar_or_none(self.QUERIES["io_utilization_percent"]),
            "io_time_seconds_per_sec": self._client.query_scalar_or_none(self.QUERIES["io_time_seconds_per_sec"]),
            "latency": {
                "read_ms": read_latency_ms,
                "write_ms": write_latency_ms,
            },
        }
