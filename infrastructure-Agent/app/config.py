
"""Application configuration helpers for the health monitoring MVP."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from chatops_common.machine_identity import (
    MachineIdentity,
    validate_machine_identity_values,
)

load_dotenv()


@dataclass(slots=True)
class Settings:
    """Runtime settings loaded from environment variables and .env files."""

    prometheus_url: str = "http://127.0.0.1:9090"
    prometheus_timeout_seconds: float = 10.0
    log_level: str = "INFO"
    log_file: str = "logs/infrastructure_agent.log"
    target_name: str = "CentOS VM"
    rabbitmq_url: str | None = None

    # Per-machine tenant/environment identity - config-driven, never branch
    # on tenant_name in code. node_role is required only when
    # environment_type is CLUSTER; environment_type is kept as a plain
    # string (not an enum) since REF's topology is not defined yet.
    tenant_name: str = ""
    environment_name: str = ""
    environment_type: str = ""
    machine_reference: str = ""
    node_role: str | None = None
    operating_system: str = ""

    @classmethod
    def from_env(cls) -> "Settings":
        """Build settings from environment variables and .env files."""

        defaults = cls()

        settings = cls(
            prometheus_url=os.getenv(
                "PROMETHEUS_URL",
                defaults.prometheus_url,
            ),
            prometheus_timeout_seconds=float(
                os.getenv(
                    "PROMETHEUS_TIMEOUT_SECONDS",
                    str(defaults.prometheus_timeout_seconds),
                )
            ),
            operating_system=os.getenv(
                "OPERATING_SYSTEM",
                defaults.operating_system,
            ).upper(),
            log_level=os.getenv(
                "LOG_LEVEL",
                defaults.log_level,
            ),
            log_file=os.getenv(
                "LOG_FILE",
                defaults.log_file,
            ),
            target_name=os.getenv(
                "TARGET_NAME",
                defaults.target_name,
            ),
            rabbitmq_url=os.getenv("RABBITMQ_URL") or None,
            tenant_name=os.getenv(
                "TENANT_NAME",
                defaults.tenant_name,
            ),
            environment_name=os.getenv(
                "ENVIRONMENT_NAME",
                defaults.environment_name,
            ),
            environment_type=os.getenv(
                "ENVIRONMENT_TYPE",
                defaults.environment_type,
            ),
            machine_reference=os.getenv(
                "MACHINE_REFERENCE",
                defaults.machine_reference,
            ),
            node_role=os.getenv("NODE_ROLE") or None,
        )

        if settings.operating_system not in {"LINUX", "WINDOWS"}:
            raise ValueError(
                "OPERATING_SYSTEM must be LINUX or WINDOWS"
            )

        settings.validate_machine_identity()

        return settings

    def validate_machine_identity(self) -> None:
        """Raise ValueError if required identity fields are missing."""

        validate_machine_identity_values(
            tenant_name=self.tenant_name,
            environment_name=self.environment_name,
            environment_type=self.environment_type,
            machine_reference=self.machine_reference,
            node_role=self.node_role,
        )

    def to_machine_identity(self) -> MachineIdentity:
        """Convert settings into a MachineIdentity object."""

        return MachineIdentity(
            tenant_name=self.tenant_name,
            environment_name=self.environment_name,
            environment_type=self.environment_type,
            machine_reference=self.machine_reference,
            node_role=self.node_role,
        )


def ensure_log_directory(log_file: str) -> None:
    """Create the parent directory for the configured log file."""

    Path(log_file).parent.mkdir(parents=True, exist_ok=True)


def resolve_project_path(relative_path: str) -> Path:
    """Resolve a path relative to the project root unless it is already absolute."""

    path = Path(relative_path)

    if path.is_absolute():
        return path

    return Path(__file__).resolve().parents[1] / path
