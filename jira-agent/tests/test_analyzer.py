from __future__ import annotations

from agent.analyzer import Analyzer


def test_analyzer_statistics():
    snapshot = {
        "project": {"name": "Project A", "key": "PROJ", "description": "Demo", "project_type": "software"},
        "issues": [
            {"key": "PROJ-1", "status": "Done", "issue_type": "Story", "priority": "Medium", "assignee": "Alice", "created_at": "2026-07-01T10:00:00Z", "updated_at": "2026-07-03T10:00:00Z", "labels": [], "sprint": "Sprint 1"},
            {"key": "PROJ-2", "status": "In Progress", "issue_type": "Bug", "priority": "High", "assignee": None, "created_at": "2026-07-02T10:00:00Z", "updated_at": "2026-07-04T10:00:00Z", "labels": ["blocked"], "sprint": "Sprint 1"},
        ],
        "sprints": [{"name": "Sprint 1"}],
    }

    result = Analyzer().analyze(snapshot)

    assert result["statistics"]["total_issues"] == 2
    assert result["statistics"]["open_issues"] == 1
    assert result["statistics"]["critical_bugs"] == 1
    assert "unassigned" in result["issues_analysis"]
    assert any(risk["type"] == "blocked_issues" for risk in result["risks"])
