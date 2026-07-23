from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ReportGenerator:
    def generate(self, snapshot: dict[str, Any], analysis: dict[str, Any]) -> dict[str, Any]:
        return {
            "project": analysis.get("project") or snapshot.get("project") or {},
            "statistics": analysis.get("statistics", {}),
            "issues_analysis": analysis.get("issues_analysis", {}),
            "risks": analysis.get("risks", []),
            "recommendations": analysis.get("recommendations", []),
        }

    def save_reports(self, report: dict[str, Any], reports_dir: str = "reports") -> tuple[Path, Path]:
        output_dir = Path(reports_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        json_path = output_dir / "jira_report.json"
        md_path = output_dir / "jira_report.md"

        json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        md_path.write_text(self._to_markdown(report), encoding="utf-8")
        return json_path, md_path

    def _to_markdown(self, report: dict[str, Any]) -> str:
        project = report.get("project", {})
        statistics = report.get("statistics", {})
        issues = report.get("issues_analysis", {})
        risks = report.get("risks", [])
        recommendations = report.get("recommendations", [])

        lines = [
            "# Jira Report",
            "",
            "## Résumé projet",
            f"- Nom: {project.get('name', 'N/A')}",
            f"- Clé: {project.get('key', 'N/A')}",
            f"- Description: {project.get('description', 'N/A')}",
            "",
            "## Métriques importantes",
            f"- Tickets totaux: {statistics.get('total_issues', 0)}",
            f"- Tickets ouverts: {statistics.get('open_issues', 0)}",
            f"- Tickets fermés: {statistics.get('closed_issues', 0)}",
            f"- Bugs critiques: {statistics.get('critical_bugs', 0)}",
            f"- Tickets bloqués: {statistics.get('blocked_issues', 0)}",
            f"- Temps moyen de résolution (jours): {statistics.get('average_resolution_days', 'N/A')}",
            "",
            "## Problèmes détectés",
        ]
        if risks:
            for risk in risks:
                lines.append(f"- {risk}")
        else:
            lines.append("- Aucun risque majeur détecté")

        lines.extend([
            "",
            "## Tickets sensibles",
            f"- Non assignés: {issues.get('unassigned', [])}",
            f"- Bloqués: {issues.get('blocked', [])}",
            f"- Bugs critiques: {issues.get('critical_bugs', [])}",
            "",
            "## Recommandations",
        ])
        for recommendation in recommendations:
            lines.append(f"- {recommendation}")
        return "\n".join(lines) + "\n"
