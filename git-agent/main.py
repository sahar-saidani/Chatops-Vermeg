from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Sequence

from agent.git_agent import GitRepositoryAgent
from config.settings import Settings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="git-agent", description="Analyze local or GitHub repositories.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze = subparsers.add_parser("analyze", help="Analyze a repository")
    analyze.add_argument("--path", type=Path, help="Path to a local Git repository")
    analyze.add_argument("--repo", help="GitHub repository in owner/name format")
    analyze.add_argument("--output", type=Path, default=Path("reports"), help="Output directory for reports")
    analyze.add_argument("--token", help="GitHub token for authenticated API access", default=None)
    analyze.add_argument("--stale-branch-days", type=int, default=90)
    analyze.add_argument("--active-window-days", type=int, default=30)
    return parser


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "analyze":
        settings = Settings.from_env(
            output_dir=args.output,
            github_token=args.token,
            stale_branch_days=args.stale_branch_days,
            active_window_days=args.active_window_days,
        )
        configure_logging()
        agent = GitRepositoryAgent(settings=settings)
        report = agent.analyze(path=args.path, repo=args.repo)
        logger = logging.getLogger(__name__)
        logger.info("Generated report for %s", report.snapshot.repository.name)

        if settings.rabbitmq_enabled:
            from dataclasses import asdict
            from messaging.rabbitmq_publisher import RabbitMqPublisher

            publisher = RabbitMqPublisher(url=settings.rabbitmq_url)
            publisher.publish(agent_key="git", data=asdict(report))
            logger.info("Report published to RabbitMQ")

        return 0

    parser.error("Unsupported command")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
