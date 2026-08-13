from __future__ import annotations

from dataclasses import dataclass, field

from .models import AgentResult, ExecutionPlan


@dataclass
class ResultBundle:
    plan: ExecutionPlan
    results: list[AgentResult] = field(default_factory=list)

    @property
    def is_complete(self) -> bool:
        completed_agents = {result.agent for result in self.results if result.status == "SUCCESS"}
        return completed_agents.issuperset(self.plan.agent_keys)


class ResultAggregator:
    def __init__(self) -> None:
        self._bundles: dict[str, ResultBundle] = {}

    def register(self, plan: ExecutionPlan) -> None:
        self._bundles[plan.task_id] = ResultBundle(plan=plan)

    def record(self, result: AgentResult) -> None:
        bundle = self._bundles.get(result.task_id)
        if bundle is None:
            raise KeyError(f"Unknown task_id {result.task_id!r}")
        bundle.results.append(result)

    def agent_statuses(self, task_id: str) -> list[dict]:
        """
        Per-agent outcome for one task, for reporting back to the caller.

        Every requested agent appears, including ones that produced no result
        at all. Without this the API could only say "here is the answer", and a
        client had no way to tell an agent that crashed from an agent that ran
        and legitimately found nothing -- the two are different answers and
        must not be rendered alike.
        """
        bundle = self._bundles.get(task_id)
        if bundle is None:
            return []

        by_agent = {result.agent: result for result in bundle.results}
        statuses = []
        for agent_key in bundle.plan.agent_keys:
            result = by_agent.get(agent_key)
            if result is None:
                # Planned but never reported back: distinct from FAILED, since
                # the agent may simply not have been reached.
                statuses.append({"agent": agent_key, "status": "NO_RESULT", "error": None})
            else:
                statuses.append(
                    {"agent": agent_key, "status": result.status, "error": result.error}
                )
        return statuses

    def build_context(self, task_id: str) -> dict:
        bundle = self._bundles[task_id]
        return {
            "task_id": bundle.plan.task_id,
            "tenant": bundle.plan.tenant,
            "machine_reference": bundle.plan.machine_reference,
            "environment": bundle.plan.environment,
            "action": bundle.plan.action,
            "requested_agents": list(bundle.plan.agent_keys),
            "results": [
                {
                    "agent": result.agent,
                    "status": result.status,
                    "data": result.data,
                    "error": result.error,
                }
                for result in bundle.results
            ],
            "is_complete": bundle.is_complete,
        }