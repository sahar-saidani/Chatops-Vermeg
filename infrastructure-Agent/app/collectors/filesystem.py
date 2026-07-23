"""Filesystem metric collection."""

from __future__ import annotations

from typing import Any

from prometheus_client import PrometheusClient


class FilesystemCollector:
    """Collect per-filesystem capacity and inode metrics."""

    FILTER = '{fstype!~"tmpfs|overlay|squashfs|devtmpfs|proc|sysfs"}'

    QUERIES: dict[str, str] = {
        "size": 'node_filesystem_size_bytes{fstype!~"tmpfs|overlay|squashfs|devtmpfs|proc|sysfs"}',
        "free": 'node_filesystem_avail_bytes{fstype!~"tmpfs|overlay|squashfs|devtmpfs|proc|sysfs"}',
        "files": 'node_filesystem_files{fstype!~"tmpfs|overlay|squashfs|devtmpfs|proc|sysfs"}',
        "files_free": 'node_filesystem_files_free{fstype!~"tmpfs|overlay|squashfs|devtmpfs|proc|sysfs"}',
        "readonly": 'node_filesystem_readonly{fstype!~"tmpfs|overlay|squashfs|devtmpfs|proc|sysfs"}',
    }

    def __init__(self, client: PrometheusClient) -> None:
        self._client = client

    def collect(self) -> dict[str, Any]:
        """Collect filesystem metrics for each mount point."""

        size_samples = self._client.query_or_empty(self.QUERIES["size"])
        free_samples = self._client.query_or_empty(self.QUERIES["free"])
        files_samples = self._client.query_or_empty(self.QUERIES["files"])
        files_free_samples = self._client.query_or_empty(self.QUERIES["files_free"])
        readonly_samples = self._client.query_or_empty(self.QUERIES["readonly"])

        def metric_key(sample_metric: dict[str, str]) -> tuple[str, str, str]:
            return (
                sample_metric.get("device", "unknown"),
                sample_metric.get("mountpoint", "unknown"),
                sample_metric.get("fstype", "unknown"),
            )

        index: dict[tuple[str, str, str], dict[str, Any]] = {}
        for sample in size_samples:
            key = metric_key(sample.metric)
            index[key] = {
                "device": key[0],
                "mountpoint": key[1],
                "filesystem_type": key[2],
                "total": sample.value,
                "free": None,
                "used": None,
                "usage_percent": None,
                "total_files": None,
                "free_files": None,
                "used_inodes": None,
                "free_inodes": None,
                "read_only": None,
            }

        for sample in free_samples:
            key = metric_key(sample.metric)
            index.setdefault(key, {"device": key[0], "mountpoint": key[1], "filesystem_type": key[2]})
            index[key]["free"] = sample.value

        for sample in files_samples:
            key = metric_key(sample.metric)
            index.setdefault(key, {"device": key[0], "mountpoint": key[1], "filesystem_type": key[2]})
            index[key]["total_files"] = sample.value

        for sample in files_free_samples:
            key = metric_key(sample.metric)
            index.setdefault(key, {"device": key[0], "mountpoint": key[1], "filesystem_type": key[2]})
            index[key]["free_files"] = sample.value

        for sample in readonly_samples:
            key = metric_key(sample.metric)
            index.setdefault(key, {"device": key[0], "mountpoint": key[1], "filesystem_type": key[2]})
            index[key]["read_only"] = bool(sample.value >= 1.0)

        filesystems: list[dict[str, Any]] = []
        for item in index.values():
            total = item.get("total")
            free = item.get("free")
            total_files = item.get("total_files")
            free_files = item.get("free_files")

            if total is not None and free is not None:
                item["used"] = total - free
                item["usage_percent"] = ((total - free) / total * 100.0) if total > 0 else None

            if total_files is not None and free_files is not None:
                item["used_inodes"] = total_files - free_files
                item["free_inodes"] = free_files

            filesystems.append(item)

        filesystems.sort(key=lambda fs: str(fs.get("mountpoint", "")))
        return {"filesystems": filesystems}