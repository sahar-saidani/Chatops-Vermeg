from __future__ import annotations

from pathlib import Path

from agent.reporter import ReportGenerator


def test_report_generator(tmp_path: Path):
    report = {
        "project": {"name": "Project A", "key": "PROJ", "description": "Demo"},
        "statistics": {"total_issues": 10, "open_issues": 4, "closed_issues": 6, "critical_bugs": 1, "blocked_issues": 2, "average_resolution_days": 3.5},
        "issues_analysis": {"unassigned": ["PROJ-2"], "blocked": ["PROJ-3"], "critical_bugs": ["PROJ-4"]},
        "risks": [{"type": "blocked_issues", "count": 2}],
        "recommendations": ["Assigner rapidement les tickets non assignés."],
    }

    generator = ReportGenerator()
    json_path, md_path = generator.save_reports(report, reports_dir=str(tmp_path))

    assert json_path.exists()
    assert md_path.exists()
    assert "# Jira Report" in md_path.read_text(encoding="utf-8")
