from __future__ import annotations

import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from chatops_common.machine_identity import MachineIdentity, enrich_message


def test_machine_identity_from_env_loads_required_values(monkeypatch) -> None:
    monkeypatch.setenv("TENANT_NAME", "MAIF")
    monkeypatch.setenv("ENVIRONMENT_NAME", "DEV")
    monkeypatch.setenv("ENVIRONMENT_TYPE", "STANDALONE")
    monkeypatch.setenv("MACHINE_REFERENCE", "MAIF-DEV-WIN-01")
    monkeypatch.delenv("NODE_ROLE", raising=False)

    identity = MachineIdentity.from_env()

    assert identity.tenant_name == "MAIF"
    assert identity.environment_name == "DEV"
    assert identity.environment_type == "STANDALONE"
    assert identity.machine_reference == "MAIF-DEV-WIN-01"
    assert identity.node_role is None


def test_machine_identity_requires_node_role_for_cluster(monkeypatch) -> None:
    monkeypatch.setenv("TENANT_NAME", "NNBN")
    monkeypatch.setenv("ENVIRONMENT_NAME", "QA")
    monkeypatch.setenv("ENVIRONMENT_TYPE", "CLUSTER")
    monkeypatch.setenv("MACHINE_REFERENCE", "NNBN-QA-MASTER-01")
    monkeypatch.setenv("NODE_ROLE", "")

    with pytest.raises(ValueError, match="NODE_ROLE"):
        MachineIdentity.from_env()


def test_enrich_message_adds_identity_fields_without_mutating_payload() -> None:
    identity = MachineIdentity(
        tenant_name="MAIF",
        environment_name="DEV",
        environment_type="STANDALONE",
        machine_reference="MAIF-DEV-WIN-01",
    )
    payload = {"agent": "git", "data": {"value": 1}}

    enriched = enrich_message(payload, identity)

    assert payload == {"agent": "git", "data": {"value": 1}}
    assert enriched["tenant"] == "MAIF"
    assert enriched["environment"] == "DEV"
    assert enriched["environmentName"] == "DEV"
    assert enriched["environmentType"] == "STANDALONE"
    assert enriched["machineReference"] == "MAIF-DEV-WIN-01"
