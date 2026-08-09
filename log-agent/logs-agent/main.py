
from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from collector import LogCollector
from config import load_config
from logger import configure_logging, get_logger


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Logs Agent - Filebeat/Logstash log collector and RabbitMQ publisher"
    )

    parser.add_argument(
        "--config",
        default=str(Path(__file__).with_name("config.yaml")),
        help="Path to config.yaml",
    )

    parser.add_argument(
        "--duration",
        type=float,
        default=30.0,
        help=(
            "Duration of the log collection in seconds. "
            "The default is 30 seconds so that the agent can be "
            "executed as a bounded subprocess by the ChatOps orchestrator. "
            "Use --duration 60 for a 60-second collection window."
        ),
    )

    return parser


async def amain() -> None:
    args = build_argument_parser().parse_args()

    # ------------------------------------------------------------------
    # Load configuration
    # ------------------------------------------------------------------
    config = load_config(args.config)

    # ------------------------------------------------------------------
    # Configure logging
    # ------------------------------------------------------------------
    configure_logging(config.logging.level)
    logger = get_logger("logs_agent")

    # ------------------------------------------------------------------
    # Build machine identity
    # ------------------------------------------------------------------
    identity = config.machine.to_machine_identity()

    logger.info(
        "%s",
        identity.startup_banner(
            "logs-agent",
            config.rabbitmq.url
            if config.rabbitmq.enabled
            else None,
        ),
    )

    logger.info(
        "Starting system log collection for "
        "machine=%s tenant=%s environment=%s",
        identity.machine_reference,
        identity.tenant_name,
        identity.environment_name,
    )

    # ------------------------------------------------------------------
    # Create collector
    # ------------------------------------------------------------------
    collector = LogCollector(
        config=config,
        logger=logger,
        identity=identity,
    )

    # ------------------------------------------------------------------
    # Bounded collection
    #
    # Filebeat -> Logstash -> Log Agent -> RabbitMQ
    #
    # The collector listens for the configured duration and then
    # terminates normally. This is important because the ChatOps
    # orchestrator executes agents as subprocesses and waits for
    # them to finish.
    # ------------------------------------------------------------------
    await collector.run(
        duration_seconds=args.duration
    )

    # ------------------------------------------------------------------
    # Summary returned to the orchestrator
    # ------------------------------------------------------------------
    summary = {
        "agent": "log",
        "machine_reference": identity.machine_reference,
        "tenant": identity.tenant_name,
        "environment": identity.environment_name,
        "environment_type": identity.environment_type,
        "duration_seconds": args.duration,
        "event_count": len(collector.collected_events),
        "events": collector.collected_events,
    }

    print(
        json.dumps(
            summary,
            ensure_ascii=False,
            default=str,
        ),
        flush=True,
    )

    logger.info(
        "Log collection completed successfully: "
        "machine=%s tenant=%s events=%d duration=%s",
        identity.machine_reference,
        identity.tenant_name,
        len(collector.collected_events),
        args.duration,
    )


def main() -> None:
    try:
        asyncio.run(amain())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
