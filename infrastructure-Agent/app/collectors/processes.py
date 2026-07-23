"""Process metric collection."""

from __future__ import annotations

from typing import Any

from prometheus_client import PrometheusClient


class ProcessCollector:
    """Collect process state metrics and available top-process indicators."""

    QUERIES: dict[str, str] = {
        "running": "node_procs_running",
        "blocked": "node_procs_blocked",
        "state": "node_processes_state",
        "top_cpu": "topk(5, rate(namedprocess_namegroup_cpu_seconds_total[5m]))",
        "top_memory": "topk(5, namedprocess_namegroup_memory_bytes)",
    }

    def __init__(self, client: PrometheusClient) -> None:
        self._client = client

    def collect(self) -> dict[str, Any]:
        """Collect process counts and top process metrics when available."""

        state_counts = {
            "total": None,
            "running": self._client.query_scalar_or_none(self.QUERIES["running"]),
            "sleeping": None,
            "stopped": None,
            "zombie": None,
            "blocked": self._client.query_scalar_or_none(self.QUERIES["blocked"]),
        }

        state_samples = self._client.query_or_empty(self.QUERIES["state"])
        if state_samples:
            total = 0.0
            for sample in state_samples:
                state_label = sample.metric.get("state", "unknown").lower()
                total += sample.value
                if state_label == "running":
                    state_counts["running"] = sample.value
                elif state_label == "sleeping":
                    state_counts["sleeping"] = sample.value
                elif state_label == "stopped":
                    state_counts["stopped"] = sample.value
                elif state_label == "zombie":
                    state_counts["zombie"] = sample.value
                elif state_label in {"blocked", "uninterruptible"}:
                    state_counts["blocked"] = sample.value
            state_counts["total"] = total

        top_cpu_samples = self._client.query_or_empty(self.QUERIES["top_cpu"])
        top_memory_samples = self._client.query_or_empty(self.QUERIES["top_memory"])

        def process_name(sample_metric: dict[str, str]) -> str:
            return (
                sample_metric.get("groupname")
                or sample_metric.get("name")
                or sample_metric.get("comm")
                or sample_metric.get("instance")
                or "unknown"
            )

        top_by_cpu = [
            {"process": process_name(sample.metric), "cpu_seconds_per_sec": sample.value} for sample in top_cpu_samples
        ]
        top_by_memory = [
            {"process": process_name(sample.metric), "memory_bytes": sample.value} for sample in top_memory_samples
        ]

        return {
            "counts": state_counts,
            "top_by_cpu": top_by_cpu,
            "top_by_memory": top_by_memory,
        }