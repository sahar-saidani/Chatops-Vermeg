from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class TenantMachineRoute:
    tenant: str
    machine_reference: str
    environment: str
    available_agents: tuple[str, ...]


class TenantMachineRegistry:
    """Tenant-to-machine routing registry loaded from YAML."""

    def __init__(self, routes: dict[str, TenantMachineRoute], default_tenant: str | None = None):
        self._routes = {tenant.upper(): route for tenant, route in routes.items()}
        self._default_tenant = default_tenant.upper() if default_tenant else None

    @classmethod
    @lru_cache(maxsize=1)
    def load_default(cls) -> "TenantMachineRegistry":
        registry_path = Path(__file__).resolve().parent.parent / "config" / "tenant_machines.yml"
        return cls.from_file(registry_path)

    @classmethod
    def from_file(cls, path: Path) -> "TenantMachineRegistry":
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        default_tenant = raw.get("default_tenant")
        tenants = raw.get("tenants", {})

        routes: dict[str, TenantMachineRoute] = {}
        for tenant_name, data in tenants.items():
            route = cls._parse_route(tenant_name, data)
            routes[tenant_name.upper()] = route

        return cls(routes, default_tenant=default_tenant)

    @property
    def available_tenants(self) -> tuple[str, ...]:
        return tuple(sorted(self._routes))

    @property
    def default_tenant(self) -> str | None:
        return self._default_tenant

    def resolve(self, tenant: str | None) -> TenantMachineRoute | None:
        if tenant:
            return self._routes.get(tenant.upper())
        if self._default_tenant:
            return self._routes.get(self._default_tenant)
        return None

    def infer_tenant(self, text: str) -> str | None:
        normalized = text.upper()
        for tenant in self._routes:
            if tenant in normalized:
                return tenant
        return None

    @staticmethod
    def _parse_route(tenant_name: str, data: Any) -> TenantMachineRoute:
        if not isinstance(data, dict):
            raise ValueError(f"Invalid tenant route for {tenant_name!r}: expected mapping")

        machine_reference = str(data.get("machine_reference", "")).strip()
        environment = str(data.get("environment", "")).strip()
        available_agents_raw = data.get("available_agents", [])
        if not machine_reference:
            raise ValueError(f"Tenant {tenant_name!r} is missing machine_reference")
        if not environment:
            raise ValueError(f"Tenant {tenant_name!r} is missing environment")
        if not isinstance(available_agents_raw, list):
            raise ValueError(f"Tenant {tenant_name!r} available_agents must be a list")

        available_agents = tuple(str(agent).strip() for agent in available_agents_raw if str(agent).strip())

        return TenantMachineRoute(
            tenant=tenant_name.upper(),
            machine_reference=machine_reference,
            environment=environment,
            available_agents=available_agents,
        )