from __future__ import annotations

from dataclasses import dataclass


CPU_USAGE_QUERY = '100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)'
MEMORY_USAGE_QUERY = '((node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes) * 100'
DISK_USAGE_QUERY = '100 - (node_filesystem_avail_bytes / node_filesystem_size_bytes * 100)'
NETWORK_RECEIVE_QUERY = 'rate(node_network_receive_bytes_total[5m])'
NETWORK_TRANSMIT_QUERY = 'rate(node_network_transmit_bytes_total[5m])'


@dataclass(frozen=True, slots=True)
class PrometheusQuery:
    name: str
    category: str
    expression: str
    unit: str


PROMETHEUS_QUERIES: tuple[PrometheusQuery, ...] = (
    PrometheusQuery(name="cpu_usage", category="cpu", expression=CPU_USAGE_QUERY, unit="percent"),
    PrometheusQuery(name="memory_usage", category="memory", expression=MEMORY_USAGE_QUERY, unit="percent"),
    PrometheusQuery(name="disk_usage", category="disk", expression=DISK_USAGE_QUERY, unit="percent"),
    PrometheusQuery(name="network_receive", category="network", expression=NETWORK_RECEIVE_QUERY, unit="bytes_per_second"),
    PrometheusQuery(name="network_transmit", category="network", expression=NETWORK_TRANSMIT_QUERY, unit="bytes_per_second"),
)
