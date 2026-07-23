from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class PrometheusClientError(RuntimeError):
    pass


class PrometheusConnectionError(PrometheusClientError):
    pass


class PrometheusTimeoutError(PrometheusClientError):
    pass


class PrometheusResponseError(PrometheusClientError):
    pass


@dataclass(slots=True)
class PrometheusQueryResult:
    metric: dict[str, Any]
    value: list[Any]


class PrometheusHTTPClient:
    def __init__(self, base_url: str = "http://127.0.0.1:9090") -> None:
        self._base_url = base_url.rstrip("/")

    def query(self, expression: str, timeout_seconds: int = 5) -> list[PrometheusQueryResult]:
        url = f"{self._base_url}/api/v1/query?{urlencode({'query': expression})}"
        request = Request(url, headers={"Accept": "application/json", "User-Agent": "logs-agent-prometheus/1.0"})
        try:
            with urlopen(request, timeout=timeout_seconds) as response:  # nosec - local service endpoint
                raw_payload = response.read().decode("utf-8", errors="replace")
        except HTTPError as exc:
            raise PrometheusConnectionError(f"Prometheus HTTP error: {exc.code}") from exc
        except TimeoutError as exc:
            raise PrometheusTimeoutError("Timed out connecting to Prometheus") from exc
        except URLError as exc:
            reason = getattr(exc, "reason", exc)
            raise PrometheusConnectionError(f"Unable to connect to Prometheus: {reason}") from exc

        try:
            payload = json.loads(raw_payload)
        except json.JSONDecodeError as exc:
            raise PrometheusResponseError("Prometheus returned invalid JSON") from exc

        if not isinstance(payload, dict) or payload.get("status") != "success":
            raise PrometheusResponseError("Prometheus returned a non-success response")

        data = payload.get("data")
        if not isinstance(data, dict):
            raise PrometheusResponseError("Prometheus response data is invalid")

        result_type = data.get("resultType")
        results = data.get("result")
        if result_type != "vector" or not isinstance(results, list):
            raise PrometheusResponseError("Prometheus response shape is unsupported")

        parsed_results: list[PrometheusQueryResult] = []
        for item in results:
            if not isinstance(item, dict):
                continue
            metric = item.get("metric") if isinstance(item.get("metric"), dict) else {}
            value = item.get("value") if isinstance(item.get("value"), list) else []
            parsed_results.append(PrometheusQueryResult(metric=metric, value=value))
        return parsed_results
