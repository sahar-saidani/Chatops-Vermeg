from __future__ import annotations

import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config.machine_identity import MachineIdentity


def test_installation_agent_machine_identity_from_env(monkeypatch) -> None:
    monkeypatch.setenv("TENANT_NAME", "MAIF")
    monkeypatch.setenv("ENVIRONMENT_NAME", "DEV")
    monkeypatch.setenv("ENVIRONMENT_TYPE", "STANDALONE")
    monkeypatch.setenv("MACHINE_REFERENCE", "MAIF-DEV-01")
    monkeypatch.delenv("NODE_ROLE", raising=False)

    identity = MachineIdentity.from_env()

    assert identity.tenant_name == "MAIF"
    assert identity.to_message_fields()["environmentName"] == "DEV"


def test_installation_agent_machine_identity_requires_required_fields(monkeypatch) -> None:
    monkeypatch.setenv("TENANT_NAME", "")
    monkeypatch.setenv("ENVIRONMENT_NAME", "")
    monkeypatch.setenv("ENVIRONMENT_TYPE", "")
    monkeypatch.setenv("MACHINE_REFERENCE", "")

    with pytest.raises(ValueError, match="TENANT_NAME"):
        MachineIdentity.from_env()
