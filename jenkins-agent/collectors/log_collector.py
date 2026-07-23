"""Collector for Jenkins console logs and issue extraction."""

from __future__ import annotations

from jenkins.jenkins_client import JenkinsClient
from jenkins.parser import parse_log_issues
from models.schemas import JobInfo, LogIssue


class LogCollector:
    """Collect and parse Jenkins console logs for errors and warnings."""

    def __init__(self, client: JenkinsClient, max_builds_per_job: int = 10) -> None:
        self.client = client
        self.max_builds_per_job = max_builds_per_job

    def collect(self, jobs: list[JobInfo]) -> list[LogIssue]:
        issues: list[LogIssue] = []
        for job in jobs:
            builds = self.client.get_builds(job.job)[: self.max_builds_per_job]
            for build in builds:
                build_number = build.get("number")
                if build_number is None:
                    continue
                text = self.client.get_console_logs(job.job, build_number)
                for issue in parse_log_issues(text):
                    issues.append(
                        LogIssue(
                            job=job.job,
                            build_number=build_number,
                            type=issue.get("type", "UNKNOWN"),
                            message=issue.get("message", ""),
                            timestamp=issue.get("timestamp"),
                            stage=issue.get("stage"),
                        )
                    )
        return issues
