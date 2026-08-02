"""Per-machine tenant/environment identity, shared by every agent on this box.

Kept separate from Settings (git-agent's own CLI/analysis configuration) so
the identity keys stay the same plain names across every agent type:
TENANT_NAME, ENVIRONMENT_NAME, ENVIRONMENT_TYPE, MACHINE_REFERENCE,
NODE_ROLE.
"""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from chatops_common.machine_identity import MachineIdentity

