"""Network metric collection."""

from __future__ import annotations

from typing import Any

from prometheus_client import PrometheusClient


class NetworkCollector:
    """Collect aggregate and per-interface network metrics."""

    QUERIES: dict[str, str] = {
        "rx_bytes": "sum(rate(node_network_receive_bytes_total[5m]))",
        "tx_bytes": "sum(rate(node_network_transmit_bytes_total[5m]))",
        "rx_packets": "sum(rate(node_network_receive_packets_total[5m]))",
        "tx_packets": "sum(rate(node_network_transmit_packets_total[5m]))",
        "rx_errors": "sum(rate(node_network_receive_errs_total[5m]))",
        "tx_errors": "sum(rate(node_network_transmit_errs_total[5m]))",
        "rx_dropped": "sum(rate(node_network_receive_drop_total[5m]))",
        "tx_dropped": "sum(rate(node_network_transmit_drop_total[5m]))",
        "if_rx_bytes": "rate(node_network_receive_bytes_total[5m])",
        "if_tx_bytes": "rate(node_network_transmit_bytes_total[5m])",
        "if_rx_packets": "rate(node_network_receive_packets_total[5m])",
        "if_tx_packets": "rate(node_network_transmit_packets_total[5m])",
        "if_rx_errors": "rate(node_network_receive_errs_total[5m])",
        "if_tx_errors": "rate(node_network_transmit_errs_total[5m])",
        "if_rx_drop": "rate(node_network_receive_drop_total[5m])",
        "if_tx_drop": "rate(node_network_transmit_drop_total[5m])",
        "if_state": "node_network_up",
    }

    def __init__(self, client: PrometheusClient) -> None:
        self._client = client

    def collect(self) -> dict[str, Any]:
        """Collect aggregate and per-interface network metrics."""

        interfaces: dict[str, dict[str, Any]] = {}

        def merge_interface_metric(query_key: str, field: str) -> None:
            for sample in self._client.query_or_empty(self.QUERIES[query_key]):
                interface = sample.metric.get("device") or sample.metric.get("interface") or "unknown"
                interfaces.setdefault(interface, {"interface": interface})
                interfaces[interface][field] = sample.value

        merge_interface_metric("if_rx_bytes", "rx_bytes_per_sec")
        merge_interface_metric("if_tx_bytes", "tx_bytes_per_sec")
        merge_interface_metric("if_rx_packets", "rx_packets_per_sec")
        merge_interface_metric("if_tx_packets", "tx_packets_per_sec")
        merge_interface_metric("if_rx_errors", "rx_errors_per_sec")
        merge_interface_metric("if_tx_errors", "tx_errors_per_sec")
        merge_interface_metric("if_rx_drop", "rx_dropped_per_sec")
        merge_interface_metric("if_tx_drop", "tx_dropped_per_sec")

        for sample in self._client.query_or_empty(self.QUERIES["if_state"]):
            interface = sample.metric.get("device") or sample.metric.get("interface") or "unknown"
            interfaces.setdefault(interface, {"interface": interface})
            interfaces[interface]["state"] = "UP" if sample.value >= 1 else "DOWN"

        return {
            "rx_bytes_per_sec": self._client.query_scalar_or_none(self.QUERIES["rx_bytes"]),
            "tx_bytes_per_sec": self._client.query_scalar_or_none(self.QUERIES["tx_bytes"]),
            "rx_packets_per_sec": self._client.query_scalar_or_none(self.QUERIES["rx_packets"]),
            "tx_packets_per_sec": self._client.query_scalar_or_none(self.QUERIES["tx_packets"]),
            "rx_errors_per_sec": self._client.query_scalar_or_none(self.QUERIES["rx_errors"]),
            "tx_errors_per_sec": self._client.query_scalar_or_none(self.QUERIES["tx_errors"]),
            "dropped_packets_per_sec": {
                "rx": self._client.query_scalar_or_none(self.QUERIES["rx_dropped"]),
                "tx": self._client.query_scalar_or_none(self.QUERIES["tx_dropped"]),
            },
            "interfaces": sorted(interfaces.values(), key=lambda item: str(item.get("interface", ""))),
        }
