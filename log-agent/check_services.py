from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass(slots=True)
class CheckResult:
    name: str
    ok: bool
    details: dict[str, Any]


def fetch_text(url: str, timeout: int = 5) -> str:
    request = Request(url, headers={"User-Agent": "logs-agent-checker/1.0"})
    with urlopen(request, timeout=timeout) as response:  # nosec - local health check only
        return response.read().decode("utf-8", errors="replace")


def fetch_json(url: str, timeout: int = 5) -> dict[str, Any]:
    request = Request(url, headers={"User-Agent": "logs-agent-checker/1.0", "Accept": "application/json"})
    with urlopen(request, timeout=timeout) as response:  # nosec - local health check only
        payload = response.read().decode("utf-8", errors="replace")
    return json.loads(payload)


def check_prometheus_health(url: str, timeout: int = 5) -> CheckResult:
    body = fetch_text(f"{url.rstrip('/')}/-/healthy", timeout=timeout).strip()
    ok = body == "Prometheus is Healthy"
    return CheckResult(name="prometheus_health", ok=ok, details={"body": body})


def check_prometheus_runtimeinfo(url: str, timeout: int = 5) -> CheckResult:
    payload = fetch_json(f"{url.rstrip('/')}/api/v1/status/runtimeinfo", timeout=timeout)
    data = payload.get("data", {}) if isinstance(payload, dict) else {}
    details = {
        "startTime": data.get("startTime"),
        "goroutines": data.get("goroutines"),
        "version": data.get("version"),
    }
    ok = all(details.values())
    return CheckResult(name="prometheus_runtimeinfo", ok=ok, details=details)


def check_node_exporter(url: str, timeout: int = 5) -> CheckResult:
    body = fetch_text(f"{url.rstrip('/')}/metrics", timeout=timeout)
    ok = "node_exporter" in body or body.strip() != ""
    return CheckResult(name="node_exporter_metrics", ok=ok, details={"available": ok})


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Prometheus and Node Exporter availability")
    parser.add_argument("--prometheus-url", default="http://127.0.0.1:9090")
    parser.add_argument("--node-exporter-url", default="http://127.0.0.1:9100")
    parser.add_argument("--timeout", type=int, default=5)
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    checks = [
        check_prometheus_health(args.prometheus_url, timeout=args.timeout),
        check_prometheus_runtimeinfo(args.prometheus_url, timeout=args.timeout),
        check_node_exporter(args.node_exporter_url, timeout=args.timeout),
    ]

    output = {result.name: {"ok": result.ok, **result.details} for result in checks}
    print(json.dumps(output, indent=2, sort_keys=True))

    failures = [result.name for result in checks if not result.ok]
    if failures:
        print(f"Validation failed: {', '.join(failures)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
