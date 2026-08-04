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