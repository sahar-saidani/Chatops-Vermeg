from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from agent.analyzer import RepositoryAnalyzer
from agent.collectors import GitHubRepositoryCollector, LocalRepositoryCollector
from agent.report_generator import ReportGenerator
from config.settings import Settings
from models.schemas import RepositoryReport

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class GitRepositoryAgent:
    settings: Settings

    def analyze(self, *, path: Path | None = None, repo: str | None = None ,branch: str | None = None) -> RepositoryReport:
        if bool(path) == bool(repo):
            raise ValueError("Specify exactly one of path or repo")
        collector = self._collector(path=path, repo=repo)
        snapshot = collector.collect()
        analyzer = RepositoryAnalyzer(stale_branch_days=self.settings.stale_branch_days)
        report = analyzer.analyze(snapshot)
        generator = ReportGenerator(self.settings.output_dir)
        generator.generate(report)
        LOGGER.info("Report generation completed in %s", self.settings.output_dir)
        return report

    def _collector(self, *, path: Path | None, repo: str | None):
        if path is not None:
            return LocalRepositoryCollector(repository_path=path, settings=self.settings)
        if repo is not None:
            return GitHubRepositoryCollector(repository_full_name=repo, settings=self.settings)
        raise ValueError("A repository source is required")
