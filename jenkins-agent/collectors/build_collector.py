"""Collector for Jenkins builds."""

from __future__ import annotations

from jenkins.jenkins_client import JenkinsClient
from jenkins.parser import (
    epoch_ms_to_datetime,
    extract_commit_and_branch,
    extract_commit_from_changeset,
    extract_trigger_user,
)
from models.schemas import BuildInfo, JobInfo


class BuildCollector:
    """Collect and normalize Jenkins build data."""

    def __init__(self, client: JenkinsClient, max_builds_per_job: int = 30) -> None:
        self.client = client
        self.max_builds_per_job = max_builds_per_job

    def collect(self, jobs: list[JobInfo]) -> list[BuildInfo]:
        builds: list[BuildInfo] = []
        for job in jobs:
            raw_builds = self.client.get_builds(job.job)[: self.max_builds_per_job]
            for raw in raw_builds:
                actions = raw.get("actions", [])
                commit_id, branch = extract_commit_and_branch(actions)
                if not commit_id:
                    commit_id = extract_commit_from_changeset(raw.get("changeSets"))

                result = raw.get("result") or "IN_PROGRESS"
                builds.append(
                    BuildInfo(
                        job=job.job,
                        number=raw.get("number", 0),
                        timestamp=epoch_ms_to_datetime(raw.get("timestamp")),
                        duration_ms=raw.get("duration", 0),
                        result=result,
                        triggered_by=extract_trigger_user(actions),
                        commit_id=commit_id,
                        branch=branch,
                    )
                )
        return builds
