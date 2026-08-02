"""Per-machine tenant/environment identity, shared by every agent on this box."""

from __future__ import annotations

from pathlib import Path
import os
import sys

from pydantic import BaseModel, ConfigDict

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from chatops_common.machine_identity import MachineIdentity, validate_machine_identity_values


class MachineIdentityConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_name: str = ""
    environment_name: str = ""
    environment_type: str = ""
    machine_reference: str = ""
    node_role: str | None = None

    def with_env_overrides(self) -> "MachineIdentityConfig":
        data = self.model_dump()
        data["tenant_name"] = os.getenv("TENANT_NAME", data["tenant_name"])
        data["environment_name"] = os.getenv("ENVIRONMENT_NAME", data["environment_name"])
        data["environment_type"] = os.getenv("ENVIRONMENT_TYPE", data["environment_type"])
        data["machine_reference"] = os.getenv("MACHINE_REFERENCE", data["machine_reference"])
        data["node_role"] = os.getenv("NODE_ROLE", data["node_role"])
        return MachineIdentityConfig(**data)

    def validate_complete(self) -> None:
        validate_machine_identity_values(
            tenant_name=self.tenant_name,
            environment_name=self.environment_name,
            environment_type=self.environment_type,
            machine_reference=self.machine_reference,
            node_role=self.node_role,
        )

    def to_machine_identity(self) -> MachineIdentity:
        self.validate_complete()
        return MachineIdentity(
            tenant_name=self.tenant_name,
            environment_name=self.environment_name,
            environment_type=self.environment_type,
            machine_reference=self.machine_reference,
            node_role=self.node_role,
        )
