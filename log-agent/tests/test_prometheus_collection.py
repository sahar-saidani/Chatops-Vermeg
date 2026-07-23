from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from urllib.error import URLError
from unittest import TestCase
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1] / "logs-agent"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from collectors.prometheus_collector import PrometheusMetricsCollector
from config import AppConfig, PrometheusPipelineConfig
from output_writer import JsonLinesWriter
from prometheus.client import PrometheusConnectionError, PrometheusHTTPClient, PrometheusResponseError


class FakePrometheusClient:
    def query(self, expression: str, timeout_seconds: int = 5):
        return [
            type(
                "PrometheusQueryResult",
                (),
                {"metric": {"instance": "centos-vm:9100"}, "value": [1720000000.0, "72.5"]},
            )
        ]


class PrometheusCollectionTests(TestCase):
    def setUp(self) -> None:
        self.config = AppConfig(
            prometheus_pipeline=PrometheusPipelineConfig(
                raw_path="output/prometheus_raw.json",
                structured_path="output/prometheus_structured.json",
                environment="test",
                host="centos-vm",
                agent_name="logs-agent",
                agent_version="1.0",
                collection_interval_seconds=60,
                query_timeout_seconds=5,
            )
        )

    def test_prometheus_connection_error_is_raised(self) -> None:
        client = PrometheusHTTPClient("http://127.0.0.1:9090")
        with patch("prometheus.client.urlopen", side_effect=URLError("unreachable")):
            with self.assertRaises(PrometheusConnectionError):
                client.query("up")

    def test_invalid_prometheus_response_is_rejected(self) -> None:
        class _BadResponse:
            def read(self):
                return b"not-json"

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        client = PrometheusHTTPClient("http://127.0.0.1:9090")
        with patch("prometheus.client.urlopen", return_value=_BadResponse()):
            with self.assertRaises(PrometheusResponseError):
                client.query("up")

    def test_json_generation_creates_raw_and_structured_files(self) -> None:
        collector = PrometheusMetricsCollector(self.config, client=FakePrometheusClient())
        events = collector.collect()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            writer = JsonLinesWriter(repo_root=temp_root)
            raw_path = writer.write_json_lines(temp_root / "prometheus_raw.json", events)
            structured_events = [
                {
                    "timestamp": event["timestamp"],
                    "environment": self.config.prometheus_pipeline.environment,
                    "host": event["host"],
                    "source": event["source"],
                    "metric_name": event["metric"]["name"],
                    "category": event["metric"]["category"],
                    "value": event["metric"]["value"],
                    "unit": event["metric"]["unit"],
                    "agent": event["collector"]["name"],
                }
                for event in events
            ]
            structured_path = writer.write_json_lines(temp_root / "prometheus_structured.json", structured_events)

            self.assertTrue(raw_path.exists())
            self.assertTrue(structured_path.exists())

            raw_line = raw_path.read_text(encoding="utf-8").splitlines()[0]
            structured_line = structured_path.read_text(encoding="utf-8").splitlines()[0]

            self.assertEqual(json.loads(raw_line)["metric"]["name"], "cpu_usage")
            self.assertEqual(json.loads(structured_line)["metric_name"], "cpu_usage")
