"""Orchestrator for Jenkins analysis and report generation."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

from collectors.build_collector import BuildCollector
from collectors.job_collector import JobCollector
from collectors.log_collector import LogCollector
from collectors.pipeline_collector import PipelineCollector
from jenkins.jenkins_client import JenkinsClient
from models.schemas import JenkinsInfo, JenkinsReport, MetricsInfo, RepositoryInfo
from utils.logger import setup_logger


class JenkinsAgent:
    """Main service coordinating all Jenkins and repository collectors."""

    def __init__(self, client: JenkinsClient, report_path: Path) -> None:
        self.client = client
        self.report_path = report_path
        self.logger = setup_logger(__name__)

    def analyze(self, repo_path: Path) -> JenkinsReport:
        """Run end-to-end analysis and return a structured report."""
        self.logger.info("Starting Jenkins analysis")

        job_collector = JobCollector(self.client)
        build_collector = BuildCollector(self.client)
        pipeline_collector = PipelineCollector(self.client)
        log_collector = LogCollector(self.client)

        jobs = job_collector.collect()
        builds = build_collector.collect(jobs)
        pipelines = pipeline_collector.collect(jobs)
        errors = log_collector.collect(jobs)
        repo_info = self._analyze_repository(repo_path)

        info = self.client.get_info()
        jenkins_info = JenkinsInfo(
            url=self.client.base_url,
            version=info.get("version"),
            node_name=info.get("nodeName"),
        )

        metrics = self._compute_metrics(builds)

        report = JenkinsReport(
            project=repo_info.project,
            generated_at=datetime.now(tz=timezone.utc),
            jenkins=jenkins_info,
            repository=repo_info,
            jobs=jobs,
            pipelines=pipelines,
            builds=builds,
            errors=errors,
            metrics=metrics,
        )
        return report

    def write_report(self, report: JenkinsReport) -> None:
        """Write report to JSON file."""
        self.report_path.parent.mkdir(parents=True, exist_ok=True)
        data = report.model_dump(mode="json")
        self.report_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        self.logger.info("Report written to %s", self.report_path)

    def _compute_metrics(self, builds: list) -> MetricsInfo:
        total = len(builds)
        if total == 0:
            return MetricsInfo()

        success = sum(1 for b in builds if b.result == "SUCCESS")
        failures = sum(1 for b in builds if b.result == "FAILURE")
        unstable = sum(1 for b in builds if b.result == "UNSTABLE")
        avg_duration = sum(b.duration_ms for b in builds) / total

        sorted_builds = sorted(builds, key=lambda b: b.timestamp, reverse=True)
        last_failure = next((b.timestamp for b in sorted_builds if b.result == "FAILURE"), None)
        last_success = next((b.timestamp for b in sorted_builds if b.result == "SUCCESS"), None)

        success_rate = (success / total) * 100
        failure_frequency = (failures / total) * 100
        stability_score = ((success + 0.5 * unstable) / total) * 100

        return MetricsInfo(
            success_rate=round(success_rate, 2),
            average_duration_ms=round(avg_duration, 2),
            failure_frequency=round(failure_frequency, 2),
            failure_count=failures,
            last_failure=last_failure,
            last_successful_deployment=last_success,
            stability_score=round(stability_score, 2),
        )

    def _analyze_repository(self, repo_path: Path) -> RepositoryInfo:
        project = repo_path.name
        ci_cd_candidates = [
            ".gitlab-ci.yml",
            "Jenkinsfile",
            "package.json",
            "requirements.txt",
            "Dockerfile",
            "docker-compose.yml",
            ".github/workflows/ci.yml",
        ]

        found_files = []
        for candidate in ci_cd_candidates:
            if list(repo_path.glob(f"**/{candidate}")):
                found_files.append(candidate)

        languages: list[str] = []
        frameworks: list[str] = []

        if (repo_path / "package.json").exists() or list(repo_path.glob("**/package.json")):
            languages.append("JavaScript")

        if list(repo_path.glob("**/*.py")):
            languages.append("Python")

        if (repo_path / "frontend").exists():
            frameworks.append("React")

        if (repo_path / "backend").exists():
            frameworks.append("Express")

        main_branch = self._detect_main_branch(repo_path)

        return RepositoryInfo(
            project=project,
            main_branch=main_branch,
            languages=sorted(set(languages)),
            frameworks=sorted(set(frameworks)),
            ci_cd_files=sorted(set(found_files)),
            has_frontend=(repo_path / "frontend").exists(),
            has_backend=(repo_path / "backend").exists(),
            has_database=(repo_path / "db").exists() or (repo_path / "database").exists(),
        )

    def _detect_main_branch(self, repo_path: Path) -> str | None:
        try:
            cmd = ["git", "-C", str(repo_path), "symbolic-ref", "refs/remotes/origin/HEAD"]
            output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, text=True).strip()
            return output.split("/")[-1]
        except Exception:
            return None


def build_agent_from_env(report_path: Path) -> JenkinsAgent:
    """Construct JenkinsAgent using environment-based configuration."""
    load_dotenv()

    import os

    url = os.getenv("JENKINS_URL", "").strip()
    user = os.getenv("JENKINS_USERNAME", "").strip()
    token = os.getenv("JENKINS_TOKEN", "").strip()

    if not url or not user or not token:
        raise ValueError("Missing JENKINS_URL, JENKINS_USERNAME or JENKINS_TOKEN in environment")

    client = JenkinsClient(base_url=url, username=user, token=token)
    return JenkinsAgent(client=client, report_path=report_path)
