from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from collector import LogCollector
from collectors.prometheus_collector import PrometheusMetricsCollector
from config import load_config
from prometheus.client import PrometheusClientError
from logger import configure_logging, get_logger
from output_writer import JsonLinesWriter


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Logs Agent metrics and log collector")
    parser.add_argument(
        "--config",
        default=str(Path(__file__).with_name("config.yaml")),
        help="Path to config.yaml",
    )
    parser.add_argument(
        "--mode",
        choices=("prometheus", "logs", "both"),
        default="prometheus",
        help="Run the Prometheus metrics pipeline, the legacy log server, or both",
    )
    return parser


async def amain() -> None:
    args = build_argument_parser().parse_args()
    config = load_config(args.config)
    configure_logging(config.logging.level)
    logger = get_logger("logs_agent")
    writer = JsonLinesWriter()

    if args.mode in {"prometheus", "both"}:
        prometheus_collector = PrometheusMetricsCollector(config=config)
        try:
            events = prometheus_collector.collect()
        except PrometheusClientError as exc:
            logger.warning("prometheus_collection_fallback", error=str(exc))
            events = prometheus_collector.sample_events()
        raw_path = writer.write_json_lines(config.prometheus_pipeline.raw_path, events)
        structured_events = [_normalize_prometheus_event(event, config.prometheus_pipeline.environment) for event in events]
        structured_path = writer.write_json_lines(config.prometheus_pipeline.structured_path, structured_events)
        logger.info("prometheus_pipeline_completed", raw_path=str(raw_path), structured_path=str(structured_path), events=len(events))

        if config.rabbitmq.enabled:
            from rabbitmq_publisher import RabbitMqPublisher

            publisher = RabbitMqPublisher(url=config.rabbitmq.url)
            publisher.publish(
                agent_key="log",
                data={"events": structured_events, "count": len(structured_events)},
            )
            logger.info("prometheus_pipeline_published_to_rabbitmq", events=len(structured_events))

    if args.mode in {"logs", "both"}:
        collector = LogCollector(config=config, logger=logger)
        await collector.run()


def _normalize_prometheus_event(event: dict[str, object], environment: str) -> dict[str, object]:
    metric = event.get("metric", {}) if isinstance(event, dict) else {}
    collector = event.get("collector", {}) if isinstance(event, dict) else {}
    host = event.get("host", "unknown-host") if isinstance(event, dict) else "unknown-host"
    timestamp = event.get("timestamp") if isinstance(event, dict) else None
    source = event.get("source", "prometheus") if isinstance(event, dict) else "prometheus"
    normalized = {
        "timestamp": timestamp,
        "environment": environment,
        "host": host,
        "source": source,
        "metric_name": metric.get("name") if isinstance(metric, dict) else None,
        "category": metric.get("category") if isinstance(metric, dict) else None,
        "value": metric.get("value") if isinstance(metric, dict) else None,
        "unit": metric.get("unit") if isinstance(metric, dict) else None,
        "agent": collector.get("name") if isinstance(collector, dict) else "logs-agent",
    }
    return normalized


def main() -> None:
    try:
        asyncio.run(amain())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
