"""
Locks in the MAIF/NNBE routing separation end-to-end: tenant_machines.yml
-> TenantMachineRegistry -> ExecutionPlan -> AgentCommand ->
AgentRunner._build_execution_command. Uses the real tenant_machines.yml
(not a fake one) so these tests fail the moment the actual routing
configuration or code drifts from what MAIF/NNBE really need.
"""

from __future__ import annotations

import datetime
from pathlib import Path
from types import SimpleNamespace

import orchestrator as orchestrator_module
from agents.registry import get_agent_definition
from agents.runner import AgentRunner
from data.canonical_events_repository import CanonicalEvent
from execution.models import AgentCommand, AgentResult, ExecutionPlan
from intent.models import Intent, RequestMode
from routing.tenant_machine_registry import TenantMachineRegistry

ORCHESTRATOR_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ORCHESTRATOR_ROOT.parent
REGISTRY_PATH = ORCHESTRATOR_ROOT / "config" / "tenant_machines.yml"


def _registry() -> TenantMachineRegistry:
    return TenantMachineRegistry.from_file(REGISTRY_PATH)


def _runner() -> AgentRunner:
    return AgentRunner(
        SimpleNamespace(
            agents_root_dir=REPO_ROOT,
            agent_subprocess_timeout_seconds=300,
        )
    )


def _plan_for(tenant: str, agent_keys: list[str]):
    route = _registry().resolve(tenant)
    assert route is not None, f"no route configured for tenant {tenant!r}"

    parameters = {
        "tenant": route.tenant,
        "environment": route.environment,
        "environment_type": route.environment_type,
        "machine_reference": route.machine_reference,
        "operating_system": route.operating_system,
        "local_execution": route.local_execution,
    }
    if route.repo:
        parameters["repo"] = route.repo
    if route.branch:
        parameters["branch"] = route.branch

    plan = ExecutionPlan.create(
        tenant=route.tenant,
        machine_reference=route.machine_reference,
        environment=route.environment,
        operating_system=route.operating_system,
        agent_keys=agent_keys,
        action="analysis",
        parameters=parameters,
    )
    return plan, route


def _build_command(route, agent_key: str, plan) -> tuple[list[str], object]:
    command = AgentCommand.from_plan(plan, agent_key)
    definition = get_agent_definition(agent_key)
    args = definition.steps[0].build(command.parameters)

    return _runner()._build_execution_command(
        definition=definition,
        args=args,
        machine_reference=route.machine_reference,
        operating_system=route.operating_system,
        local_execution=route.local_execution,
    )


# ============================================================
# TEST 1 - NNBE Git
# ============================================================

def test_nnbe_git_routes_over_ssh_with_nnbe_branch_only(monkeypatch):
    monkeypatch.setenv("NNBE_CENTOS_01_HOST", "192.168.56.101")
    monkeypatch.setenv("NNBE_CENTOS_01_USER", "sahar")
    monkeypatch.setenv("NNBE_CENTOS_01_SSH_PORT", "22")
    monkeypatch.setenv("NNBE_CENTOS_01_GIT_AGENT_DIR", "/home/sahar/Chatops-Vermeg/git-agent")
    monkeypatch.setenv("NNBE_CENTOS_01_GIT_PYTHON", "/home/sahar/Chatops-Vermeg/git-agent/.venv/bin/python")

    plan, route = _plan_for("NNBE", ["git"])

    assert route.machine_reference == "NNBE-CENTOS-01"
    assert route.operating_system == "LINUX"
    assert route.branch == "NNBE-Solife"
    assert route.repo == "sahar-saidani/Solife-Standard"
    assert route.local_execution is False

    command, working_dir = _build_command(route, "git", plan)
    joined = " ".join(command)

    assert working_dir is None  # remote execution never resolves a local cwd
    assert command[0] == "ssh"
    assert "sahar@192.168.56.101" in command
    assert "--branch NNBE-Solife" in joined
    assert "MAIF-Solife" not in joined


# ============================================================
# TEST 2 - MAIF Git
# ============================================================

def test_maif_git_runs_locally_with_maif_branch_only():
    plan, route = _plan_for("MAIF", ["git"])

    assert route.machine_reference == "MAIF-WINDOWS-01"
    assert route.operating_system == "WINDOWS"
    assert route.branch == "MAIF-Solife"
    assert route.local_execution is True

    command, working_dir = _build_command(route, "git", plan)
    joined = " ".join(command)

    assert "ssh" not in command
    assert working_dir is not None
    assert "--branch MAIF-Solife" in joined
    assert "NNBE-Solife" not in joined


# ============================================================
# TEST 3 - NNBE Infrastructure
# ============================================================

def test_nnbe_infrastructure_uses_its_own_python_and_plain_collect(monkeypatch):
    monkeypatch.setenv("NNBE_CENTOS_01_HOST", "192.168.56.101")
    monkeypatch.setenv("NNBE_CENTOS_01_USER", "sahar")
    monkeypatch.setenv(
        "NNBE_CENTOS_01_INFRASTRUCTURE_AGENT_DIR",
        "/home/sahar/Chatops-Vermeg/infrastructure-Agent/app",
    )
    monkeypatch.setenv(
        "NNBE_CENTOS_01_INFRASTRUCTURE_PYTHON",
        "/home/sahar/Chatops-Vermeg/infrastructure-Agent/.venv/bin/python",
    )

    plan, route = _plan_for("NNBE", ["infrastructure"])
    command, _ = _build_command(route, "infrastructure", plan)
    joined = " ".join(command)

    assert "/home/sahar/Chatops-Vermeg/infrastructure-Agent/.venv/bin/python" in joined
    assert "main.py --collect" in joined
    assert "--os" not in joined  # infrastructure's main.py does not accept --os


# ============================================================
# TEST 4 - NNBE Installation
# ============================================================

def test_nnbe_installation_config_dir_from_env():
    plan, route = _plan_for("NNBE", ["installation"])
    command = AgentCommand.from_plan(plan, "installation")
    definition = get_agent_definition("installation")
    args = definition.steps[0].build(command.parameters)

    assert "--config-dir" in args
    assert args[args.index("--config-dir") + 1] == (
        "/home/sahar/Chatops-Vermeg/installation-agent/config"
    )


# ============================================================
# TEST 5 - NNBE Log
# ============================================================

def test_nnbe_log_working_dir_and_python_match_real_layout(monkeypatch):
    monkeypatch.setenv("NNBE_CENTOS_01_HOST", "192.168.56.101")
    monkeypatch.setenv("NNBE_CENTOS_01_USER", "sahar")
    monkeypatch.setenv(
        "NNBE_CENTOS_01_LOG_AGENT_DIR",
        "/home/sahar/Chatops-Vermeg/log-agent/logs-agent",
    )
    monkeypatch.setenv(
        "NNBE_CENTOS_01_LOG_PYTHON",
        "/home/sahar/Chatops-Vermeg/log-agent/.venv/bin/python",
    )

    plan, route = _plan_for("NNBE", ["log"])
    command, _ = _build_command(route, "log", plan)
    joined = " ".join(command)

    # .venv lives at log-agent/, the CLI entrypoint at log-agent/logs-agent/
    # - the two must not be conflated.
    assert "cd /home/sahar/Chatops-Vermeg/log-agent/logs-agent" in joined
    assert "/home/sahar/Chatops-Vermeg/log-agent/.venv/bin/python" in joined
    assert "logs-agent/.venv" not in joined


# ============================================================
# TEST 6 - isolation across successive requests
# ============================================================

class _SequenceClassifier:
    def __init__(self, intents: list[Intent]):
        self._intents = list(intents)

    def classify(self, text: str) -> Intent:
        return self._intents.pop(0)


class _NullEventsRepository:
    def wait_for_fresh_data(self, *args, **kwargs):
        return CanonicalEvent(
            id="1",
            agent_key=kwargs["agent_key"],
            message_timestamp=datetime.datetime.now(datetime.timezone.utc),
            environment=kwargs.get("environment") or "DEV",
            data={},
            created_at=datetime.datetime.now(datetime.timezone.utc),
        )

    def find_recent(self, agent_keys, since=None, environment=None, tenant=None, limit=200):
        return []


class _NullAnalyzer:
    def analyze(self, user_message, events, context=None):
        return "ok"


class _NullConversationClient:
    def save(self, turn):
        return True


class _RecordingGateway:
    def __init__(self, runner):
        self.runner = runner

    def execute(self, plan):
        _RecordingGateway.seen_plans.append(plan)
        return [
            AgentResult(
                task_id=plan.task_id,
                tenant=plan.tenant,
                machine_reference=plan.machine_reference,
                agent="git",
                status="SUCCESS",
                data={"branch": plan.parameters.get("branch")},
            )
        ]

    seen_plans: list = []


def test_successive_requests_do_not_leak_tenant_state(monkeypatch):
    _RecordingGateway.seen_plans = []
    monkeypatch.setattr(orchestrator_module, "SubprocessAgentExecutionGateway", _RecordingGateway)

    sequence = [
        Intent(mode=RequestMode.REAL_TIME, tenant="MAIF", agent_keys=["git"], action="analysis"),
        Intent(mode=RequestMode.REAL_TIME, tenant="NNBE", agent_keys=["git"], action="analysis"),
        Intent(mode=RequestMode.REAL_TIME, tenant="MAIF", agent_keys=["git"], action="analysis"),
        Intent(mode=RequestMode.REAL_TIME, tenant="NNBE", agent_keys=["git"], action="analysis"),
    ]

    orch = orchestrator_module.Orchestrator(
        settings=SimpleNamespace(default_tenant=None),
        classifier=_SequenceClassifier(sequence),
        runner=SimpleNamespace(),
        events_repository=_NullEventsRepository(),
        analyzer=_NullAnalyzer(),
        conversation_client=_NullConversationClient(),
        tenant_registry=_registry(),
    )

    expected = [
        ("MAIF", "MAIF-WINDOWS-01", "MAIF-Solife"),
        ("NNBE", "NNBE-CENTOS-01", "NNBE-Solife"),
        ("MAIF", "MAIF-WINDOWS-01", "MAIF-Solife"),
        ("NNBE", "NNBE-CENTOS-01", "NNBE-Solife"),
    ]

    for expected_tenant, expected_machine, expected_branch in expected:
        result = orch.handle_request("user-1", "Analyze git")
        assert result.tenant == expected_tenant
        assert result.machine_reference == expected_machine

    assert len(_RecordingGateway.seen_plans) == 4

    for plan, (expected_tenant, expected_machine, expected_branch) in zip(
        _RecordingGateway.seen_plans, expected
    ):
        assert plan.tenant == expected_tenant
        assert plan.machine_reference == expected_machine
        assert plan.parameters.get("branch") == expected_branch
        # The other tenant's branch must never appear alongside this one.
        other_branch = "NNBE-Solife" if expected_tenant == "MAIF" else "MAIF-Solife"
        assert plan.parameters.get("branch") != other_branch


# ============================================================
# TEST 7 - DEFAULT_TENANT must never override an explicit tenant
# ============================================================

def test_default_tenant_never_overrides_an_explicit_tenant(monkeypatch):
    _RecordingGateway.seen_plans = []
    monkeypatch.setattr(orchestrator_module, "SubprocessAgentExecutionGateway", _RecordingGateway)

    intent = Intent(
        mode=RequestMode.REAL_TIME,
        tenant="NNBE",
        agent_keys=["git"],
        action="analysis",
    )

    orch = orchestrator_module.Orchestrator(
        # default_tenant is MAIF, but the request explicitly names NNBE.
        settings=SimpleNamespace(default_tenant="MAIF"),
        classifier=_SequenceClassifier([intent]),
        runner=SimpleNamespace(),
        events_repository=_NullEventsRepository(),
        analyzer=_NullAnalyzer(),
        conversation_client=_NullConversationClient(),
        tenant_registry=_registry(),
    )

    result = orch.handle_request("user-1", "Analyze NNBE git")

    assert result.tenant == "NNBE"
    assert result.machine_reference == "NNBE-CENTOS-01"
    assert _RecordingGateway.seen_plans[0].parameters.get("branch") == "NNBE-Solife"
