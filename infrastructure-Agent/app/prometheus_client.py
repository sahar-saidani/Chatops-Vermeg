"""Prometheus HTTP API client."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import requests


class PrometheusClientError(RuntimeError):
	"""Raised when the Prometheus API cannot be queried safely."""


class PrometheusMetricUnavailableError(PrometheusClientError):
	"""Raised when a PromQL query returns no samples."""


@dataclass(slots=True)
class PrometheusSample:
	"""Normalized response from a Prometheus instant query."""

	metric: dict[str, str]
	value: float
	timestamp: datetime | None = None


class PrometheusClient:
	"""Small wrapper around the Prometheus instant query endpoint."""

	def __init__(self, base_url: str, timeout_seconds: float = 10.0) -> None:
		self._base_url = base_url.rstrip("/")
		self._timeout_seconds = timeout_seconds
		self._session = requests.Session()

	def query(self, query: str) -> list[PrometheusSample]:
		"""Execute an instant PromQL query and return normalized samples."""

		try:
			response = self._session.get(
				f"{self._base_url}/api/v1/query",
				params={"query": query},
				timeout=self._timeout_seconds,
			)
			response.raise_for_status()
		except requests.RequestException as exc:
			raise PrometheusClientError(f"Prometheus request failed for query: {query}") from exc

		try:
			payload: dict[str, Any] = response.json()
		except ValueError as exc:
			raise PrometheusClientError("Prometheus returned invalid JSON") from exc

		if payload.get("status") != "success":
			raise PrometheusClientError(payload.get("error", "Prometheus returned an error response"))

		data = payload.get("data") or {}
		result_type = data.get("resultType")
		result = data.get("result") or []

		if result_type == "scalar":
			if not isinstance(result, list) or len(result) != 2:
				raise PrometheusClientError(f"Unexpected scalar response for query: {query}")
			timestamp, value = result
			return [
				PrometheusSample(
					metric={},
					value=float(value),
					timestamp=datetime.fromtimestamp(float(timestamp), tz=timezone.utc),
				)
			]

		samples: list[PrometheusSample] = []
		for item in result:
			value_payload = item.get("value")
			if not value_payload or len(value_payload) < 2:
				continue

			timestamp_raw, value_raw = value_payload
			samples.append(
				PrometheusSample(
					metric={str(key): str(value) for key, value in item.get("metric", {}).items()},
					value=float(value_raw),
					timestamp=datetime.fromtimestamp(float(timestamp_raw), tz=timezone.utc),
				)
			)

		if not samples:
			raise PrometheusMetricUnavailableError(f"No data returned for query: {query}")

		return samples

	def query_scalar(self, query: str) -> float:
		"""Execute a query expected to return a single numeric value."""

		samples = self.query(query)
		return samples[0].value

	def query_scalar_or_none(self, query: str) -> float | None:
		"""Execute a query and return ``None`` when no samples are available."""

		try:
			return self.query_scalar(query)
		except PrometheusMetricUnavailableError:
			return None

	def query_or_empty(self, query: str) -> list[PrometheusSample]:
		"""Execute a query and return an empty list when no samples are available."""

		try:
			return self.query(query)
		except PrometheusMetricUnavailableError:
			return []
