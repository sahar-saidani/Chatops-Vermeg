"""Collector for Jenkins pipeline stages."""

from __future__ import annotations

from jenkins.jenkins_client import JenkinsClient
from models.schemas import JobInfo, PipelineInfo, StageInfo


class PipelineCollector:
    """Collect stage-level pipeline status from Jenkins wfapi."""

    def __init__(self, client: JenkinsClient) -> None:
        self.client = client

    def collect(self, jobs: list[JobInfo]) -> list[PipelineInfo]:
        pipelines: list[PipelineInfo] = []
        for job in jobs:
            if not job.last_build:
                continue

            try:
                data = self.client.get_pipeline_status(job.job, job.last_build)
            except Exception:
                # Some jobs are not pipeline jobs and do not expose wfapi.
                continue

            raw_stages = data.get("stages", [])
            stages = [
                StageInfo(
                    stage=stage.get("name", "unknown"),
                    status=(stage.get("status") or "UNKNOWN").upper(),
                    duration_ms=stage.get("durationMillis", 0),
                    error=(stage.get("error") or {}).get("message"),
                )
                for stage in raw_stages
            ]
            pipelines.append(
                PipelineInfo(
                    job=job.job,
                    build_number=job.last_build,
                    status=(data.get("status") or job.status).upper(),
                    stages=stages,
                )
            )
        return pipelines
