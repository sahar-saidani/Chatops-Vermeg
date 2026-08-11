from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4


@dataclass(frozen=True)
class ExecutionPlan:
    task_id: str
    tenant: str | None
    machine_reference: str | None
    environment: str | None
    operating_system: str | None
    agent_keys: tuple[str, ...]
    action: str
    parameters: dict[str, str] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        tenant: str | None,
        machine_reference: str | None,
        environment: str | None,
        operating_system: str | None,
        agent_keys: list[str],
        action: str,
        parameters: dict[str, str] | None = None,
    ) -> "ExecutionPlan":
        return cls(
            task_id=uuid4().hex,
            tenant=tenant,
            machine_reference=machine_reference,
            environment=environment,
            operating_system=operating_system,
            agent_keys=tuple(agent_keys),
            action=action,
            parameters=dict(parameters or {}),
        )


@dataclass(frozen=True)
class AgentCommand:
    task_id: str
    tenant: str | None
    machine_reference: str | None
    agent: str
    operating_system: str | None
    action: str
    parameters: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_plan(cls, plan: ExecutionPlan, agent: str) -> "AgentCommand":
        return cls(
            task_id=plan.task_id,
            tenant=plan.tenant,
            machine_reference=plan.machine_reference,
            agent=agent,
            operating_system=plan.operating_system,
            action=plan.action,
            parameters=dict(plan.parameters),
        )


@dataclass(frozen=True)
class AgentResult:
    task_id: str
    tenant: str | None
    machine_reference: str | None
    agent: str
    status: str
    data: dict
    error: str | None = None