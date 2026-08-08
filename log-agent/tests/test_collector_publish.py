"""
[REGENERATED — not the literal file from the previous session, rebuilt to
be consistent with collector.py's LogCollector / DuplicateDetector. It
mocks rabbitmq_publisher.RabbitMqPublisher, so it does not require a real
broker. Review field names against your actual machine_identity.py and
rabbitmq_publisher.py before trusting this as-is.]
"""

from __future__ import annotations

import asyncio
import sys
import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1] / "logs-agent"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from collector import DuplicateDetector, LogCollector
from config import AppConfig, RabbitMqConfig


class _FakeLogger:
    """Minimal structlog-like logger that just records calls."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict]] = []

    def _record(self, level: str, event: str, **kwargs) -> None:
        self.calls.append((level, event, kwargs))

    def info(self, event: str, **kwargs) -> None:
        self._record("info", event, **kwargs)

    def debug(self, event: str, **kwargs) -> None:
        self._record("debug", event, **kwargs)

    def warning(self, event: str, **kwargs) -> None:
        self._record("warning", event, **kwargs)

    def error(self, event: str, **kwargs) -> None:
        self._record("error", event, **kwargs)


def _run(coro):
    return asyncio.run(coro)


def _config(enabled: bool) -> AppConfig:
    config = AppConfig()
    config.rabbitmq = RabbitMqConfig(enabled=enabled, url="amqp://guest:guest@localhost:5672/")
    return config


def _fake_identity() -> SimpleNamespace:
    return SimpleNamespace(
        tenant_name="NNBE",
        environment_name="DEV",
        environment_type="STANDALONE",
        machine_reference="NNBE-DEV-01",
    )


SAMPLE_LINUX_LINE = (
    b'{"message":"Failed password for invalid user demo from 127.0.0.1 port 2222 ssh2",'
    b'"host":{"name":"NNBE-DEV-01"},'
    b'"log":{"file":{"path":"/var/log/secure"}},'
    b'"process":{"name":"sshd"}}\n'
)


def test_publish_called_with_normalized_event_when_rabbitmq_enabled() -> None:
    identity = _fake_identity()
    logger = _FakeLogger()

    with patch("rabbitmq_publisher.RabbitMqPublisher") as MockPublisher:
        mock_instance = MockPublisher.return_value
        collector = LogCollector(_config(enabled=True), logger, identity=identity)

        _run(collector._process_line(SAMPLE_LINUX_LINE))

        assert mock_instance.publish.call_count == 1
        _, kwargs = mock_instance.publish.call_args
        assert kwargs["agent_key"] == "log"
        assert kwargs["identity"] is identity

        data = kwargs["data"]
        assert data["hostname"] == "NNBE-DEV-01"
        assert data["source"] == "/var/log/secure"
        assert data["process"] == "sshd"
        # Explicit process name should win over source-based inference.
        assert data["service"] == "sshd"
        assert "logs-agent" in data["tags"]


def test_no_publisher_created_when_rabbitmq_disabled() -> None:
    logger = _FakeLogger()

    with patch("rabbitmq_publisher.RabbitMqPublisher") as MockPublisher:
        collector = LogCollector(_config(enabled=False), logger, identity=None)

        MockPublisher.assert_not_called()
        assert collector._publisher is None

        # Must not raise even with no publisher and no identity configured.
        _run(collector._process_line(SAMPLE_LINUX_LINE))


def test_duplicate_events_within_window_are_published_once() -> None:
    identity = _fake_identity()
    logger = _FakeLogger()

    with patch("rabbitmq_publisher.RabbitMqPublisher") as MockPublisher:
        mock_instance = MockPublisher.return_value
        collector = LogCollector(_config(enabled=True), logger, identity=identity)

        _run(collector._process_line(SAMPLE_LINUX_LINE))
        _run(collector._process_line(SAMPLE_LINUX_LINE))

        assert mock_instance.publish.call_count == 1


def test_publish_failure_is_caught_and_logged_not_raised() -> None:
    identity = _fake_identity()
    logger = _FakeLogger()

    with patch("rabbitmq_publisher.RabbitMqPublisher") as MockPublisher:
        mock_instance = MockPublisher.return_value
        mock_instance.publish.side_effect = RuntimeError("broker unreachable")

        collector = LogCollector(_config(enabled=True), logger, identity=identity)

        # A broker failure must not crash the collector; it should be logged.
        _run(collector._process_line(SAMPLE_LINUX_LINE))

        error_events = [event for level, event, _ in logger.calls if level == "error"]
        assert "rabbitmq_publish_failed" in error_events


def test_malformed_json_line_is_skipped_without_publishing() -> None:
    identity = _fake_identity()
    logger = _FakeLogger()

    with patch("rabbitmq_publisher.RabbitMqPublisher") as MockPublisher:
        mock_instance = MockPublisher.return_value
        collector = LogCollector(_config(enabled=True), logger, identity=identity)

        _run(collector._process_line(b"not valid json\n"))

        mock_instance.publish.assert_not_called()
        warning_events = [event for level, event, _ in logger.calls if level == "warning"]
        assert "malformed_json" in warning_events


def test_duplicate_detector_purges_after_window() -> None:
    detector = DuplicateDetector(window_seconds=1)
    payload = {"message": "hello"}

    assert detector.seen(payload) is False
    assert detector.seen(payload) is True

    time.sleep(1.2)
    assert detector.seen(payload) is False