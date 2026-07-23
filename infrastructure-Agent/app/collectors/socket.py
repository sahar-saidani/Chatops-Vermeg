"""Socket and connection metric collection."""

from __future__ import annotations

from typing import Any

from prometheus_client import PrometheusClient


class SocketCollector:
    """Collect TCP/UDP/socket statistics from Prometheus."""

    QUERIES: dict[str, str] = {
        "tcp_inuse": "node_sockstat_TCP_inuse",
        "udp_inuse": "node_sockstat_UDP_inuse",
        "listening": "node_sockstat_TCP_alloc",
        "established": "node_netstat_Tcp_CurrEstab",
        "time_wait": "node_sockstat_TCP_tw",
        "close_wait": "node_netstat_Tcp_CurrEstab{state=\"CLOSE-WAIT\"}",
    }

    def __init__(self, client: PrometheusClient) -> None:
        self._client = client

    def collect(self) -> dict[str, Any]:
        """Collect socket-level connection counters."""

        close_wait = self._client.query_scalar_or_none(self.QUERIES["close_wait"])
        if close_wait is None:
            close_wait = self._estimate_close_wait_from_state()

        return {
            "tcp_connections": self._client.query_scalar_or_none(self.QUERIES["tcp_inuse"]),
            "udp_sockets": self._client.query_scalar_or_none(self.QUERIES["udp_inuse"]),
            "listening_sockets": self._client.query_scalar_or_none(self.QUERIES["listening"]),
            "established_connections": self._client.query_scalar_or_none(self.QUERIES["established"]),
            "time_wait": self._client.query_scalar_or_none(self.QUERIES["time_wait"]),
            "close_wait": close_wait,
        }

    def _estimate_close_wait_from_state(self) -> float | None:
        """Estimate CLOSE_WAIT from netstat metrics when direct state is unavailable."""

        state_samples = self._client.query_or_empty("node_netstat_TcpExt_TCPAbortOnClose")
        if not state_samples:
            return None
        return sum(sample.value for sample in state_samples)