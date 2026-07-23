from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from models.schemas import RepositoryReport


class ReportGenerator:
    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir

    def generate(self, report: RepositoryReport) -> dict[str, Path]:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        json_path = self.output_dir / "report.json"
        markdown_path = self.output_dir / "report.md"
        summary_path = self.output_dir / "summary.txt"
        json_path.write_text(json.dumps(asdict(report), indent=2, ensure_ascii=False), encoding="utf-8")
        markdown_path.write_text(self._markdown(report), encoding="utf-8")
        summary_path.write_text(self._summary(report), encoding="utf-8")
        return {"json": json_path, "markdown": markdown_path, "summary": summary_path}

    def _markdown(self, report: RepositoryReport) -> str:
        snapshot = report.snapshot
        metrics = report.metrics
        health = report.health_score
        lines = [
            f"# {snapshot.repository.name}",
            "",
            f"- Source: {snapshot.source}",
            f"- URL: {snapshot.repository.url}",
            f"- Owner: {snapshot.repository.owner}",
            f"- Visibility: {snapshot.repository.visibility}",
            f"- Default branch: {snapshot.repository.default_branch or 'n/a'}",
            f"- Health score: {health.score}/100",
            "",
            "## Repository",
            f"- Description: {snapshot.repository.description or 'n/a'}",
            f"- Stars: {snapshot.repository.stars}",
            f"- Forks: {snapshot.repository.forks}",
            f"- Watchers: {snapshot.repository.watchers}",
            f"- Open issues: {snapshot.repository.open_issues_count}",
            f"- Languages: {', '.join(f'{language}={count}' for language, count in snapshot.repository.languages.items()) or 'n/a'}",
            "",
            "## Metrics",
            f"- Commits per day: {metrics.commits_per_day}",
            f"- Commits per week: {metrics.commits_per_week}",
            f"- Open PRs: {metrics.open_pr_count}",
            f"- Merged PRs: {metrics.merged_pr_count}",
            f"- Bugs: {metrics.number_of_bugs}",
            f"- Enhancements: {metrics.number_of_enhancements}",
            f"- Stale branches: {metrics.stale_branches}",
            "",
            "## Quality",
            f"- README: {snapshot.quality_indicators.readme_exists}",
            f"- License: {snapshot.quality_indicators.license_exists}",
            f"- CI/CD: {snapshot.quality_indicators.ci_cd_configured}",
            f"- Tests: {snapshot.quality_indicators.tests_present}",
        ]
        return "\n".join(lines) + "\n"

    def _summary(self, report: RepositoryReport) -> str:
        snapshot = report.snapshot
        metrics = report.metrics
        return "\n".join(
            [
                f"Repository: {snapshot.repository.name}",
                f"Source: {snapshot.source}",
                f"Health score: {report.health_score.score}/100",
                f"Commits: {len(snapshot.commits)}",
                f"Contributors: {len(snapshot.contributors)}",
                f"Branches: {len(snapshot.branches)}",
                f"Open PRs: {metrics.open_pr_count}",
                f"Merged PRs: {metrics.merged_pr_count}",
                f"Issues: {len(snapshot.issues)}",
            ]
        )
