"""Parser helpers for Jenkins API payloads."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


STATUS_MAP = {
    "blue": "SUCCESS",
    "red": "FAILURE",
    "yellow": "UNSTABLE",
    "aborted": "ABORTED",
    "disabled": "DISABLED",
    "notbuilt": "NOT_BUILT",
}


LOG_KEYWORDS = {
    "ERROR": "ERROR",
    "EXCEPTION": "ERROR",
    "FAILED": "FAILED",
    "WARNING": "WARNING",
}


def epoch_ms_to_datetime(value: int | None) -> datetime:
    """Convert epoch milliseconds to UTC datetime."""
    if not value:
        return datetime.fromtimestamp(0, tz=timezone.utc)
    return datetime.fromtimestamp(value / 1000, tz=timezone.utc)


def normalize_job_status(color: str | None) -> str:
    """Normalize Jenkins color-based status to canonical build status."""
    if not color:
        return "UNKNOWN"
    clean = color.replace("_anime", "").lower()
    return STATUS_MAP.get(clean, clean.upper())


def extract_trigger_user(actions: list[dict[str, Any]] | None) -> str | None:
    """Extract user who triggered the build from Jenkins actions."""
    for action in actions or []:
        causes = action.get("causes") or []
        for cause in causes:
            if cause.get("userName"):
                return cause.get("userName")
            if cause.get("userId"):
                return cause.get("userId")
    return None


def extract_commit_and_branch(actions: list[dict[str, Any]] | None) -> tuple[str | None, str | None]:
    """Extract commit SHA and branch name from actions."""
    for action in actions or []:
        revision = action.get("lastBuiltRevision") or {}
        sha = revision.get("SHA1")
        branches = revision.get("branch") or []
        branch_name = None
        if branches and isinstance(branches, list):
            branch_name = branches[0].get("name")
        if sha or branch_name:
            return sha, branch_name

        by_branch = action.get("buildsByBranchName") or {}
        if by_branch:
            first_branch = next(iter(by_branch.keys()), None)
            if first_branch:
                branch_name = first_branch.replace("refs/remotes/origin/", "")
                return None, branch_name
    return None, None


def extract_commit_from_changeset(change_sets: list[dict[str, Any]] | None) -> str | None:
    """Fallback commit extraction from change sets."""
    for change_set in change_sets or []:
        items = change_set.get("items") or []
        if items:
            return items[0].get("commitId")
    return None


def parse_log_issues(log_text: str, max_issues: int = 50) -> list[dict[str, str | None]]:
    """Extract important log issues from console output."""
    issues: list[dict[str, str | None]] = []
    for line in log_text.splitlines():
        upper = line.upper()
        detected = next((kind for key, kind in LOG_KEYWORDS.items() if key in upper), None)
        if not detected:
            continue

        timestamp = None
        if line.startswith("[") and "]" in line:
            timestamp = line.split("]", 1)[0].strip("[]")

        issues.append(
            {
                "type": detected,
                "message": line.strip()[:500],
                "timestamp": timestamp,
                "stage": _guess_stage_from_line(line),
            }
        )
        if len(issues) >= max_issues:
            break
    return issues


def _guess_stage_from_line(line: str) -> str | None:
    """Heuristic to infer stage name from a Jenkins log line."""
    markers = ("Checkout", "Install", "Test", "Build", "Deploy")
    for marker in markers:
        if marker.lower() in line.lower():
            return marker
    return None
