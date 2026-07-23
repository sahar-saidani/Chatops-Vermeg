"""Unit tests for collectors and parser behavior."""

from __future__ import annotations

from collectors.build_collector import BuildCollector
from collectors.job_collector import JobCollector
from collectors.log_collector import LogCollector
from models.schemas import JobInfo


class FakeJenkinsClient:
    """Simple fake client for collector testing."""

    def get_jobs(self):
        return [
            {
                "name": "ToDoList-CI",
                "url": "http://jenkins/job/ToDoList-CI/",
                "color": "blue",
                "description": "CI pipeline",
                "lastBuild": {"number": 45},
                "lastSuccessfulBuild": {"number": 45},
                "lastFailedBuild": {"number": 42},
            }
        ]

    def get_job(self, job_name: str):
        return {"builds": [{"number": 45}, {"number": 44}]}

    def get_builds(self, job_name: str):
        return [
            {
                "number": 45,
                "timestamp": 1720500000000,
                "duration": 120000,
                "result": "SUCCESS",
                "actions": [{"causes": [{"userName": "admin"}]}],
                "changeSets": [{"items": [{"commitId": "abc123"}]}],
            }
        ]

    def get_console_logs(self, job_name: str, build_number: int):
        return "[2026-01-01 10:00:00] ERROR npm install failed in Install Dependencies"


def test_job_collector_parses_jobs() -> None:
    collector = JobCollector(FakeJenkinsClient())
    jobs = collector.collect()

    assert len(jobs) == 1
    assert jobs[0].job == "ToDoList-CI"
    assert jobs[0].status == "SUCCESS"
    assert jobs[0].last_failure == 42


def test_build_collector_parses_builds() -> None:
    jobs = [
        JobInfo(
            job="ToDoList-CI",
            url="http://jenkins/job/ToDoList-CI/",
            status="SUCCESS",
        )
    ]
    collector = BuildCollector(FakeJenkinsClient())
    builds = collector.collect(jobs)

    assert len(builds) == 1
    assert builds[0].number == 45
    assert builds[0].result == "SUCCESS"
    assert builds[0].triggered_by == "admin"


def test_log_collector_extracts_issues() -> None:
    jobs = [
        JobInfo(
            job="ToDoList-CI",
            url="http://jenkins/job/ToDoList-CI/",
            status="SUCCESS",
        )
    ]
    collector = LogCollector(FakeJenkinsClient())
    issues = collector.collect(jobs)

    assert len(issues) == 1
    assert issues[0].type == "ERROR"
    assert "npm install failed" in issues[0].message.lower()
