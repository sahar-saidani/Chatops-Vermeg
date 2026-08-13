from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

# installation-agent/ root, regardless of the current working directory or
# which machine (Windows/Linux) this runs on - used as the default base for
# every relative path below instead of a hardcoded developer-machine path.
_AGENT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AGENT_", case_sensitive=False)

    # Core directories
    workspace_dir: Path = _AGENT_ROOT
    fake_files_dir: Path = Path("fake_files")
    # Real configuration/installation artifacts to scan in production.
    # This is the directory the Installation Agent actually analyzes when
    # run via `main.py --scan` - never fake/generated files.
    config_dir: Path = Path("config")
    reports_dir: Path = Path("reports")
    logs_dir: Path = Path("logs")
    
    # Scanner Settings
    ignored_folders: List[str] = [
        ".git", 
        ".venv", 
        "venv", 
        "__pycache__", 
        "node_modules", 
        ".pytest_cache", 
        ".idea", 
        ".vscode",
        "dist",
        "build"
    ]

    # Symlinks are NOT followed by default. os.walk(followlinks=True) has no
    # cycle detection: a single self-referential or parent-pointing link makes
    # the walk run forever, and a link out of the scan root silently drags in
    # whatever it points at. Both turned a scan into a hang that outlived the
    # orchestrator's 300s subprocess timeout. When explicitly re-enabled, the
    # scanner still refuses links that resolve outside the scan root and still
    # tracks visited directories so a cycle terminates.
    follow_symlinks: bool = False

    # Hard bounds on a single scan. All of them are env-overridable
    # (AGENT_MAX_SCAN_DEPTH, AGENT_MAX_SCAN_FILES, ...) so a deliberately
    # exhaustive run is still possible, but the default can no longer hang.

    # Depth below the scan root, in directory levels.
    max_scan_depth: int = 12

    # Upper bound on indexed files; the scan stops early and flags itself as
    # truncated rather than running until something kills it.
    max_scan_files: int = 20000

    # Files larger than this are indexed without hashes. Hashing reads every
    # byte twice (MD5 + SHA256), so a handful of multi-gigabyte artifacts
    # dominated the runtime of an otherwise small scan.
    max_hash_file_size_bytes: int = 256 * 1024 * 1024

    # Wall-clock budget. Well under the orchestrator's 300s subprocess timeout
    # so the agent returns a truncated-but-valid report instead of being killed
    # mid-write and leaving the caller with nothing.
    max_scan_seconds: int = 180

    # Never descended into, at any depth. Pseudo-filesystems yield endless or
    # blocking reads, and the Windows/system trees are enormous and irrelevant
    # to an installation artifact scan.
    excluded_absolute_paths: List[str] = [
        "/proc",
        "/sys",
        "/dev",
        "/run",
        "/snap",
        "/var/lib/docker",
        "C:\\Windows",
        "C:\\$Recycle.Bin",
        "C:\\ProgramData\\Microsoft\\Windows",
        "C:\\System Volume Information",
    ]

    # Watcher Settings
    watch_directory: Path = Path("fake_files")
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/installation_agent.log"

    def get_absolute_path(self, path: Path | str) -> Path:
        """Returns absolute path, relative to workspace if not absolute already."""
        p = Path(path)
        if p.is_absolute():
            return p
        return (Path(self.workspace_dir) / p).resolve()

settings = Settings()
