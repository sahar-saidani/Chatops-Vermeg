from __future__ import annotations

import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1] / "logs-agent"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from machine_identity import MachineIdentityConfig


def test_log_agent_machine_identity_exports_message_fields() -> None:
    config = MachineIdentityConfig(
        tenant_name="MAIF",
        environment_name="DEV",
        environment_type="STANDALONE",
        machine_reference="MAIF-DEV-LOG-01",
    )

    fields = config.to_machine_identity().to_message_fields()

    assert fields["tenant"] == "MAIF"
    assert fields["environmentName"] == "DEV"
    assert "nodeRole" not in fields


def test_log_agent_cluster_requires_node_role() -> None:
    config = MachineIdentityConfig(
        tenant_name="NNBN",
        environment_name="QA",
        environment_type="CLUSTER",
        machine_reference="NNBN-QA-SLAVE-01",
    )

    with pytest.raises(ValueError, match="NODE_ROLE"):
        config.validate_complete()
