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

    The function supports both common layouts:

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

    If no agent-specific virtual environment exists,
    sys.executable is used as fallback.

    base_dir:
        Directory that `working_dir` is relative to (normally
        Settings.agents_root_dir, i.e. the repository root).

        Without it, `working_dir` would be resolved relative to the
        current process working directory instead, which silently
        breaks whenever the orchestrator isn't launched from a
        directory that happens to contain the agent folder next to
        it (e.g. running `main.py` from within `llm-orchestrator/`,
        where "log-agent/logs-agent" doesn't exist) - falling back to
        sys.executable and raising ModuleNotFoundError for packages
        only installed in the agent's own venv.
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

    # Remove duplicates while preserving order.
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
            "main.py",
            "--scan",
        ]

        # Per-machine override for the directory to scan, following the
        # same {MACHINE}_{AGENT_KEY}_... convention runner.py already uses
        # for remote AGENT_DIR/PYTHON (e.g. NNBE_CENTOS_01_INSTALLATION_
        # CONFIG_DIR=/home/.../installation-agent/config). Falls back to
        # the agent's own config/ folder (its default) when unset, so a
        # bare `main.py --scan` still works standalone.
        machine_reference = params.get("machine_reference")

        config_dir = params.get("config_dir")

        if not config_dir and machine_reference:
            env_prefix = machine_reference.strip().upper().replace("-", "_")
            config_dir = os.getenv(f"{env_prefix}_INSTALLATION_CONFIG_DIR")

        if config_dir:
            args += [
                "--config-dir",
                config_dir,
            ]

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
    """Build the steps for the Infrastructure agent."""

    def build(params: AgentParams) -> list[str]:

        args = [
            "main.py",
            "--collect",
        ]

        # IMPORTANT:
        # Infrastructure main.py accepts --collect.
        # It does NOT accept --os.
        #
        # The operating system is already determined by
        # the orchestrator / machine routing.

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

        # The Log agent is launched as a bounded subprocess by the
        # orchestrator (AgentRunner), which itself enforces
        # AGENT_SUBPROCESS_TIMEOUT_SECONDS. --duration must therefore
        # stay comfortably below that timeout, or the subprocess gets
        # killed via subprocess.TimeoutExpired before it can flush its
        # summary/events. LOG_AGENT_DURATION_SECONDS lets this be tuned
        # per-deployment without touching code.
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
            "Log collection and publishing to RabbitMQ"
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
        Directory that every agent's `working_dir` is relative to
        (Settings.agents_root_dir). Pass this whenever it's
        available so the agent-specific .venv can be found
        regardless of the orchestrator's current working directory.
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
    # Resolve agent-specific virtual environment.
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