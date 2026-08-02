"""Shared per-machine identity helpers for all Python agents."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from dotenv import load_dotenv


def _normalize(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def validate_machine_identity_values(
    *,
    tenant_name: str,
    environment_name: str,
    environment_type: str,
    machine_reference: str,
    node_role: str | None = None,
) -> None:
    missing = [
        field
        for field, value in (
            ("TENANT_NAME", tenant_name),
            ("ENVIRONMENT_NAME", environment_name),
            ("ENVIRONMENT_TYPE", environment_type),
            ("MACHINE_REFERENCE", machine_reference),
        )
        if not value
    ]
    if missing:
        raise ValueError(f"Missing required machine identity env var(s): {', '.join(missing)}")
    if environment_type.upper() == "CLUSTER" and not node_role:
        raise ValueError("NODE_ROLE is required when ENVIRONMENT_TYPE is CLUSTER")


def _format_banner(title: str, fields: list[tuple[str, str | None]]) -> str:
    lines = ["==================================================", title]
    lines.extend(f"{label}: {value or ''}" for label, value in fields)
    lines.append("==================================================")
    return "\n".join(lines)


@dataclass(slots=True, frozen=True)
class MachineIdentity:
    tenant_name: str
    environment_name: str
    environment_type: str
    machine_reference: str
    node_role: str | None = None

    @classmethod
    def from_env(cls) -> "MachineIdentity":
        load_dotenv()

        tenant_name = _normalize(os.getenv("TENANT_NAME")) or ""
        environment_name = _normalize(os.getenv("ENVIRONMENT_NAME")) or ""
        environment_type = _normalize(os.getenv("ENVIRONMENT_TYPE")) or ""
        machine_reference = _normalize(os.getenv("MACHINE_REFERENCE")) or ""
        node_role = _normalize(os.getenv("NODE_ROLE"))

        validate_machine_identity_values(
            tenant_name=tenant_name,
            environment_name=environment_name,
            environment_type=environment_type,
            machine_reference=machine_reference,
            node_role=node_role,
        )

        return cls(
            tenant_name=tenant_name,
            environment_name=environment_name,
            environment_type=environment_type,
            machine_reference=machine_reference,
            node_role=node_role,
        )

    def to_message_fields(self) -> dict[str, Any]:
        fields: dict[str, Any] = {
            "tenant": self.tenant_name,
            "environment": self.environment_name,
            "environmentName": self.environment_name,
            "environmentType": self.environment_type,
            "machineReference": self.machine_reference,
        }
        if self.node_role:
            fields["nodeRole"] = self.node_role
        return fields

    def startup_banner(self, agent_name: str, rabbitmq_url: str | None) -> str:
        return _format_banner(
            "Agent Startup",
            [
                ("Agent Name", agent_name),
                ("Tenant", self.tenant_name),
                ("Environment", self.environment_name),
                ("Environment Type", self.environment_type),
                ("Machine Reference", self.machine_reference),
                ("Node Role", self.node_role),
                ("RabbitMQ URL", rabbitmq_url),
            ],
        )

    def publish_banner(self, agent_name: str) -> str:
        return _format_banner(
            "Publishing Agent Message",
            [
                ("Tenant", self.tenant_name),
                ("Environment", self.environment_name),
                ("Environment Type", self.environment_type),
                ("Machine Reference", self.machine_reference),
                ("Node Role", self.node_role),
                ("Agent Name", agent_name),
            ],
        )


def enrich_message(message: dict[str, Any], identity: MachineIdentity) -> dict[str, Any]:
    enriched = dict(message)
    enriched.update(identity.to_message_fields())
    return enriched
