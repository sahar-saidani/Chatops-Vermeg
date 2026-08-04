from types import SimpleNamespace

import orchestrator as orchestrator_module
from data.canonical_events_repository import CanonicalEvent
from execution.models import AgentResult
from intent.models import Intent, RequestMode
from routing.tenant_machine_registry import TenantMachineRegistry


class FakeClassifier:
    def __init__(self, intent: Intent):
        self._intent = intent

    def classify(self, text: str) -> Intent:
        return self._intent


class FakeEventsRepository:
    def __init__(self):
        self.last_find_recent = None

    def wait_for_fresh_data(self, *args, **kwargs):
        return CanonicalEvent(
            id="1",
            agent_key=kwargs["agent_key"],
            message_timestamp=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
            environment=kwargs.get("environment") or "DEV",
            data={"agent": kwargs["agent_key"], "environment": kwargs.get("environment") or "DEV"},
            created_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
        )

    def find_recent(self, agent_keys, since=None, environment=None, tenant=None, limit=200):
        self.last_find_recent = {
            "agent_keys": agent_keys,
            "environment": environment,
            "tenant": tenant,
            "limit": limit,
        }
        return [
            CanonicalEvent(
                id="1",
                agent_key=agent_keys[0],
                message_timestamp=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
                environment=environment or "DEV",
                data={"agent": agent_keys[0], "tenant": tenant},
                created_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
            )
        ]


class FakeAnalyzer:
    def __init__(self):
        self.context = None

    def analyze(self, user_message, events, context=None):
        self.context = context
        return "final answer"


class FakeConversationClient:
    def save(self, turn):
        self.turn = turn
        return True


class FakeGateway:
    def __init__(self, runner):
        self.runner = runner

    def execute(self, plan):
        return [
            AgentResult(
                task_id=plan.task_id,
                tenant=plan.tenant,
                machine_reference=plan.machine_reference,
                agent="git",
                status="SUCCESS",
                data={"launched_at": "2026-08-04T10:00:00+00:00"},
            ),
            AgentResult(
                task_id=plan.task_id,
                tenant=plan.tenant,
                machine_reference=plan.machine_reference,
                agent="jenkins",
                status="SUCCESS",
                data={"launched_at": "2026-08-04T10:00:00+00:00"},
            ),
        ]


def test_orchestrator_aggregates_multi_agent_results(monkeypatch):
    monkeypatch.setattr(orchestrator_module, "SubprocessAgentExecutionGateway", FakeGateway)

    intent = Intent(
        mode=RequestMode.REAL_TIME,
        tenant="MAIF",
        agent_keys=["git", "jenkins"],
        action="analysis",
        environment="DEV",
    )

    fake_analyzer = FakeAnalyzer()
    orch = orchestrator_module.Orchestrator(
        settings=SimpleNamespace(default_tenant=None),
        classifier=FakeClassifier(intent),
        runner=SimpleNamespace(),
        events_repository=FakeEventsRepository(),
        analyzer=fake_analyzer,
        conversation_client=FakeConversationClient(),
        tenant_registry=TenantMachineRegistry.from_file(
            __import__("pathlib").Path(__file__).resolve().parents[1] / "config" / "tenant_machines.yml"
        ),
    )

    result = orch.handle_request("user-1", "Analyze MAIF git and jenkins")

    assert result.tenant == "MAIF"
    assert result.machine_reference == "MAIF-WINDOWS-01"
    assert result.task_id is not None
    assert fake_analyzer.context["tenant"] == "MAIF"
    assert len(fake_analyzer.context["results"]) == 2


def test_orchestrator_asks_for_tenant_when_missing(monkeypatch):
    monkeypatch.setattr(orchestrator_module, "SubprocessAgentExecutionGateway", FakeGateway)

    intent = Intent(mode=RequestMode.REAL_TIME, tenant=None, agent_keys=["git"], action="analysis")
    orch = orchestrator_module.Orchestrator(
        settings=SimpleNamespace(default_tenant=None),
        classifier=FakeClassifier(intent),
        runner=SimpleNamespace(),
        events_repository=FakeEventsRepository(),
        analyzer=FakeAnalyzer(),
        conversation_client=FakeConversationClient(),
        tenant_registry=TenantMachineRegistry.from_file(
            __import__("pathlib").Path(__file__).resolve().parents[1] / "config" / "tenant_machines.yml"
        ),
    )

    result = orch.handle_request("user-1", "Analyze git")

    assert result.task_id is None
    assert "Available tenants" in result.answer