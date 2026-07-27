from __future__ import annotations

import argparse
import logging
from pathlib import Path

from agent.analyzer import Analyzer
from agent.collector import JiraCollector
from agent.reporter import ReportGenerator
from config.settings import Settings


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")
logger = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Standalone Jira analysis agent")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("collect", help="Collect Jira data")
    subparsers.add_parser("analyze", help="Analyze collected data")
    subparsers.add_parser("report", help="Generate reports")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    settings = Settings.from_env()
    collector = JiraCollector.from_settings(settings)
    analyzer = Analyzer()
    reporter = ReportGenerator()

    if args.command == "collect":
        payload = collector.collect_project_snapshot()
        collector.save_snapshot(payload)
        logger.info("Collection completed")
        return 0

    snapshot = collector.load_snapshot()
    if snapshot is None:
        logger.error("No collected data found. Run 'python cli.py collect' first.")
        return 1

    analysis = analyzer.analyze(snapshot)

    if args.command == "analyze":
        collector.save_analysis(analysis)
        logger.info("Analysis completed")
        return 0

    report = reporter.generate(snapshot=snapshot, analysis=analysis)
    reporter.save_reports(report)
    logger.info("Reports generated in %s", Path(settings.reports_dir).resolve())

    if settings.rabbitmq_url:
        from rabbitmq_publisher import RabbitMqPublisher

        publisher = RabbitMqPublisher(url=settings.rabbitmq_url)
        publisher.publish(agent_key="jira", data=report)
        logger.info("Report published to RabbitMQ")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
