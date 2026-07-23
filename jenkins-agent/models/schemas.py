"""Pydantic schemas for Jenkins agent data models."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class JenkinsInfo(BaseModel):
    url: str
    version: str | None = None
    node_name: str | None = None


class JobInfo(BaseModel):
    job: str
    description: str | None = None
    url: str
    status: str
    last_build: int | None = None
    last_success: int | None = None
    last_failure: int | None = None
    total_builds: int = 0


class BuildInfo(BaseModel):
    job: str
    number: int
    timestamp: datetime
    duration_ms: int
    result: str
    triggered_by: str | None = None
    commit_id: str | None = None
    branch: str | None = None


class StageInfo(BaseModel):
    stage: str
    status: str
    duration_ms: int = 0
    error: str | None = None


class PipelineInfo(BaseModel):
    job: str
    build_number: int
    status: str
    stages: list[StageInfo] = Field(default_factory=list)


class LogIssue(BaseModel):
    job: str
    build_number: int
    type: str
    message: str
    timestamp: str | None = None
    stage: str | None = None


class RepositoryInfo(BaseModel):
    project: str
    main_branch: str | None = None
    languages: list[str] = Field(default_factory=list)
    frameworks: list[str] = Field(default_factory=list)
    ci_cd_files: list[str] = Field(default_factory=list)
    has_frontend: bool = False
    has_backend: bool = False
    has_database: bool = False


class MetricsInfo(BaseModel):
    success_rate: float = 0.0
    average_duration_ms: float = 0.0
    failure_frequency: float = 0.0
    failure_count: int = 0
    last_failure: datetime | None = None
    last_successful_deployment: datetime | None = None
    stability_score: float = 0.0


class JenkinsReport(BaseModel):
    project: str
    generated_at: datetime
    jenkins: JenkinsInfo
    repository: RepositoryInfo
    jobs: list[JobInfo] = Field(default_factory=list)
    pipelines: list[PipelineInfo] = Field(default_factory=list)
    builds: list[BuildInfo] = Field(default_factory=list)
    errors: list[LogIssue] = Field(default_factory=list)
    metrics: MetricsInfo


class AgentMessage(BaseModel):
    agent: str = "jenkins-agent"
    timestamp: datetime
    data: dict[str, Any]
