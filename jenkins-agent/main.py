"""CLI entry point for Jenkins agent."""

from __future__ import annotations

import argparse
from pathlib import Path

from agent.jenkins_agent import build_agent_from_env
from agent.machine_identity import MachineIdentity
from message_sender import MessageSender
from utils.logger import setup_logger

import agent.machine_identity

print(agent.machine_identity.__file__)
print(MachineIdentity)

def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Jenkins CI/CD analysis agent")
    parser.add_argument(
        "command",
        nargs="?",
        default="analyze",
        choices=["analyze", "report"],
        help="Command to run",
    )
    parser.add_argument(
        "--repo-path",
        default="ToDoList",
        help="Path to target source repository",
    )
    parser.add_argument(
        "--report-path",
        default="reports/jenkins_report.json",
        help="Path to generated report JSON",
    )
    return parser.parse_args()


def main() -> None:
    """Execute Jenkins analysis workflow."""
    args = parse_args()
    logger = setup_logger(__name__)

    import os

    identity = MachineIdentity.from_env()

    logger.info(
        "Starting jenkins-agent | tenant=%s | environment=%s | machine=%s | rabbitmq=%s",
        identity.tenant_name,
        identity.environment_name,
        identity.machine_reference,
        os.getenv("RABBITMQ_URL", "disabled"),
        )

    report_path = Path(args.report_path)
    repo_path = Path(args.repo_path)

    agent = build_agent_from_env(report_path=report_path)
    report = agent.analyze(repo_path=repo_path)

    if args.command in {"analyze", "report"}:
        agent.write_report(report)

    rabbitmq_url = os.getenv("RABBITMQ_URL")
    message = MessageSender(rabbitmq_url=rabbitmq_url).send(report.model_dump(mode="json"), identity=identity)
    logger.info("Message successfully published.")


if __name__ == "__main__":
    main()
