"""Per-machine tenant/environment identity, shared by every agent on this box.

Jenkins runs this agent on two dedicated machines - one for RELEASE jobs,
one for SNAPSHOT jobs - so on top of the common identity fields this module
also reads JENKINS_PURPOSE (RELEASE|SNAPSHOT) so the same agent codebase
works unmodified on either machine.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

_VALID_JENKINS_PURPOSES = {"RELEASE", "SNAPSHOT"}

# A bare load_dotenv() relies on python-dotenv's call-stack inspection to
# locate .env relative to the caller's file - this module's caller is
# agent/machine_identity.py itself, one directory below jenkins-agent/.env.
# That resolution is version- and platform-dependent (confirmed: it finds
# the file locally on Windows but silently fails on the deployed Linux
# venv, even with the working directory set to jenkins-agent/ - the
# process then starts with every identity field blank instead of a load
# error, so the agent crashes deep inside from_env() with a confusing
# "missing env var" instead of a clear "wrong .env path"). Anchoring to
# this file's own location removes the ambiguity entirely.
_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"


@dataclass(slots=True, frozen=True)
class MachineIdentity:
    tenant_name: str
    environment_name: str
    # STANDALONE | CLUSTER today; kept as a plain string (not an enum) since
    # REF's topology/type is not defined yet and must not require a code change.
    environment_type: str
    machine_reference: str
    jenkins_purpose: str
    # MASTER | SLAVE - only required when environment_type == "CLUSTER"
    node_role: str | None = None

    @classmethod
    def from_env(cls) -> "MachineIdentity":
        load_dotenv(_ENV_PATH)

        tenant_name = os.getenv("TENANT_NAME", "").strip()
        environment_name = os.getenv("ENVIRONMENT_NAME", "").strip()
        environment_type = os.getenv("ENVIRONMENT_TYPE", "").strip()
        machine_reference = os.getenv("MACHINE_REFERENCE", "").strip()
        jenkins_purpose = os.getenv("JENKINS_PURPOSE", "").strip().upper()
        node_role = os.getenv("NODE_ROLE", "").strip() or None

        missing = [
            name
            for name, value in (
                ("TENANT_NAME", tenant_name),
                ("ENVIRONMENT_NAME", environment_name),
                ("ENVIRONMENT_TYPE", environment_type),
                ("MACHINE_REFERENCE", machine_reference),
                ("JENKINS_PURPOSE", jenkins_purpose),
            )
            if not value
        ]
        if missing:
            raise ValueError(f"Missing required machine identity env var(s): {', '.join(missing)}")
        if jenkins_purpose not in _VALID_JENKINS_PURPOSES:
            raise ValueError(f"JENKINS_PURPOSE must be one of {sorted(_VALID_JENKINS_PURPOSES)}, got {jenkins_purpose!r}")
        if environment_type.upper() == "CLUSTER" and not node_role:
            raise ValueError("NODE_ROLE is required when ENVIRONMENT_TYPE is CLUSTER")

        return cls(
            tenant_name=tenant_name,
            environment_name=environment_name,
            environment_type=environment_type,
            machine_reference=machine_reference,
            jenkins_purpose=jenkins_purpose,
            node_role=node_role,
        )
