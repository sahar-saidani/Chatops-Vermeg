from __future__ import annotations

from pathlib import Path

import main as main_module
from agent.git_agent import GitRepositoryAgent
from config.settings import Settings
from tests.helpers import build_sample_report, build_sample_snapshot


class FakeCollector:
    def __init__(self, snapshot) -> None:
        self.snapshot = snapshot

    def collect(self):
        return self.snapshot


class FakeAnalyzer:
    def __init__(self, *args, **kwargs) -> None:
        self.args = args
        self.kwargs = kwargs

    def analyze(self, snapshot):
        return build_sample_report(source=snapshot.source)


class FakeReportGenerator:
    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir

    def generate(self, report):
        self.output_dir.mkdir(parents=True, exist_ok=True)
        return {}


def test_git_repository_agent_uses_local_collector(monkeypatch, tmp_path) -> None:
    snapshot = build_sample_snapshot(source="local")
    monkeypatch.setattr("agent.git_agent.LocalRepositoryCollector", lambda repository_path, settings: FakeCollector(snapshot))
    monkeypatch.setattr("agent.git_agent.RepositoryAnalyzer", FakeAnalyzer)
    monkeypatch.setattr("agent.git_agent.ReportGenerator", FakeReportGenerator)

    report = GitRepositoryAgent(Settings(output_dir=tmp_path)).analyze(path=tmp_path)

    assert report.snapshot.source == "local"
    assert report.health_score.score == 76


def test_main_cli_analyze_returns_zero(monkeypatch, tmp_path) -> None:
    class FakeAgent:
        def __init__(self, settings):
            self.settings = settings

        def analyze(self, path=None, repo=None):
            return build_sample_report(source="github" if repo else "local")

    monkeypatch.setattr(main_module, "GitRepositoryAgent", FakeAgent)

    exit_code = main_module.main(["analyze", "--repo", "sahar-saidani/ToDoList", "--output", str(tmp_path)])

    assert exit_code == 0
