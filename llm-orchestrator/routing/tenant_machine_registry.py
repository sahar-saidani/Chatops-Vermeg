from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class TenantMachineRoute:
    """Routing information for one tenant machine."""

    tenant: str
    machine_reference: str
    environment: str
    environment_type: str
    operating_system: str
    available_agents: tuple[str, ...]

    repo: str | None = None
    branch: str | None = None

    # Run this tenant's agents as local subprocesses instead of over SSH.
    #
    # This used to be inferred from machine_reference == "windows-local",
    # which forced one field to be both the machine's *identity* (stamped on
    # every event and used to correlate canonical_events rows) and the
    # *transport* decision. The two conflict: agents on the MAIF box report
    # machine_reference "MAIF-WINDOWS-01", so naming it "windows-local" to get
    # local execution meant the routed identity matched nothing that was ever
    # recorded. Declaring transport separately lets the identity stay correct.
    local_execution: bool = False


class TenantMachineRegistry:
    """Tenant-to-machine routing registry loaded from YAML."""

    def __init__(
        self,
        routes: dict[str, TenantMachineRoute],
        default_tenant: str | None = None,
    ):
        self._routes = {
            tenant.upper(): route
            for tenant, route in routes.items()
        }

        self._default_tenant = (
            default_tenant.upper()
            if default_tenant
            else None
        )

    @classmethod
    @lru_cache(maxsize=1)
    def load_default(cls) -> "TenantMachineRegistry":
        """Load the default tenant-machine registry."""

        registry_path = (
            Path(__file__).resolve().parent.parent
            / "config"
            / "tenant_machines.yml"
        )

        return cls.from_file(registry_path)

    @classmethod
    def from_file(cls, path: Path) -> "TenantMachineRegistry":
        """Load tenant routes from a YAML file."""

        raw = yaml.safe_load(
            path.read_text(encoding="utf-8")
        ) or {}

        default_tenant = raw.get("default_tenant")
        tenants = raw.get("tenants", {})

        if not isinstance(tenants, dict):
            raise ValueError(
                "Invalid tenant registry: 'tenants' must be a mapping"
            )

        routes: dict[str, TenantMachineRoute] = {}

        for tenant_name, data in tenants.items():
            route = cls._parse_route(
                tenant_name,
                data,
            )

            routes[tenant_name.upper()] = route

        return cls(
            routes,
            default_tenant=default_tenant,
        )

    @property
    def available_tenants(self) -> tuple[str, ...]:
        """Return all configured tenant names."""

        return tuple(sorted(self._routes))

    @property
    def default_tenant(self) -> str | None:
        """Return the configured default tenant."""

        return self._default_tenant

    def resolve(
        self,
        tenant: str | None,
    ) -> TenantMachineRoute | None:
        """
        Resolve a tenant to its machine route.

        If no tenant is provided, the configured default tenant
        is used.
        """

        if tenant:
            return self._routes.get(
                tenant.upper()
            )

        if self._default_tenant:
            return self._routes.get(
                self._default_tenant
            )

        return None

    def infer_tenant(
        self,
        text: str,
    ) -> str | None:
        """
        Infer a tenant from user text.

        Example:
            "Show CPU metrics for MAIF"
            -> "MAIF"
        """

        normalized = text.upper()

        for tenant in self._routes:
            if tenant in normalized:
                return tenant

        return None

    @staticmethod
    def _parse_route(
        tenant_name: str,
        data: Any,
    ) -> TenantMachineRoute:
        """Validate and build a tenant machine route."""

        if not isinstance(data, dict):
            raise ValueError(
                f"Invalid tenant route for {tenant_name!r}: "
                "expected mapping"
            )

        # --------------------------------------------------
        # Machine
        # --------------------------------------------------

        machine_reference = str(
            data.get("machine_reference", "")
        ).strip()

        if not machine_reference:
            raise ValueError(
                f"Tenant {tenant_name!r} is missing "
                "machine_reference"
            )

        # --------------------------------------------------
        # Environment
        # --------------------------------------------------

        environment = str(
            data.get("environment", "")
        ).strip().upper()

        if not environment:
            raise ValueError(
                f"Tenant {tenant_name!r} is missing environment"
            )

        environment_type = str(
            data.get("environment_type", "")
        ).strip().upper()

        if environment_type not in {
            "STANDALONE",
            "CLUSTER",
        }:
            raise ValueError(
                f"Tenant {tenant_name!r} must define "
                "environment_type as STANDALONE or CLUSTER"
            )

        # --------------------------------------------------
        # Operating system
        # --------------------------------------------------

        operating_system = str(
            data.get("operating_system", "")
        ).strip().upper()

        if operating_system not in {
            "LINUX",
            "WINDOWS",
        }:
            raise ValueError(
                f"Tenant {tenant_name!r} must define "
                "operating_system as LINUX or WINDOWS"
            )

        # --------------------------------------------------
        # Available agents
        # --------------------------------------------------

        available_agents_raw = data.get(
            "available_agents",
            [],
        )

        if not isinstance(
            available_agents_raw,
            list,
        ):
            raise ValueError(
                f"Tenant {tenant_name!r} "
                "available_agents must be a list"
            )

        available_agents = tuple(
            str(agent).strip()
            for agent in available_agents_raw
            if str(agent).strip()
        )

        # --------------------------------------------------
        # Build route
        # --------------------------------------------------

        return TenantMachineRoute(
            tenant=tenant_name.upper(),
            machine_reference=machine_reference,
            environment=environment,
            environment_type=environment_type,
            operating_system=operating_system,
            available_agents=available_agents,
            repo=data.get("repo"),
            branch=data.get("branch"),
            # Backwards compatible: a registry still using the old
            # "windows-local" sentinel as its machine_reference keeps running
            # locally instead of suddenly attempting SSH.
            local_execution=bool(data.get("local_execution", False))
            or machine_reference.strip().lower() == "windows-local",
        )