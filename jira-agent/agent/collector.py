from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from agent.jira_client import JiraClient
from agent.models import JiraIssue, JiraProject, JiraSnapshot, JiraWorkflow, utc_now_iso
from config.settings import Settings


class JiraCollector:
    def __init__(self, client: JiraClient, settings: Settings) -> None:
        self.client = client
        self.settings = settings
        self.data_dir = Path(settings.data_dir)
        self.reports_dir = Path(settings.reports_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_settings(cls, settings: Settings) -> "JiraCollector":
        return cls(JiraClient.from_settings(settings), settings)

    def collect_project_snapshot(self) -> dict[str, Any]:
        project_key = self.settings.jira_project_key
        if not project_key:
            raise ValueError("JIRA_PROJECT_KEY is required for collection")
        print(f"PROJECT KEY = [{project_key}]")
        print(f"PROJECT KEY BYTES = {list(project_key.encode())}")
        project_raw = self.client.get_project(project_key)
        project = JiraProject(
            key=project_raw.get("key", project_key),
            name=project_raw.get("name", project_key),
            description=project_raw.get("description"),
            project_type=project_raw.get("projectTypeKey"),
        )

        issues_raw = self.client.search_issues(f'project = "{project_key}" ORDER BY created DESC')
        issues = [self._parse_issue(issue) for issue in issues_raw]

        workflow = self._build_workflow(issues_raw)
        sprints = self._build_sprints(issues_raw)

        snapshot = JiraSnapshot(
            collected_at=utc_now_iso(),
            project=project,
            projects=[project],
            issues=issues,
            sprints=sprints,
            workflow=workflow,
            raw={"project": project_raw, "issues": issues_raw},
        )
        return self._snapshot_to_dict(snapshot)

    def save_snapshot(self, payload: dict[str, Any]) -> Path:
        path = self.data_dir / "jira_snapshot.json"
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return path

    def load_snapshot(self) -> dict[str, Any] | None:
        path = self.data_dir / "jira_snapshot.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def save_analysis(self, payload: dict[str, Any]) -> Path:
        path = self.data_dir / "jira_analysis.json"
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return path

    def _parse_issue(self, issue: dict[str, Any]) -> JiraIssue:
        fields = issue.get("fields", {})
        return JiraIssue(
            id=str(issue.get("id", "")),
            key=issue.get("key", ""),
            title=fields.get("summary", ""),
            description=fields.get("description"),
            issue_type=(fields.get("issuetype") or {}).get("name"),
            priority=(fields.get("priority") or {}).get("name"),
            status=(fields.get("status") or {}).get("name"),
            creator=((fields.get("creator") or {}).get("displayName") or (fields.get("creator") or {}).get("name")),
            assignee=((fields.get("assignee") or {}).get("displayName") or (fields.get("assignee") or {}).get("name")),
            created_at=fields.get("created"),
            updated_at=fields.get("updated"),
            labels=list(fields.get("labels") or []),
            components=[component.get("name") for component in (fields.get("components") or []) if component.get("name")],
            sprint=self._extract_sprint_name(fields),
            history=list(issue.get("changelog", {}).get("histories", [])),
        )

    def _extract_sprint_name(self, fields: dict[str, Any]) -> str | None:
        sprint_value = fields.get("customfield_10020") or fields.get("sprint")
        if isinstance(sprint_value, dict):
            return sprint_value.get("name")
        if isinstance(sprint_value, list) and sprint_value:
            first = sprint_value[-1]
            if isinstance(first, dict):
                return first.get("name")
        if isinstance(sprint_value, str):
            return sprint_value
        return None

    def _build_workflow(self, issues_raw: list[dict[str, Any]]) -> JiraWorkflow:
        statuses: list[str] = []
        transitions: list[dict[str, Any]] = []
        for issue in issues_raw:
            for history in issue.get("changelog", {}).get("histories", []):
                for item in history.get("items", []):
                    if item.get("field") == "status":
                        statuses.extend([item.get("fromString"), item.get("toString")])
                        transitions.append({
                            "issue": issue.get("key"),
                            "from": item.get("fromString"),
                            "to": item.get("toString"),
                            "at": history.get("created"),
                        })
        return JiraWorkflow(statuses=sorted({status for status in statuses if status}), transitions=transitions)

    def _build_sprints(self, issues_raw: list[dict[str, Any]]) -> list[Any]:
        sprint_map: dict[str, dict[str, Any]] = {}
        for issue in issues_raw:
            fields = issue.get("fields", {})
            sprint_name = self._extract_sprint_name(fields)
            if not sprint_name:
                continue
            sprint_map.setdefault(
                sprint_name,
                {
                    "id": sprint_name,
                    "name": sprint_name,
                    "state": "active",
                    "issues": [],
                },
            )
            sprint_map[sprint_name]["issues"].append(issue.get("key"))

        return [
            {
                "id": sprint["id"],
                "name": sprint["name"],
                "state": sprint.get("state"),
                "goal": sprint.get("goal"),
                "start_date": sprint.get("start_date"),
                "end_date": sprint.get("end_date"),
                "complete_date": sprint.get("complete_date"),
                "velocity": sprint.get("velocity"),
                "progress": sprint.get("progress"),
                "issues": sprint.get("issues", []),
            }
            for sprint in sprint_map.values()
        ]

    def _snapshot_to_dict(self, snapshot: JiraSnapshot) -> dict[str, Any]:
        return {
            "collected_at": snapshot.collected_at,
            "project": asdict(snapshot.project) if snapshot.project else None,
            "projects": [asdict(project) for project in snapshot.projects],
            "issues": [asdict(issue) for issue in snapshot.issues],
            "sprints": snapshot.sprints,
            "workflow": asdict(snapshot.workflow) if snapshot.workflow else None,
            "raw": snapshot.raw,
        }
