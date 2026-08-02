from __future__ import annotations

import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import Settings


def test_infrastructure_settings_to_machine_identity(monkeypatch) -> None:
    monkeypatch.setenv("PROMETHEUS_URL", "http://127.0.0.1:9090")
    monkeypatch.setenv("TENANT_NAME", "MAIF")
    monkeypatch.setenv("ENVIRONMENT_NAME", "DEV")
    monkeypatch.setenv("ENVIRONMENT_TYPE", "STANDALONE")
    monkeypatch.setenv("MACHINE_REFERENCE", "MAIF-DEV-INFRA-01")
    monkeypatch.delenv("NODE_ROLE", raising=False)

    settings = Settings.from_env()
    identity = settings.to_machine_identity()

    assert identity.tenant_name == "MAIF"
    assert identity.to_message_fields()["machineReference"] == "MAIF-DEV-INFRA-01"


def test_infrastructure_settings_validate_cluster_requires_node_role(monkeypatch) -> None:
    monkeypatch.setenv("TENANT_NAME", "NNBN")
    monkeypatch.setenv("ENVIRONMENT_NAME", "QA")
    monkeypatch.setenv("ENVIRONMENT_TYPE", "CLUSTER")
    monkeypatch.setenv("MACHINE_REFERENCE", "NNBN-QA-MASTER-01")
    monkeypatch.delenv("NODE_ROLE", raising=False)

    with pytest.raises(ValueError, match="NODE_ROLE"):
        Settings.from_env()
