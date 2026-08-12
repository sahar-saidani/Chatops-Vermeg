from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


# ============================================================
# Agent parameters
# ============================================================

AgentParams = dict[str, str]

StepBuilder = Callable[[AgentParams], list[str]]


# ============================================================
# Agent step
# ============================================================

@dataclass(frozen=True)
class AgentStep:
    """
    One subprocess invocation.

    An agent can contain one or multiple steps.
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
        Optional explicit Python interpreter.

        If None, the interpreter is automatically resolved from
        the agent's own .venv.

    Supported layouts:

        agent/
            .venv/
                Scripts/python.exe

        agent/
            .venv/
                bin/python

        agent/
            subdirectory/
                .venv/
                    Scripts/python.exe

        agent/
            subdirectory/
                .venv/
                    bin/python
    """

    key: str
    working_dir: str
    steps: list[AgentStep]
    description: str = ""
    python_executable: str | None = None


# ============================================================
# Python interpreter resolution
# ============================================================

def resolve_agent_python(
    working_dir: str,
    base_dir: Path | None = None,
) -> str:
    """
    Resolve the Python interpreter belonging to an agent.

    Supports:

        agent/.venv/...
        agent/subdirectory/.venv/...

    Example:

        working_dir = "log-agent/logs-agent"

    It checks:

        log-agent/logs-agent/.venv/Scripts/python.exe
        log-agent/logs-agent/.venv/bin/python

    Then:

        log-agent/.venv/Scripts/python.exe
        log-agent/.venv/bin/python

    Then:

        repository-root/.venv/...

    Finally falls back to sys.executable.
    """

    working_path = (
        Path(base_dir) / working_dir
        if base_dir is not None
        else Path(working_dir)
    )

    candidate_roots = [
        working_path,
        working_path.parent,
        working_path.parent.parent,
    ]

    unique_roots: list[Path] = []

    for path in candidate_roots:
        resolved = path.resolve()

        if resolved not in unique_roots:
            unique_roots.append(resolved)

    # --------------------------------------------------------
    # Windows
    # --------------------------------------------------------

    if sys.platform.startswith("win"):

        for agent_root in unique_roots:

            python_path = (
                agent_root
                / ".venv"
                / "Scripts"
                / "python.exe"
            )

            if python_path.is_file():
                return str(python_path)

    # --------------------------------------------------------
    # Linux / Unix
    # --------------------------------------------------------

    else:

        for agent_root in unique_roots:

            python_path = (
                agent_root
                / ".venv"
                / "bin"
                / "python"
            )

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
    """
    Build the steps for the Git agent.

    Git Agent CLI supports:

        main.py analyze --repo <repo>
        main.py analyze --path <path>
        main.py analyze --branch <branch>

    The branch is NOT hardcoded here.

    It must come from the tenant/machine configuration
    and be present in params["branch"].
    """

    def build(params: AgentParams) -> list[str]:

        args = [
            "main.py",
            "analyze",
        ]

        # ----------------------------------------------------
        # Repository
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # Branch
        # ----------------------------------------------------

        branch = params.get("branch")

        if branch:
            args += [
                "--branch",
                branch,
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
    """
    Build the steps for the Jenkins agent.
    """

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
    """
    Build the steps for the Installation agent.

    The Installation Agent scans the real machine
    configuration directory.

    The directory can be supplied through:

        <MACHINE>_INSTALLATION_CONFIG_DIR

    Example:

        NNBE_CENTOS_01_INSTALLATION_CONFIG_DIR=
        /home/sahar/Chatops-Vermeg/installation-agent/config
    """

    def build(params: AgentParams) -> list[str]:

        args = [
            "main.py",
            "--scan",
        ]

        # ----------------------------------------------------
        # Machine reference
        # ----------------------------------------------------

        machine_reference = params.get("machine_reference")

        # ----------------------------------------------------
        # Explicit config directory
        # ----------------------------------------------------

        config_dir = params.get("config_dir")

        # ----------------------------------------------------
        # Machine-specific environment variable
        # ----------------------------------------------------

        if not config_dir and machine_reference:

            env_prefix = (
                machine_reference
                .strip()
                .upper()
                .replace("-", "_")
            )

            config_dir = os.getenv(
                f"{env_prefix}_INSTALLATION_CONFIG_DIR"
            )

        # ----------------------------------------------------
        # Config directory
        # ----------------------------------------------------

        if config_dir:

            args += [
                "--config-dir",
                config_dir,
            ]

        # ----------------------------------------------------
        # Operating system
        # ----------------------------------------------------

        operating_system = params.get("operating_system")

        if operating_system:

            args += [
                "--os",
                operating_system,
            ]

        return args

    return [
        AgentStep(
            build=build,
            description="Scan and analyze real installation/configuration files",
        )
    ]


# ============================================================
# Infrastructure Agent
# ============================================================

def _infrastructure_steps() -> list[AgentStep]:
    """
    Build the steps for the Infrastructure Agent.

    Infrastructure main.py accepts:

        --collect

    It does NOT accept:

        --os

    The operating system is already determined by the
    orchestrator/machine routing.
    """

    def build(params: AgentParams) -> list[str]:

        return [
            "main.py",
            "--collect",
        ]

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
    """
    Build the steps for the Log Agent.

    The Log Agent is executed as a bounded subprocess.

    LOG_AGENT_DURATION_SECONDS must remain lower than
    AGENT_SUBPROCESS_TIMEOUT_SECONDS.
    """

    def build(params: AgentParams) -> list[str]:

        duration = params.get("duration") or os.getenv(
            "LOG_AGENT_DURATION_SECONDS",
            "30",
        )

        return [
            "main.py",
            "--duration",
            str(duration),
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

    # --------------------------------------------------------
    # Git
    # --------------------------------------------------------

    "git": AgentDefinition(
        key="git",
        working_dir="git-agent",
        steps=_git_steps(),
        description=(
            "Repository mining and software analytics "
            "(commits, branches, PRs)"
        ),
    ),

    # --------------------------------------------------------
    # Jenkins
    # --------------------------------------------------------

    "jenkins": AgentDefinition(
        key="jenkins",
        working_dir="jenkins-agent",
        steps=_jenkins_steps(),
        description=(
            "Jenkins CI/CD job and build analysis"
        ),
    ),

    # --------------------------------------------------------
    # Jira
    # --------------------------------------------------------

    "jira": AgentDefinition(
        key="jira",
        working_dir="jira-agent",
        steps=_jira_steps(),
        description=(
            "Jira issues, sprints and project analytics"
        ),
    ),

    # --------------------------------------------------------
    # Installation
    # --------------------------------------------------------

    "installation": AgentDefinition(
        key="installation",
        working_dir="installation-agent",
        steps=_installation_steps(),
        description=(
            "Deployment/installation script and "
            "configuration discovery"
        ),
    ),

    # --------------------------------------------------------
    # Infrastructure
    # --------------------------------------------------------

    "infrastructure": AgentDefinition(
        key="infrastructure",
        working_dir="infrastructure-Agent/app",
        steps=_infrastructure_steps(),
        description=(
            "Infrastructure health metrics "
            "(CPU, memory, disk, network, services)"
        ),
    ),

    # --------------------------------------------------------
    # Log
    # --------------------------------------------------------

    "log": AgentDefinition(
        key="log",
        working_dir="log-agent/logs-agent",
        steps=_log_steps(),
        description=(
            "Log collection and publishing"
        ),
    ),
}


# ============================================================
# Agent lookup
# ============================================================

def get_agent_definition(
    agent_key: str,
    agents_root_dir: Path | None = None,
) -> AgentDefinition:
    """
    Return an agent definition with its Python interpreter
    automatically resolved.

    agents_root_dir:
        Directory containing all agents.

    This should normally be Settings.agents_root_dir.
    """

    try:

        definition = AGENT_REGISTRY[agent_key]

    except KeyError as exc:

        known = ", ".join(
            sorted(AGENT_REGISTRY)
        )

        raise KeyError(
            f"Unknown agent key '{agent_key}'. "
            f"Known agents: {known}"
        ) from exc

    # --------------------------------------------------------
    # Resolve agent-specific virtual environment
    # --------------------------------------------------------

    if definition.python_executable is None:

        python_executable = resolve_agent_python(
            definition.working_dir,
            base_dir=agents_root_dir,
        )

        definition = AgentDefinition(
            key=definition.key,
            working_dir=definition.working_dir,
            steps=definition.steps,
            description=definition.description,
            python_executable=python_executable,
        )

    return definition