from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

# ============================================================
# Agent parameters
# ============================================================
# Parameters extracted by the intent classifier and passed
# to an agent's command builder.
#
# Examples:
# {
#     "environment": "DEV",
#     "repo": "owner/name",
#     "operating_system": "WINDOWS",
# }
AgentParams = dict[str, str]

StepBuilder = Callable[[AgentParams], list[str]]


# ============================================================
# Agent step
# ============================================================
@dataclass(frozen=True)
class AgentStep:
    """
    One subprocess invocation.

    Some agents require multiple steps.
    Example:
        jira-agent -> collect -> report
    """

    build: StepBuilder
    description: str


# ============================================================
# Agent definition
# ============================================================
@dataclass(frozen=True)
class AgentDefinition:
    """
    Describes how to launch an existing agent.

    working_dir:
        Directory relative to Settings.agents_root_dir.

    python_executable:
        Python interpreter used to execute the agent.

        If None, the interpreter is automatically resolved from
        the agent's own .venv.

        Windows:
            <agent-root>/.venv/Scripts/python.exe

        Linux:
            <agent-root>/.venv/bin/python

        If no agent-specific .venv exists, sys.executable is used.
    """

    key: str
    working_dir: str
    steps: list[AgentStep]
    description: str = ""
    python_executable: str | None = None


# ============================================================
# Python interpreter resolution
# ============================================================
def resolve_agent_python(working_dir: str) -> str:
    """
    Resolve the Python interpreter for an agent.

    Examples:
        infrastructure-Agent/app
        git-agent
        jenkins-agent
        jira-agent

    For infrastructure-Agent/app, the function checks:
        infrastructure-Agent/app/.venv/...
        infrastructure-Agent/.venv/...

    The second location is the expected one for the project.

    If no dedicated .venv is found, the Python interpreter
    running the orchestrator is used as fallback.
    """
    working_path = Path(working_dir)

    # The agent's .venv can be either:
    #
    #   agent/.venv
    #
    # or, for agents whose working directory is a subdirectory:
    #
    #   agent/app
    #   agent/.venv
    #
    candidate_roots = [
        working_path,
        working_path.parent,
    ]

    # Remove duplicates while preserving order.
    candidate_roots = list(
        dict.fromkeys(
            path.resolve()
            for path in candidate_roots
        )
    )

    # --------------------------------------------------------
    # Windows
    # --------------------------------------------------------
    if sys.platform.startswith("win"):
        for agent_root in candidate_roots:
            python_path = agent_root / ".venv" / "Scripts" / "python.exe"
            if python_path.is_file():
                return str(python_path)

    # --------------------------------------------------------
    # Linux / Unix
    # --------------------------------------------------------
    else:
        for agent_root in candidate_roots:
            python_path = agent_root / ".venv" / "bin" / "python"
            if python_path.is_file():
                return str(python_path)

    # --------------------------------------------------------
    # Fallback
    # --------------------------------------------------------
    return sys.executable


# ============================================================
# Git Agent
# ============================================================
def _git_steps() -> list[AgentStep]:
    """Build the steps for the Git agent."""

    def build(params: AgentParams) -> list[str]:
        args = [
            "main.py",
            "analyze",
        ]

        if params.get("repo"):
            args += [
                "--repo",
                params["repo"],
            ]
        elif params.get("path"):
            args += [
                "--path",
                params["path"],
            ]

        if params.get("branch"):
            args += [
                "--branch",
                params["branch"],
            ]

        return args

    return [
        AgentStep(
            build=build,
            description="Analyze repository and publish report",
        )
    ]


# ============================================================
# Jenkins Agent
# ============================================================
def _jenkins_steps() -> list[AgentStep]:
    """Build the steps for the Jenkins agent."""

    def build(params: AgentParams) -> list[str]:
        args = [
            "main.py",
            "analyze",
        ]

        if params.get("repo_path"):
            args += [
                "--repo-path",
                params["repo_path"],
            ]

        return args

    return [
        AgentStep(
            build=build,
            description="Analyze Jenkins CI/CD status and publish report",
        )
    ]


# ============================================================
# Jira Agent
# ============================================================
def _jira_steps() -> list[AgentStep]:
    """
    Jira requires collection before reporting.
    """

    return [
        AgentStep(
            build=lambda params: [
                "main.py",
                "collect",
            ],
            description="Collect Jira snapshot",
        ),
        AgentStep(
            build=lambda params: [
                "main.py",
                "report",
            ],
            description="Analyze snapshot, generate report and publish",
        ),
    ]


# ============================================================
# Installation Agent
# ============================================================
def _installation_steps() -> list[AgentStep]:
    """Build the steps for the Installation agent."""

    def build(params: AgentParams) -> list[str]:
        args = [
            "cli.py",
            "analyze",
        ]

        if params.get("path"):
            args += [
                "--path",
                params["path"],
            ]

        return args

    return [
        AgentStep(
            build=build,
            description="Discover and analyze installation metadata",
        )
    ]


# ============================================================
# Infrastructure Agent
# ============================================================
def _infrastructure_steps() -> list[AgentStep]:
    """Build the steps for the Infrastructure agent."""

    def build(params: AgentParams) -> list[str]:
        args = [
            "main.py",
            "--collect",
        ]

        operating_system = (
            params.get("operating_system")
            or params.get("OPERATING_SYSTEM")
        )

        if operating_system:
            args += [
                "--os",
                operating_system.strip().upper(),
            ]

        return args

    return [
        AgentStep(
            build=build,
            description="Collect infrastructure health snapshot",
        )
    ]


# ============================================================
# Log Agent
# ============================================================
def _log_steps() -> list[AgentStep]:
    """Build the steps for the Log agent."""

    def build(params: AgentParams) -> list[str]:
        # Default duration is limited so that the log agent
        # terminates and releases the orchestrator.
        duration = params.get(
            "duration",
            "500",
        )

        return [
            "main.py",
            "--duration",
            duration,
        ]

    return [
        AgentStep(
            build=build,
            description="Collect and publish log events",
        )
    ]


# ============================================================
# Agent Registry
# ============================================================
AGENT_REGISTRY: dict[str, AgentDefinition] = {
    "git": AgentDefinition(
        key="git",
        working_dir="git-agent",
        steps=_git_steps(),
        description=(
            "Repository mining and software analytics "
            "(commits, branches, PRs)"
        ),
    ),
    "jenkins": AgentDefinition(
        key="jenkins",
        working_dir="jenkins-agent",
        steps=_jenkins_steps(),
        description=(
            "Jenkins CI/CD job and build analysis"
        ),
    ),
    "jira": AgentDefinition(
        key="jira",
        working_dir="jira-agent",
        steps=_jira_steps(),
        description=(
            "Jira issues, sprints and project analytics"
        ),
    ),
    "installation": AgentDefinition(
        key="installation",
        working_dir="installation-agent",
        steps=_installation_steps(),
        description=(
            "Deployment/installation script and "
            "configuration discovery"
        ),
    ),
    "infrastructure": AgentDefinition(
        key="infrastructure",
        working_dir="infrastructure-Agent/app",
        steps=_infrastructure_steps(),
        description=(
            "Infrastructure health metrics "
            "(CPU, memory, disk, network, services)"
        ),
    ),
    "log": AgentDefinition(
        key="log",
        working_dir="log-agent/logs-agent",
        steps=_log_steps(),
        description=(
            "Log collection and publishing to RabbitMQ"
        ),
    ),
}


# ============================================================
# Agent lookup
# ============================================================
def get_agent_definition(agent_key: str) -> AgentDefinition:
    """
    Return an agent definition with its Python interpreter
    automatically resolved.
    """
    try:
        definition = AGENT_REGISTRY[agent_key]
    except KeyError as exc:
        known = ", ".join(sorted(AGENT_REGISTRY))
        raise KeyError(
            f"Unknown agent key '{agent_key}'. "
            f"Known agents: {known}"
        ) from exc

    # --------------------------------------------------------
    # Resolve agent-specific virtual environment.
    # --------------------------------------------------------
    if definition.python_executable is None:
        python_executable = resolve_agent_python(definition.working_dir)

        definition = AgentDefinition(
            key=definition.key,
            working_dir=definition.working_dir,
            steps=definition.steps,
            description=definition.description,
            python_executable=python_executable,
        )

    return definition