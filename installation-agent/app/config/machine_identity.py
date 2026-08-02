"""Per-machine tenant/environment identity, shared by every agent on this box.

Kept separate from Settings (which uses AGENT_ as its env var prefix) so
the identity keys stay the same plain names across every agent type:
TENANT_NAME, ENVIRONMENT_NAME, ENVIRONMENT_TYPE, MACHINE_REFERENCE,
NODE_ROLE. Loaded lazily via from_env() rather than at import time, so
importing app.config.settings.settings (as the test suite does) never
requires these to be set.
"""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from chatops_common.machine_identity import MachineIdentity

