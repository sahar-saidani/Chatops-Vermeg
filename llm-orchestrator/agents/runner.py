
from __future__ import annotations

import logging
import os
import shlex
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from config import Settings
from .registry import AgentDefinition, AgentParams, get_agent_definition


logger = logging.getLogger(__name__)


@dataclass
class AgentExecutionResult:
    agent_key: str
    launched_at: datetime
    success: bool
    steps_run: int
    stdout_tail: str
    stderr_tail: str


class AgentRunner:
    """
    Execute existing agents through their CLI entrypoints.

    Agents can be executed:
      - locally, when no machine_reference is provided
      - locally, when machine_reference == "windows-local"
      - remotely on Linux through SSH
      - remotely on Windows through SSH

    The target machine is selected using:
        machine_reference
        operating_system
    """

    def __init__(self, settings: Settings):
        self._settings = settings

    def run(
        self,
        agent_key: str,
        params: AgentParams | None = None,
    ) -> AgentExecutionResult:

        params = params or {}

        definition = get_agent_definition(agent_key)

        machine_reference = params.get("machine_reference")

        operating_system = (
            params.get("operating_system")
            or params.get("OPERATING_SYSTEM")
        )

        launched_at = datetime.now(timezone.utc)

        stdout_parts: list[str] = []
        stderr_parts: list[str] = []

        steps_run = 0

        for step in definition.steps:

            args = step.build(params)

            try:
                command, working_dir = self._build_execution_command(
                    definition=definition,
                    args=args,
                    machine_reference=machine_reference,
                    operating_system=operating_system,
                )

            except Exception as exc:
                logger.exception(
                    "Failed to build command for agent '%s'",
                    agent_key,
                )

                stderr_parts.append(repr(exc))

                return self._failure_result(
                    agent_key,
                    launched_at,
                    steps_run,
                    stdout_parts,
                    stderr_parts,
                )

            logger.info(
                "Launching agent '%s' step '%s': %s "
                "(cwd=%s, machine=%s, os=%s)",
                agent_key,
                step.description,
                " ".join(command),
                working_dir,
                machine_reference or "local",
                operating_system or "unknown",
            )

            try:
                completed = subprocess.run(
                    command,
                    cwd=str(working_dir) if working_dir else None,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=self._settings.agent_subprocess_timeout_seconds,
                    check=False,
                )

            except subprocess.TimeoutExpired as exc:
                logger.exception(
                    "Agent '%s' timeout",
                    agent_key,
                )

                stderr_parts.append(
                    f"Timeout: {str(exc)}"
                )

                return self._failure_result(
                    agent_key,
                    launched_at,
                    steps_run,
                    stdout_parts,
                    stderr_parts,
                )

            except Exception as exc:
                logger.exception(
                    "Unexpected error launching agent '%s'",
                    agent_key,
                )

                stderr_parts.append(
                    repr(exc)
                )

                return self._failure_result(
                    agent_key,
                    launched_at,
                    steps_run,
                    stdout_parts,
                    stderr_parts,
                )

            stdout_parts.append(
                completed.stdout or ""
            )

            stderr_parts.append(
                completed.stderr or ""
            )

            steps_run += 1

            if completed.returncode != 0:
                logger.error(
                    "Agent '%s' step '%s' failed with exit code %s",
                    agent_key,
                    step.description,
                    completed.returncode,
                )

                logger.error(
                    "STDOUT:\n%s",
                    completed.stdout,
                )

                logger.error(
                    "STDERR:\n%s",
                    completed.stderr,
                )

                return self._failure_result(
                    agent_key,
                    launched_at,
                    steps_run,
                    stdout_parts,
                    stderr_parts,
                )

        return AgentExecutionResult(
            agent_key=agent_key,
            launched_at=launched_at,
            success=True,
            steps_run=steps_run,
            stdout_tail=self._tail(stdout_parts),
            stderr_tail=self._tail(stderr_parts),
        )

    def _build_execution_command(
        self,
        definition: AgentDefinition,
        args: list[str],
        machine_reference: str | None,
        operating_system: str | None,
    ) -> tuple[list[str], Path | None]:

        # ============================================================
        # 1. Local execution
        # ============================================================
        #
        # Local execution happens in two cases:
        #
        #   - no machine_reference
        #   - machine_reference == "windows-local"
        #
        # This is important because a Windows local machine must NOT
        # be treated as a remote Windows machine requiring SSH.
        #

        if (
            not machine_reference
            or machine_reference.strip().lower() == "windows-local"
        ):

            working_dir = self._resolve_working_dir(definition)

            command = [
                definition.python_executable,
                *args,
            ]

            logger.debug(
                "Using local execution for agent '%s' "
                "(machine_reference=%s, operating_system=%s)",
                definition.key,
                machine_reference or "local",
                operating_system or "unknown",
            )

            return command, working_dir

        # ============================================================
        # 2. Normalize operating system
        # ============================================================

        normalized_os = (
            operating_system.strip().upper()
            if operating_system
            else None
        )

        if normalized_os not in {"LINUX", "WINDOWS"}:
            raise RuntimeError(
                f"Unsupported or missing operating_system "
                f"for machine '{machine_reference}'. "
                f"Expected LINUX or WINDOWS, got "
                f"{operating_system!r}"
            )

        # ============================================================
        # 3. Resolve remote machine configuration from environment
        # ============================================================

        env_prefix = (
            machine_reference
            .upper()
            .replace("-", "_")
        )

        host = os.getenv(
            f"{env_prefix}_HOST"
        )

        user = os.getenv(
            f"{env_prefix}_USER"
        )

        agent_dir = os.getenv(
            f"{env_prefix}_AGENT_DIR"
        )

        python = os.getenv(
            f"{env_prefix}_PYTHON",
            "python",
        )

        ssh_port = os.getenv(
            f"{env_prefix}_SSH_PORT",
            "22",
        )

        if not host:
            raise RuntimeError(
                f"Missing {env_prefix}_HOST"
            )

        if not user:
            raise RuntimeError(
                f"Missing {env_prefix}_USER"
            )

        if not agent_dir:
            raise RuntimeError(
                f"Missing {env_prefix}_AGENT_DIR"
            )

        # ============================================================
        # 4. Build remote command
        # ============================================================

        if normalized_os == "LINUX":

            remote_command = self._build_linux_remote_command(
                agent_dir=agent_dir,
                python=python,
                args=args,
            )

        else:

            remote_command = self._build_windows_remote_command(
                agent_dir=agent_dir,
                python=python,
                args=args,
            )

        # ============================================================
        # 5. SSH command
        # ============================================================

        command = [
            "ssh",
            "-p",
            ssh_port,
            f"{user}@{host}",
            remote_command,
        ]

        return command, None

    @staticmethod
    def _build_linux_remote_command(
        agent_dir: str,
        python: str,
        args: list[str],
    ) -> str:
        """
        Build command executed on a Linux machine.

        Example:

            cd /opt/chatops/infrastructure-Agent/app &&
            python main.py --collect
        """

        quoted_args = " ".join(
            shlex.quote(str(arg))
            for arg in args
        )

        return (
            f"cd {shlex.quote(agent_dir)} && "
            f"{shlex.quote(python)} "
            f"{quoted_args}"
        )

    @staticmethod
    def _build_windows_remote_command(
        agent_dir: str,
        python: str,
        args: list[str],
    ) -> str:
        """
        Build command executed on a remote Windows machine through SSH.

        Example:

            cd /d C:\\Chatops-Vermeg\\infrastructure-Agent\\app &&
            python main.py --collect
        """

        normalized_agent_dir = agent_dir.replace("/", "\\")

        escaped_agent_dir = normalized_agent_dir.replace(
            '"',
            '\\"',
        )

        command_parts: list[str] = []

        for arg in args:
            value = str(arg)

            if any(
                char in value
                for char in " &()[]{}^=;!'+,`~"
            ):
                value = (
                    f'"{value.replace(chr(34), chr(92) + chr(34))}"'
                )

            command_parts.append(value)

        quoted_args = " ".join(command_parts)

        return (
            f'cd /d "{escaped_agent_dir}" && '
            f'"{python}" {quoted_args}'
        )

    def _failure_result(
        self,
        agent_key: str,
        launched_at: datetime,
        steps_run: int,
        stdout_parts: list[str],
        stderr_parts: list[str],
    ) -> AgentExecutionResult:

        return AgentExecutionResult(
            agent_key=agent_key,
            launched_at=launched_at,
            success=False,
            steps_run=steps_run,
            stdout_tail=self._tail(stdout_parts),
            stderr_tail=self._tail(stderr_parts),
        )

    def _resolve_working_dir(
        self,
        definition: AgentDefinition,
    ) -> Path:

        working_dir = (
            self._settings.agents_root_dir
            / definition.working_dir
        ).resolve()

        if not working_dir.exists():
            raise FileNotFoundError(
                f"""
Working directory for agent '{definition.key}' not found:

{working_dir}

Check AGENTS_ROOT_DIR configuration.
"""
            )

        return working_dir

    @staticmethod
    def _tail(
        parts: list[str],
        max_chars: int = 4000,
    ) -> str:

        joined = "\n".join(
            p for p in parts if p
        )

        return joined[-max_chars:]

