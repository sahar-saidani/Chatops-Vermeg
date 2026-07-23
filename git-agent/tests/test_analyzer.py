from __future__ import annotations

from agent.analyzer import RepositoryAnalyzer
from tests.helpers import build_sample_snapshot


def test_analyzer_computes_repository_metrics() -> None:
    snapshot = build_sample_snapshot()
    report = RepositoryAnalyzer(stale_branch_days=90).analyze(snapshot)

    assert report.metrics.merged_pr_count == 1
    assert report.metrics.open_pr_count == 1
    assert report.metrics.number_of_bugs == 1
    assert report.metrics.number_of_enhancements == 1
    assert report.metrics.stale_branches == 1
    assert report.metrics.top_contributors[0].name == "Alice"
    assert report.health_score.score <= 100
    assert report.health_score.breakdown["ci_cd"] == 15
