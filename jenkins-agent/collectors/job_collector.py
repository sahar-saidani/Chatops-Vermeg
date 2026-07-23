"""Collector for Jenkins jobs."""

from __future__ import annotations

from jenkins.jenkins_client import JenkinsClient
from jenkins.parser import normalize_job_status
from models.schemas import JobInfo


class JobCollector:
    """Collect and normalize Jenkins job data."""

    def __init__(self, client: JenkinsClient) -> None:
        self.client = client

    def collect(self) -> list[JobInfo]:
        jobs = self.client.get_jobs()
        collected: list[JobInfo] = []
        for raw in jobs:
            name = raw.get("name", "unknown")
            build_data = self.client.get_job(name)
            builds = build_data.get("builds", [])
            collected.append(
                JobInfo(
                    job=name,
                    description=raw.get("description"),
                    url=raw.get("url", ""),
                    status=normalize_job_status(raw.get("color")),
                    last_build=(raw.get("lastBuild") or {}).get("number"),
                    last_success=(raw.get("lastSuccessfulBuild") or {}).get("number"),
                    last_failure=(raw.get("lastFailedBuild") or {}).get("number"),
                    total_builds=len(builds),
                )
            )
        return collected
