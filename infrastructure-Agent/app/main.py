"""Infrastructure monitoring agent entry point."""

from __future__ import annotations

import argparse
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, timezone
from typing import Any

from analyzer.health import HealthAnalyzer
from collectors.cpu import CPUCollector
from collectors.disk import DiskCollector
from collectors.filesystem import FilesystemCollector
from collectors.memory import MemoryCollector
from collectors.network import NetworkCollector
from collectors.processes import ProcessCollector
from collectors.prometheus import PrometheusCollector
from collectors.services import ServicesCollector
from collectors.socket import SocketCollector
from collectors.system import SystemCollector
from config import Settings, ensure_log_directory, resolve_project_path
from report import build_health_report_text, format_metric, format_network, save_latest_health_report
from prometheus_client import PrometheusClient, PrometheusClientError


def setup_logging(settings: Settings) -> logging.Logger:
    """Configure console and file logging."""

    log_path = resolve_project_path(settings.log_file)
    ensure_log_directory(str(log_path))
    logger = logging.getLogger("infrastructure_agent")
    logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))
    logger.handlers.clear()
    logger.propagate = False

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    file_handler = RotatingFileHandler(log_path, maxBytes=1_048_576, backupCount=3)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""

    parser = argparse.ArgumentParser(description="Infrastructure Health Monitoring Agent")
    parser.add_argument("--collect", action="store_true", help="Collect the current health snapshot and exit")
    return parser.parse_args()


def main() -> int:
    """Program entry point."""

    settings = Settings.from_env()
    logger = setup_logging(settings)
    identity = settings.to_machine_identity()
    logger.info("%s", identity.startup_banner("infrastructure-agent", settings.rabbitmq_url))
    args = parse_args()

    if not args.collect:
        print("Use --collect to generate a health report.")
        return 0

    logger.info("Connecting to Prometheus at %s", settings.prometheus_url)
    client = PrometheusClient(settings.prometheus_url, timeout_seconds=settings.prometheus_timeout_seconds)
    prometheus_collector = PrometheusCollector(client)
    cpu_collector = CPUCollector(client)
    memory_collector = MemoryCollector(client)
    disk_collector = DiskCollector(client)
    filesystem_collector = FilesystemCollector(client)
    network_collector = NetworkCollector(client)
    process_collector = ProcessCollector(client)
    system_collector = SystemCollector(client)
    socket_collector = SocketCollector(client)
    services_collector = ServicesCollector(client)
    health_analyzer = HealthAnalyzer()

    try:
        logger.info("Metric collection started")
        metrics: dict[str, Any] = {
            "prometheus": prometheus_collector.collect(),
            "cpu": cpu_collector.collect(),
            "memory": memory_collector.collect(),
            "disk": disk_collector.collect(),
            "filesystem": filesystem_collector.collect(),
            "network": network_collector.collect(),
            "processes": process_collector.collect(),
            "system": system_collector.collect(),
            "socket": socket_collector.collect(),
            "services": services_collector.collect(),
        }
    except PrometheusClientError as exc:
        logger.error("Prometheus collection failed: %s", exc)
        print(f"Collection failed: {exc}")
        return 2
    except Exception as exc:
        logger.exception("Unexpected collection failure")
        print(f"Collection failed: {exc}")
        return 2

    report = health_analyzer.analyze(metrics)
    timestamp = datetime.now(timezone.utc)

    prometheus = metrics.get("prometheus", {})
    cpu = metrics.get("cpu", {})
    memory = metrics.get("memory", {})
    disk = metrics.get("disk", {})
    network = metrics.get("network", {})

    report_text = build_health_report_text(
        timestamp=timestamp,
        target=settings.target_name,
        metrics=metrics,
        health_report=report,
    )

    print(report_text, end="")

    try:
        save_latest_health_report(report_text)
    except Exception:
        logger.exception("Failed to write the latest health report")
        print("Warning: failed to save reports/latest_health_report.txt")

    logger.info(
        "Health analysis result: %s | Problems=%s",
        report.status,
        "; ".join(report.problems) if report.problems else "none",
    )
    logger.info(
        "Metric collection completed | Availability=%s | CPU=%s | Memory=%s | Disk=%s | Network RX=%s | Network TX=%s",
        prometheus.get("availability", "DOWN"),
        format_metric(cpu.get("overall_usage")),
        format_metric(memory.get("usage_percent")),
        format_metric(disk.get("usage_percent")),
        format_network(network.get("rx_bytes_per_sec")),
        format_network(network.get("tx_bytes_per_sec")),
    )

    if settings.rabbitmq_url:
        from rabbitmq_publisher import RabbitMqPublisher

        publish_payload = {
            "target": settings.target_name,
            "timestamp": timestamp.isoformat(),
            "status": report.status,
            "problems": report.problems,
            "metrics": metrics,
        }
        publisher = RabbitMqPublisher(url=settings.rabbitmq_url)
        publisher.publish(agent_key="infrastructure", data=publish_payload, identity=identity)
        logger.info("Message successfully published.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

