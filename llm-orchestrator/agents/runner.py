from __future__ import annotations

import logging
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

    Each agent is executed as an isolated subprocess.
    """

    def __init__(self, settings: Settings):
        self._settings = settings


    def run(
        self,
        agent_key: str,
        params: AgentParams | None = None
    ) -> AgentExecutionResult:

        params = params or {}

        definition = get_agent_definition(agent_key)

        working_dir = self._resolve_working_dir(definition)

        launched_at = datetime.now(timezone.utc)

        stdout_parts: list[str] = []
        stderr_parts: list[str] = []

        steps_run = 0


        for step in definition.steps:

            args = step.build(params)

            command = [
                definition.python_executable,
                *args
            ]


            logger.info(
                "Launching agent '%s' step '%s': %s (cwd=%s)",
                agent_key,
                step.description,
                " ".join(command),
                working_dir,
            )


            try:

                completed = subprocess.run(
                    command,
                    cwd=str(working_dir),

                    # Important:
                    # capture both stdout and stderr
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,

                    text=True,

                    timeout=self._settings.agent_subprocess_timeout_seconds,

                    check=False,
                )


            except subprocess.TimeoutExpired as exc:

                logger.exception(
                    "Agent '%s' timeout",
                    agent_key
                )

                stderr_parts.append(
                    f"Timeout: {str(exc)}"
                )


                return self._failure_result(
                    agent_key,
                    launched_at,
                    steps_run,
                    stdout_parts,
                    stderr_parts
                )


            except Exception as exc:

                logger.exception(
                    "Unexpected error launching agent '%s'",
                    agent_key
                )

                stderr_parts.append(
                    repr(exc)
                )


                return self._failure_result(
                    agent_key,
                    launched_at,
                    steps_run,
                    stdout_parts,
                    stderr_parts
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
                    completed.stdout
                )

                logger.error(
                    "STDERR:\n%s",
                    completed.stderr
                )


                return self._failure_result(
                    agent_key,
                    launched_at,
                    steps_run,
                    stdout_parts,
                    stderr_parts
                )


        return AgentExecutionResult(
            agent_key=agent_key,
            launched_at=launched_at,
            success=True,
            steps_run=steps_run,
            stdout_tail=self._tail(stdout_parts),
            stderr_tail=self._tail(stderr_parts),
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
        definition: AgentDefinition
    ) -> Path:

        working_dir = (
            self._settings.agents_root_dir
            /
            definition.working_dir
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
        max_chars: int = 4000
    ) -> str:

        joined = "\n".join(
            p for p in parts if p
        )

        return joined[-max_chars:]