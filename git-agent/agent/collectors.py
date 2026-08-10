from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from config.settings import Settings
from git.local_git import LocalGitRepository
from github.github_client import GitHubClient
from models.schemas import RepositorySnapshot

LOGGER = logging.getLogger(__name__)


class RepositoryCollector(Protocol):
    def collect(self) -> RepositorySnapshot:
        ...


@dataclass(slots=True)
class LocalRepositoryCollector:
    repository_path: Path
    settings: Settings

    def collect(self) -> RepositorySnapshot:
        LOGGER.info("Collecting local repository snapshot from %s", self.repository_path)
        return LocalGitRepository(
            path=self.repository_path,
            stale_branch_days=self.settings.stale_branch_days,
            active_window_days=self.settings.active_window_days,
        ).collect_snapshot()


@dataclass(slots=True)
class GitHubRepositoryCollector:
    repository_full_name: str
    settings: Settings

    def collect(self) -> RepositorySnapshot:
        LOGGER.info("Collecting GitHub repository snapshot from %s", self.repository_full_name)
        client = GitHubClient(token=self.settings.github_token, timeout=self.settings.request_timeout_seconds, per_page=self.settings.per_page)
        return client.get_repository_snapshot(
            self.repository_full_name,
            analyzed_branches=self.settings.github_branches,
        )
