
from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from collector import LogCollector
from config import load_config
from logger import configure_logging, get_logger
from output_writer import JsonLinesWriter


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Logs Agent metrics and log collector"
    )

    parser.add_argument(
        "--config",
        default=str(Path(__file__).with_name("config.yaml")),
        help="Path to config.yaml",
    )

    parser.add_argument(
        "--mode",
        choices=("prometheus", "logs", "both"),
        default="prometheus",
        help="Run the Prometheus metrics pipeline, the log collector, or both",
    )

    return parser


async def amain() -> None:
    args = build_argument_parser().parse_args()

    # Load configuration
    config = load_config(args.config)

    # Configure logging
    configure_logging(config.logging.level)
    logger = get_logger("logs_agent")

    # Build machine identity
    identity = config.machine.to_machine_identity()

    logger.info(
        "%s",
        identity.startup_banner(
            "logs-agent",
            config.rabbitmq.url if config.rabbitmq.enabled else None,
        ),
    )

    writer = JsonLinesWriter()

    # ------------------------------------------------------------------
    # PROMETHEUS MODE
    # ------------------------------------------------------------------
    if args.mode in {"prometheus", "both"}:
        from collectors.prometheus_collector import PrometheusMetricsCollector
        from prometheus.client import PrometheusClientError

        prometheus_collector = PrometheusMetricsCollector(config=config)

        try:
            events = prometheus_collector.collect()

        except PrometheusClientError as exc:
            logger.warning(
                "prometheus_collection_fallback",
                error=str(exc),
            )

            events = prometheus_collector.sample_events()

        # Write raw Prometheus events
        raw_path = writer.write_json_lines(
            config.prometheus_pipeline.raw_path,
            events,
        )

        # Normalize Prometheus events
        structured_events = [
            _normalize_prometheus_event(
                event,
                config.prometheus_pipeline.environment,
            )
            for event in events
        ]

        # Write structured events
        structured_path = writer.write_json_lines(
            config.prometheus_pipeline.structured_path,
            structured_events,
        )

        logger.info(
            "prometheus_pipeline_completed",
            raw_path=str(raw_path),
            structured_path=str(structured_path),
            events=len(events),
        )

        # Publish Prometheus events to RabbitMQ
        if config.rabbitmq.enabled:
            from rabbitmq_publisher import RabbitMqPublisher

            publisher = RabbitMqPublisher(
                url=config.rabbitmq.url,
            )

            publisher.publish(
                agent_key="log",
                data={
                    "events": structured_events,
                    "count": len(structured_events),
                },
                identity=identity,
            )

            logger.info("Message successfully published.")

    # ------------------------------------------------------------------
    # LOGS MODE
    # ------------------------------------------------------------------
    if args.mode in {"logs", "both"}:
        logger.info(
            "Starting system log collection for machine=%s tenant=%s environment=%s",
            identity.machine_reference,
            identity.tenant_name,
            identity.environment_name,
        )

        collector = LogCollector(
            config=config,
            logger=logger,
        )

        await collector.run()


def _normalize_prometheus_event(
    event: dict[str, object],
    environment: str,
) -> dict[str, object]:
    """
    Normalize one Prometheus event into the structure consumed
    by the ChatOps pipeline.
    """

    metric = (
        event.get("metric", {})
        if isinstance(event, dict)
        else {}
    )

    collector = (
        event.get("collector", {})
        if isinstance(event, dict)
        else {}
    )

    host = (
        event.get("host", "unknown-host")
        if isinstance(event, dict)
        else "unknown-host"
    )

    timestamp = (
        event.get("timestamp")
        if isinstance(event, dict)
        else None
    )

    source = (
        event.get("source", "prometheus")
        if isinstance(event, dict)
        else "prometheus"
    )

    normalized = {
        "timestamp": timestamp,
        "environment": environment,
        "host": host,
        "source": source,
        "metric_name": (
            metric.get("name")
            if isinstance(metric, dict)
            else None
        ),
        "category": (
            metric.get("category")
            if isinstance(metric, dict)
            else None
        ),
        "value": (
            metric.get("value")
            if isinstance(metric, dict)
            else None
        ),
        "unit": (
            metric.get("unit")
            if isinstance(metric, dict)
            else None
        ),
        "agent": (
            collector.get("name")
            if isinstance(collector, dict)
            else "logs-agent"
        ),
    }

    return normalized


def main() -> None:
    try:
        asyncio.run(amain())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

