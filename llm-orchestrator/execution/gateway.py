from __future__ import annotations

from abc import ABC, abstractmethod

from agents.runner import AgentExecutionResult, AgentRunner

from .models import AgentCommand, AgentResult, ExecutionPlan


class AgentExecutionGateway(ABC):
    @abstractmethod
    def execute(self, plan: ExecutionPlan) -> list[AgentResult]:
        raise NotImplementedError


class SubprocessAgentExecutionGateway(AgentExecutionGateway):
    """Executes the existing agents locally as a transitional backend."""

    def __init__(self, runner: AgentRunner):
        self._runner = runner

    def execute(self, plan: ExecutionPlan) -> list[AgentResult]:
        results: list[AgentResult] = []
        for agent_key in plan.agent_keys:
            command = AgentCommand.from_plan(plan, agent_key)
            execution = self._runner.run(command.agent, dict(command.parameters))
            results.append(self._to_result(command, execution))
        return results

    @staticmethod
    def _to_result(command: AgentCommand, execution: AgentExecutionResult) -> AgentResult:
        status = "SUCCESS" if execution.success else "FAILED"
        payload = {
            "stdout_tail": execution.stdout_tail,
            "stderr_tail": execution.stderr_tail,
            "steps_run": execution.steps_run,
            "launched_at": execution.launched_at.isoformat(),
        }
        error = None if execution.success else execution.stderr_tail or "Agent execution failed"
        return AgentResult(
            task_id=command.task_id,
            tenant=command.tenant,
            machine_reference=command.machine_reference,
            agent=command.agent,
            status=status,
            data=payload,
            error=error,
        )