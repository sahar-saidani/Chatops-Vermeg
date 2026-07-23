from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import git.local_git as local_git_module
from git.local_git import LocalGitRepository


@dataclass
class FakeAuthor:
    name: str
    email: str


class FakeCommitStats:
    def __init__(self, files: dict[str, object], total: dict[str, int]) -> None:
        self.files = files
        self.total = total


class FakeCommit:
    def __init__(self, hexsha: str, author: FakeAuthor, committed_datetime: datetime, message: str, files: dict[str, object], total: dict[str, int], parents: list[object] | None = None) -> None:
        self.hexsha = hexsha
        self.author = author
        self.committed_datetime = committed_datetime
        self.message = message
        self.stats = FakeCommitStats(files, total)
        self.parents = parents or []


class FakeBranch:
    def __init__(self, name: str, commit: FakeCommit) -> None:
        self.name = name
        self.commit = commit


class FakeTag:
    def __init__(self, name: str, commit: FakeCommit) -> None:
        self.name = name
        self.commit = commit


class FakeRepo:
    def __init__(self, path: Path) -> None:
        now = datetime(2024, 2, 10, tzinfo=timezone.utc)
        older = datetime(2024, 1, 1, tzinfo=timezone.utc)
        self._commits = [
            FakeCommit("abc123", FakeAuthor("Alice", "alice@example.com"), now, "Add feature", {"app.py": object()}, {"total": 12, "insertions": 10, "deletions": 2}),
            FakeCommit("def456", FakeAuthor("Bob", "bob@example.com"), older, "Initial commit", {"README.md": object()}, {"total": 6, "insertions": 5, "deletions": 1}),
        ]
        self.bare = False
        self.head = SimpleNamespace(commit=self._commits[0], is_detached=False)
        self.active_branch = SimpleNamespace(name="main")
        self.remotes = [SimpleNamespace(url="https://example.com/repo.git")]
        self.branches = [FakeBranch("main", self._commits[0]), FakeBranch("legacy", self._commits[1])]
        self.tags = [FakeTag("v1.0.0", self._commits[0])]
        self._path = path

    def iter_commits(self, *args, **kwargs):
        if kwargs.get("reverse") and kwargs.get("max_count") == 1:
            return [self._commits[-1]]
        return self._commits


class FakeGitPythonModule:
    def __init__(self, repo: FakeRepo) -> None:
        self._repo = repo

    def Repo(self, path: Path) -> FakeRepo:
        return self._repo


def test_local_git_collects_snapshot(tmp_path, monkeypatch) -> None:
    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")
    (tmp_path / "LICENSE").write_text("MIT\n", encoding="utf-8")
    (tmp_path / "requirements.txt").write_text("Flask==3.0.0\npytest==8.0.0\n", encoding="utf-8")
    (tmp_path / "app.py").write_text("print('hello')\n", encoding="utf-8")
    (tmp_path / "Dockerfile").write_text("FROM python:3.11\n", encoding="utf-8")
    (tmp_path / ".gitlab-ci.yml").write_text("stages: [test]\n", encoding="utf-8")
    (tmp_path / ".github").mkdir()
    (tmp_path / ".github" / "workflows").mkdir(parents=True)
    (tmp_path / ".github" / "workflows" / "ci.yml").write_text("name: ci\n", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_app.py").write_text("def test_app():\n    assert True\n", encoding="utf-8")

    fake_repo = FakeRepo(tmp_path)
    monkeypatch.setattr(local_git_module, "_GITPYTHON", FakeGitPythonModule(fake_repo))

    snapshot = LocalGitRepository(path=tmp_path).collect_snapshot()

    assert snapshot.repository.name == tmp_path.name
    assert snapshot.quality_indicators.readme_exists is True
    assert snapshot.quality_indicators.license_exists is True
    assert snapshot.quality_indicators.ci_cd_configured is True
    assert snapshot.quality_indicators.tests_present is True
    assert snapshot.repository.languages["Python"] >= 1
    assert any(tech.name == "Python" for tech in snapshot.technologies)
    assert any(tech.name == "Flask" for tech in snapshot.technologies)
    assert snapshot.contributors[0].name == "Alice"
    assert snapshot.branches[1].active is False
    assert snapshot.releases[0].latest is True
