from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class JiraProject:
    key: str
    name: str
    description: str | None = None
    project_type: str | None = None


@dataclass(slots=True)
class JiraIssue:
    id: str
    key: str
    title: str
    description: str | None = None
    issue_type: str | None = None
    priority: str | None = None
    status: str | None = None
    creator: str | None = None
    assignee: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    labels: list[str] = field(default_factory=list)
    components: list[str] = field(default_factory=list)
    sprint: str | None = None
    history: list[dict[str, Any]] = field(default_factory=list)


@dataclass(slots=True)
class JiraSprint:
    id: str
    name: str
    state: str | None = None
    goal: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    complete_date: str | None = None
    velocity: float | None = None
    progress: float | None = None
    issues: list[str] = field(default_factory=list)


@dataclass(slots=True)
class JiraWorkflow:
    statuses: list[str] = field(default_factory=list)
    transitions: list[dict[str, Any]] = field(default_factory=list)


@dataclass(slots=True)
class JiraSnapshot:
    collected_at: str
    project: JiraProject | None
    projects: list[JiraProject] = field(default_factory=list)
    issues: list[JiraIssue] = field(default_factory=list)
    sprints: list[JiraSprint] = field(default_factory=list)
    workflow: JiraWorkflow | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class AnalyzerOutput:
    project: dict[str, Any]
    statistics: dict[str, Any]
    issues_analysis: dict[str, Any]
    risks: list[dict[str, Any]]
    recommendations: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "project": self.project,
            "statistics": self.statistics,
            "issues_analysis": self.issues_analysis,
            "risks": self.risks,
            "recommendations": self.recommendations,
        }


def utc_now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
