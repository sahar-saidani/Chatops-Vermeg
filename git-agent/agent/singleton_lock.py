"""Machine-wide singleton lock for the git-agent.

The git-agent is launched ONCE per Windows machine and shared by every test
project on that machine - it is not one instance per project, not one per
client. This has nothing to do with the TENANT_NAME/ENVIRONMENT_NAME
identity config: it is a plain "don't let a second instance start on this
box" guard, so it lives in its own module.
"""

from __future__ import annotations

import atexit
import ctypes
import os
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

DEFAULT_LOCK_PATH = Path(os.environ.get("TEMP") or os.environ.get("TMPDIR") or "/tmp") / "chatops-git-agent.lock"


class AlreadyRunningError(RuntimeError):
    """Raised when another git-agent instance already holds the lock on this machine."""


def _pid_is_running(pid: int) -> bool:
    """Best-effort liveness check. Windows-safe: os.kill(pid, 0) would actually
    terminate the target process there, so a real presence check is used instead."""
    if sys.platform == "win32":
        process_query_limited_information = 0x1000
        handle = ctypes.windll.kernel32.OpenProcess(process_query_limited_information, False, pid)
        if handle:
            ctypes.windll.kernel32.CloseHandle(handle)
            return True
        return False

    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


@contextmanager
def singleton_lock(lock_path: Path = DEFAULT_LOCK_PATH) -> Iterator[Path]:
    """Acquire the machine-wide git-agent lock for the life of the `with` block.

    Raises AlreadyRunningError if another live process already holds it.
    A lock file left behind by a process that no longer exists (crash, kill
    -9, reboot) is treated as stale and silently reclaimed.
    """

    if lock_path.exists():
        try:
            existing_pid = int(lock_path.read_text(encoding="utf-8").strip())
        except (ValueError, OSError):
            existing_pid = None

        if existing_pid is not None and _pid_is_running(existing_pid):
            raise AlreadyRunningError(
                f"git-agent is already running on this machine (pid {existing_pid}, lock file {lock_path})."
            )

    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text(str(os.getpid()), encoding="utf-8")

    def _release() -> None:
        try:
            if lock_path.exists() and lock_path.read_text(encoding="utf-8").strip() == str(os.getpid()):
                lock_path.unlink()
        except OSError:
            pass

    atexit.register(_release)
    try:
        yield lock_path
    finally:
        _release()
        atexit.unregister(_release)
