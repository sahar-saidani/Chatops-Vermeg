from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any

from agent.models import AnalyzerOutput


class Analyzer:
    def analyze(self, snapshot: dict[str, Any]) -> dict[str, Any]:
        issues = snapshot.get("issues", [])
        project = snapshot.get("project") or {}
        sprints = snapshot.get("sprints", [])

        total_issues = len(issues)
        open_issues = [issue for issue in issues if (issue.get("status") or "").lower() not in {"done", "closed", "resolved"}]
        closed_issues = [issue for issue in issues if issue not in open_issues]
        critical_bugs = [issue for issue in issues if (issue.get("issue_type") or "").lower() == "bug" and (issue.get("priority") or "").lower() in {"highest", "high", "critical"}]
        blocked_issues = [issue for issue in issues if self._is_blocked(issue)]
        unassigned = [issue for issue in issues if not issue.get("assignee")]

        issues_by_owner = Counter(issue.get("assignee") or "Unassigned" for issue in issues)
        open_by_owner = Counter(issue.get("assignee") or "Unassigned" for issue in open_issues)
        avg_resolution_days = self._average_resolution_days(issues)
        velocity = self._estimate_velocity(sprints, issues)
        sprint_progress = self._sprint_progress(sprints, issues)
        risks = self._detect_risks(issues, blocked_issues, critical_bugs, unassigned, open_by_owner)

        output = AnalyzerOutput(
            project={
                "name": project.get("name"),
                "key": project.get("key"),
                "description": project.get("description"),
                "type": project.get("project_type"),
            },
            statistics={
                "total_issues": total_issues,
                "open_issues": len(open_issues),
                "closed_issues": len(closed_issues),
                "critical_bugs": len(critical_bugs),
                "blocked_issues": len(blocked_issues),
                "average_resolution_days": avg_resolution_days,
                "issues_per_developer": dict(issues_by_owner),
                "load_per_member": dict(open_by_owner),
                "sprint_progress": sprint_progress,
                "team_velocity": velocity,
            },
            issues_analysis={
                "unassigned": [issue.get("key") for issue in unassigned],
                "blocked": [issue.get("key") for issue in blocked_issues],
                "critical_bugs": [issue.get("key") for issue in critical_bugs],
                "open_by_owner": dict(open_by_owner),
            },
            risks=risks,
            recommendations=self._recommendations(risks, blocked_issues, unassigned, avg_resolution_days),
        )
        return output.to_dict()

    def _is_blocked(self, issue: dict[str, Any]) -> bool:
        status = (issue.get("status") or "").lower()
        labels = {label.lower() for label in issue.get("labels", [])}
        return status == "blocked" or "blocked" in labels

    def _average_resolution_days(self, issues: list[dict[str, Any]]) -> float | None:
        durations = []
        for issue in issues:
            created = issue.get("created_at")
            updated = issue.get("updated_at")
            status = (issue.get("status") or "").lower()
            if not created or not updated or status not in {"done", "closed", "resolved"}:
                continue
            try:
                created_dt = self._parse_datetime(created)
                updated_dt = self._parse_datetime(updated)
            except ValueError:
                continue
            durations.append((updated_dt - created_dt).total_seconds() / 86400)
        if not durations:
            return None
        return round(sum(durations) / len(durations), 2)

    def _estimate_velocity(self, sprints: list[dict[str, Any]], issues: list[dict[str, Any]]) -> float | None:
        completed = [issue for issue in issues if (issue.get("status") or "").lower() in {"done", "closed", "resolved"}]
        if not sprints:
            return float(len(completed)) if completed else None
        completed_count = len(completed)
        return round(completed_count / max(len(sprints), 1), 2)

    def _sprint_progress(self, sprints: list[dict[str, Any]], issues: list[dict[str, Any]]) -> dict[str, Any]:
        if not sprints:
            return {"current": None, "completion_rate": None}
        current = sprints[0]
        sprint_issues = [issue for issue in issues if issue.get("sprint") == current.get("name")]
        if not sprint_issues:
            return {"current": current.get("name"), "completion_rate": 0.0}
        completed = [issue for issue in sprint_issues if (issue.get("status") or "").lower() in {"done", "closed", "resolved"}]
        return {
            "current": current.get("name"),
            "completion_rate": round((len(completed) / len(sprint_issues)) * 100, 2),
        }

    def _detect_risks(
        self,
        issues: list[dict[str, Any]],
        blocked_issues: list[dict[str, Any]],
        critical_bugs: list[dict[str, Any]],
        unassigned: list[dict[str, Any]],
        open_by_owner: Counter[str],
    ) -> list[dict[str, Any]]:
        risks: list[dict[str, Any]] = []
        if unassigned:
            risks.append({"type": "unassigned_work", "count": len(unassigned), "severity": "medium"})
        if blocked_issues:
            risks.append({"type": "blocked_issues", "count": len(blocked_issues), "severity": "high"})
        if critical_bugs:
            risks.append({"type": "critical_bugs", "count": len(critical_bugs), "severity": "high"})
        overloaded = [owner for owner, count in open_by_owner.items() if owner != "Unassigned" and count >= max(5, len(issues) // 3 or 1)]
        if overloaded:
            risks.append({"type": "developer_overload", "owners": overloaded, "severity": "medium"})
        return risks

    def _recommendations(
        self,
        risks: list[dict[str, Any]],
        blocked_issues: list[dict[str, Any]],
        unassigned: list[dict[str, Any]],
        avg_resolution_days: float | None,
    ) -> list[str]:
        recommendations: list[str] = []
        if unassigned:
            recommendations.append("Assigner rapidement les tickets non assignés pour réduire le temps de prise en charge.")
        if blocked_issues:
            recommendations.append("Examiner les tickets bloqués et lever les dépendances prioritaires.")
        if avg_resolution_days is not None and avg_resolution_days > 7:
            recommendations.append("Réduire le temps moyen de résolution en renforçant le triage et la priorisation.")
        if any(risk.get("type") == "developer_overload" for risk in risks):
            recommendations.append("Rééquilibrer la charge pour éviter la saturation d’un membre de l’équipe.")
        if not recommendations:
            recommendations.append("Le projet ne montre pas de risque majeur immédiat; continuer la surveillance des indicateurs clés.")
        return recommendations

    def _parse_datetime(self, value: str) -> datetime:
        normalized = value.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized).astimezone(timezone.utc)
