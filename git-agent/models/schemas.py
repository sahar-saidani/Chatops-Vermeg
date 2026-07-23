from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class DataclassJSONMixin:
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class DependencyItem(DataclassJSONMixin):
    name: str
    version: str | None = None
    specifier: str | None = None
    scope: str | None = None


@dataclass(slots=True)
class RepositoryInfo(DataclassJSONMixin):
    name: str
    description: str | None
    owner: str
    visibility: str
    created_at: str | None
    updated_at: str | None
    default_branch: str | None
    size_kb: int | None
    license: str | None
    url: str
    stars: int
    forks: int
    watchers: int
    open_issues_count: int
    topics: list[str] = field(default_factory=list)
    homepage: str | None = None
    languages: dict[str, int] = field(default_factory=dict)
    age_days: int | None = None
    archived: bool = False


@dataclass(slots=True)
class BranchInfo(DataclassJSONMixin):
    name: str
    default_branch: bool
    protected: bool | None
    last_commit: str | None
    last_update: str | None
    active: bool


@dataclass(slots=True)
class CommitInfo(DataclassJSONMixin):
    hash: str
    author: str
    email: str | None
    date: str
    message: str
    files_modified: list[str] = field(default_factory=list)
    insertions: int = 0
    deletions: int = 0
    merge_commit: bool = False
    statistics: dict[str, int] = field(default_factory=dict)


@dataclass(slots=True)
class ContributorInfo(DataclassJSONMixin):
    name: str
    email: str | None
    commits: int
    last_contribution: str | None
    ranking: int


@dataclass(slots=True)
class PullRequestInfo(DataclassJSONMixin):
    title: str
    description: str | None
    author: str | None
    state: str
    open: bool
    closed: bool
    merged: bool
    created_at: str | None
    merged_at: str | None
    closed_at: str | None
    reviewers: list[str] = field(default_factory=list)
    comments: int = 0
    labels: list[str] = field(default_factory=list)
    merge_duration_hours: float | None = None


@dataclass(slots=True)
class IssueInfo(DataclassJSONMixin):
    title: str
    state: str
    labels: list[str] = field(default_factory=list)
    creator: str | None = None
    assignee: str | None = None
    comments: int = 0
    created_at: str | None = None
    closed_at: str | None = None


@dataclass(slots=True)
class ReleaseInfo(DataclassJSONMixin):
    tag: str
    name: str | None
    body: str | None
    published_at: str | None
    latest: bool = False


@dataclass(slots=True)
class StructureItem(DataclassJSONMixin):
    path: str
    kind: str
    size_bytes: int | None = None


@dataclass(slots=True)
class TechnologyEvidence(DataclassJSONMixin):
    name: str
    evidence: list[str] = field(default_factory=list)
    confidence: float = 0.0


@dataclass(slots=True)
class QualityIndicators(DataclassJSONMixin):
    readme_exists: bool = False
    license_exists: bool = False
    ci_cd_configured: bool = False
    tests_present: bool = False
    documentation_exists: bool = False
    docker_support: bool = False
    issue_templates: bool = False
    pull_request_templates: bool = False
    codeowners: bool = False
    security_policy: bool = False
    dependabot: bool = False


@dataclass(slots=True)
class CodeStatistics(DataclassJSONMixin):
    directories: int = 0
    files: int = 0
    source_files: int = 0
    loc_estimation: int = 0
    largest_directories: list[dict[str, Any]] = field(default_factory=list)
    language_distribution: dict[str, int] = field(default_factory=dict)


@dataclass(slots=True)
class RepositorySnapshot(DataclassJSONMixin):
    source: str
    repository: RepositoryInfo
    branches: list[BranchInfo] = field(default_factory=list)
    commits: list[CommitInfo] = field(default_factory=list)
    contributors: list[ContributorInfo] = field(default_factory=list)
    pull_requests: list[PullRequestInfo] = field(default_factory=list)
    issues: list[IssueInfo] = field(default_factory=list)
    releases: list[ReleaseInfo] = field(default_factory=list)
    structure: list[StructureItem] = field(default_factory=list)
    dependencies: list[DependencyItem] = field(default_factory=list)
    technologies: list[TechnologyEvidence] = field(default_factory=list)
    quality_indicators: QualityIndicators = field(default_factory=QualityIndicators)
    code_statistics: CodeStatistics = field(default_factory=CodeStatistics)


@dataclass(slots=True)
class RepositoryMetrics(DataclassJSONMixin):
    commits_per_day: float = 0.0
    commits_per_week: float = 0.0
    top_contributors: list[ContributorInfo] = field(default_factory=list)
    last_activity: str | None = None
    merged_pr_count: int = 0
    open_pr_count: int = 0
    average_merge_duration_hours: float | None = None
    number_of_bugs: int = 0
    number_of_enhancements: int = 0
    average_resolution_time_hours: float | None = None
    stale_branches: int = 0


@dataclass(slots=True)
class HealthScore(DataclassJSONMixin):
    score: int
    breakdown: dict[str, int] = field(default_factory=dict)


@dataclass(slots=True)
class RepositoryReport(DataclassJSONMixin):
    snapshot: RepositorySnapshot
    metrics: RepositoryMetrics
    health_score: HealthScore
    generated_at: str
