from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from statistics import mean

from models.schemas import HealthScore, RepositoryMetrics, RepositoryReport, RepositorySnapshot


@dataclass(slots=True)
class RepositoryAnalyzer:
    stale_branch_days: int = 90

    def analyze(self, snapshot: RepositorySnapshot) -> RepositoryReport:
        metrics = self._metrics(snapshot)
        health_score = self._health_score(snapshot, metrics)
        generated_at = datetime.now(timezone.utc).isoformat()
        return RepositoryReport(snapshot=snapshot, metrics=metrics, health_score=health_score, generated_at=generated_at)

    def _metrics(self, snapshot: RepositorySnapshot) -> RepositoryMetrics:
        commits = snapshot.commits
        commit_dates = [self._parse_datetime(commit.date) for commit in commits if commit.date]
        commit_dates = [date for date in commit_dates if date is not None]
        last_activity = max(commit_dates).isoformat() if commit_dates else snapshot.repository.updated_at
        commit_span_days = max((max(commit_dates) - min(commit_dates)).days + 1, 1) if len(commit_dates) > 1 else 1
        commits_per_day = len(commits) / commit_span_days if commit_span_days else 0.0
        commits_per_week = commits_per_day * 7
        merged_prs = [pull_request for pull_request in snapshot.pull_requests if pull_request.merged]
        open_prs = [pull_request for pull_request in snapshot.pull_requests if pull_request.open]
        merge_durations = [pull_request.merge_duration_hours for pull_request in merged_prs if pull_request.merge_duration_hours is not None]
        resolution_times = [self._resolution_time(issue.created_at, issue.closed_at) for issue in snapshot.issues if issue.closed_at]
        resolution_times = [value for value in resolution_times if value is not None]
        bug_issues = [issue for issue in snapshot.issues if "bug" in {label.lower() for label in issue.labels}]
        enhancement_issues = [issue for issue in snapshot.issues if "enhancement" in {label.lower() for label in issue.labels}]
        stale_branches = [branch for branch in snapshot.branches if not branch.active and not branch.default_branch]
        top_contributors = sorted(snapshot.contributors, key=lambda contributor: contributor.commits, reverse=True)[:5]
        return RepositoryMetrics(
            commits_per_day=round(commits_per_day, 2),
            commits_per_week=round(commits_per_week, 2),
            top_contributors=top_contributors,
            last_activity=last_activity,
            merged_pr_count=len(merged_prs),
            open_pr_count=len(open_prs),
            average_merge_duration_hours=round(mean(merge_durations), 2) if merge_durations else None,
            number_of_bugs=len(bug_issues),
            number_of_enhancements=len(enhancement_issues),
            average_resolution_time_hours=round(mean(resolution_times), 2) if resolution_times else None,
            stale_branches=len(stale_branches),
        )

    def _health_score(self, snapshot: RepositorySnapshot, metrics: RepositoryMetrics) -> HealthScore:
        breakdown = {
            "documentation": 20 if snapshot.quality_indicators.readme_exists else 0,
            "activity": self._score_activity(metrics),
            "maintenance": 20 if metrics.stale_branches < max(len(snapshot.branches), 1) else 5,
            "testing": 15 if snapshot.quality_indicators.tests_present else 0,
            "ci_cd": 15 if snapshot.quality_indicators.ci_cd_configured else 0,
            "security": self._security_score(snapshot),
            "organization": self._organization_score(snapshot),
        }
        score = min(sum(breakdown.values()), 100)
        return HealthScore(score=score, breakdown=breakdown)

    def _score_activity(self, metrics: RepositoryMetrics) -> int:
        if metrics.commits_per_week >= 20:
            return 20
        if metrics.commits_per_week >= 8:
            return 15
        if metrics.commits_per_week >= 2:
            return 10
        if metrics.commits_per_week > 0:
            return 5
        return 0

    def _security_score(self, snapshot: RepositorySnapshot) -> int:
        score = 0
        score += 5 if snapshot.quality_indicators.license_exists else 0
        score += 5 if snapshot.quality_indicators.security_policy else 0
        score += 5 if snapshot.quality_indicators.dependabot else 0
        return score

    def _organization_score(self, snapshot: RepositorySnapshot) -> int:
        score = 0
        score += 5 if snapshot.quality_indicators.documentation_exists else 0
        score += 5 if snapshot.code_statistics.directories > 1 else 0
        score += 5 if snapshot.code_statistics.source_files > 0 else 0
        return score

    @staticmethod
    def _parse_datetime(value: str):
        return datetime.fromisoformat(value.replace("Z", "+00:00"))

    @staticmethod
    def _resolution_time(created_at: str | None, closed_at: str | None) -> float | None:
        if not created_at or not closed_at:
            return None
        start = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        end = datetime.fromisoformat(closed_at.replace("Z", "+00:00"))
        return (end - start).total_seconds() / 3600
