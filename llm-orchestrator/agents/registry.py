from __future__ import annotations
import sys
from dataclasses import dataclass, field
from typing import Callable

# Params the intent classifier may extract from a user request and pass down
# to an agent's command builder (e.g. {"environment": "DEV", "repo": "owner/name"}).
AgentParams = dict[str, str]

StepBuilder = Callable[[AgentParams], list[str]]


@dataclass(frozen=True)
class AgentStep:
    """One subprocess invocation. Some agents need more than one step
    (jira-agent must 'collect' before it can 'report')."""

    build: StepBuilder
    description: str


@dataclass(frozen=True)
class AgentDefinition:
    """Describes how to launch an EXISTING collection agent as-is.

    ``working_dir`` is relative to ``Settings.agents_root_dir``.
    ``python_executable`` defaults to the interpreter running the
    orchestrator; override per-agent if a dedicated venv is used in
    production (e.g. via a wrapper script on PATH).
    """

    key: str
    working_dir: str
    steps: list[AgentStep]
    python_executable: str = "python"
    description: str = ""


def _git_steps() -> list[AgentStep]:
    def build(params: AgentParams) -> list[str]:
        args = ["main.py", "analyze"]
        if params.get("repo"):
            args += ["--repo", params["repo"]]
        elif params.get("path"):
            args += ["--path", params["path"]]
        return args

    return [AgentStep(build=build, description="Analyze repository and publish report")]


def _jenkins_steps() -> list[AgentStep]:
    def build(params: AgentParams) -> list[str]:
        args = ["main.py", "analyze"]
        if params.get("repo_path"):
            args += ["--repo-path", params["repo_path"]]
        return args

    return [AgentStep(build=build, description="Analyze Jenkins CI/CD status and publish report")]


def _jira_steps() -> list[AgentStep]:
    # jira-agent's CLI requires 'collect' to run before 'report' can load a snapshot.
    return [
        AgentStep(build=lambda params: ["main.py", "collect"], description="Collect Jira snapshot"),
        AgentStep(
            build=lambda params: ["main.py", "report"],
            description="Analyze snapshot, generate report and publish",
        ),
    ]


def _installation_steps() -> list[AgentStep]:
    def build(params: AgentParams) -> list[str]:
        args = ["cli.py", "analyze"]
        if params.get("path"):
            args += ["--path", params["path"]]
        return args

    return [AgentStep(build=build, description="Discover and analyze installation metadata")]


def _infrastructure_steps() -> list[AgentStep]:
    return [
        AgentStep(build=lambda params: ["main.py", "--collect"], description="Collect infrastructure health snapshot")
    ]


def _log_steps() -> list[AgentStep]:
    def build(params: AgentParams) -> list[str]:
        return ["main.py", "--mode", params.get("mode", "prometheus")]

    return [AgentStep(build=build, description="Collect and publish log/metric events")]


AGENT_REGISTRY: dict[str, AgentDefinition] = {
    "git": AgentDefinition(
        key="git",
        working_dir="git-agent",
        steps=_git_steps(),
        description="Repository mining and software analytics (commits, branches, PRs)",
    ),
    "jenkins": AgentDefinition(
        key="jenkins",
        working_dir="jenkins-agent",
        steps=_jenkins_steps(),
        description="Jenkins CI/CD job and build analysis",
    ),
    "jira": AgentDefinition(
        key="jira",
        working_dir="jira-agent",
        steps=_jira_steps(),
        description="Jira issues, sprints and project analytics",
    ),
    "installation": AgentDefinition(
        key="installation",
        working_dir="installation-agent",
        steps=_installation_steps(),
        description="Deployment/installation script and configuration discovery",
    ),
    "infrastructure": AgentDefinition(
        key="infrastructure",
        working_dir="infrastructure-Agent/app",
        steps=_infrastructure_steps(),
        description="Infrastructure health metrics (CPU, memory, disk, network, services)",
    ),
    "log": AgentDefinition(
        key="log",
        working_dir="log-agent/logs-agent",
        steps=_log_steps(),
        description="Log and Prometheus metric collection",
    ),
}


def get_agent_definition(agent_key: str) -> AgentDefinition:
    try:
        return AGENT_REGISTRY[agent_key]
    except KeyError as exc:
        known = ", ".join(sorted(AGENT_REGISTRY))
        raise KeyError(f"Unknown agent key '{agent_key}'. Known agents: {known}") from exc
