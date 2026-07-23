"""CPU metric collection."""

from __future__ import annotations

from typing import Any

from prometheus_client import PrometheusClient


class CPUCollector:
    """Collect CPU utilization and load metrics from Prometheus."""

    MODE_QUERY_TEMPLATE = 'avg(rate(node_cpu_seconds_total{mode="%s"}[5m])) * 100'

    QUERIES: dict[str, str] = {
        "overall_usage": '100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)',
        "per_core_usage": '100 - (rate(node_cpu_seconds_total{mode="idle"}[5m]) * 100)',
        "load_1m": "node_load1",
        "load_5m": "node_load5",
        "load_15m": "node_load15",
        "frequency_hz": "avg(node_cpu_scaling_frequency_hertz)",
        "frequency_hz_fallback": "avg(node_cpu_frequency_hertz)",
        "context_switches_per_sec": "rate(node_context_switches_total[5m])",
        "interrupts_per_sec": "sum(rate(node_intr_total[5m]))",
        "softirqs_per_sec": "sum(rate(node_softirqs_total[5m]))",
    }

    CPU_MODES = ("user", "system", "idle", "nice", "iowait", "irq", "softirq", "steal")

    def __init__(self, client: PrometheusClient) -> None:
        self._client = client

    def collect(self) -> dict[str, Any]:
        """Collect CPU metrics, including mode percentages and per-core usage."""

        per_core_samples = self._client.query_or_empty(self.QUERIES["per_core_usage"])
        per_core_usage: dict[str, float] = {}
        for sample in per_core_samples:
            core_id = sample.metric.get("cpu")
            if core_id is not None:
                per_core_usage[core_id] = sample.value

        mode_usage: dict[str, float | None] = {}
        for mode in self.CPU_MODES:
            mode_usage[mode] = self._client.query_scalar_or_none(self.MODE_QUERY_TEMPLATE % mode)

        frequency_hz = self._client.query_scalar_or_none(self.QUERIES["frequency_hz"])
        if frequency_hz is None:
            frequency_hz = self._client.query_scalar_or_none(self.QUERIES["frequency_hz_fallback"])

        return {
            "overall_usage": self._client.query_scalar_or_none(self.QUERIES["overall_usage"]),
            "per_core_usage": per_core_usage,
            "mode_usage": mode_usage,
            "load": {
                "1m": self._client.query_scalar_or_none(self.QUERIES["load_1m"]),
                "5m": self._client.query_scalar_or_none(self.QUERIES["load_5m"]),
                "15m": self._client.query_scalar_or_none(self.QUERIES["load_15m"]),
            },
            "frequency_mhz": (frequency_hz / 1_000_000.0) if frequency_hz is not None else None,
            "context_switches_per_sec": self._client.query_scalar_or_none(self.QUERIES["context_switches_per_sec"]),
            "interrupts_per_sec": self._client.query_scalar_or_none(self.QUERIES["interrupts_per_sec"]),
            "softirqs_per_sec": self._client.query_scalar_or_none(self.QUERIES["softirqs_per_sec"]),
        }
