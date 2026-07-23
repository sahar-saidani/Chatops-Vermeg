from __future__ import annotations

import base64

from github.github_client import GitHubClient


class FakeGitHubClient(GitHubClient):
    def __post_init__(self) -> None:
        self.session = None

    def _request(self, path: str, params: dict | None = None):
        payloads = {
            "/repos/sahar-saidani/ToDoList": {
                "name": "ToDoList",
                "description": "Task list app",
                "owner": {"login": "sahar-saidani"},
                "visibility": "public",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-02-10T00:00:00Z",
                "default_branch": "main",
                "size": 100,
                "license": {"spdx_id": "MIT"},
                "html_url": "https://github.com/sahar-saidani/ToDoList",
                "stargazers_count": 10,
                "forks_count": 2,
                "subscribers_count": 3,
                "open_issues_count": 1,
                "topics": ["python"],
                "homepage": "https://example.com",
                "archived": False,
            },
            "/repos/sahar-saidani/ToDoList/languages": {"Python": 1000},
            "/repos/sahar-saidani/ToDoList/branches": [
                {"name": "main", "protected": True, "commit": {"sha": "abc123", "commit": {"committer": {"date": "2024-02-10T00:00:00Z"}}}},
            ],
            "/repos/sahar-saidani/ToDoList/commits": [{"sha": "abc123"}],
            "/repos/sahar-saidani/ToDoList/commits/abc123": {
                "sha": "abc123",
                "commit": {
                    "author": {"name": "Alice", "email": "alice@example.com", "date": "2024-02-10T00:00:00Z"},
                    "message": "Add feature",
                },
                "stats": {"additions": 10, "deletions": 2, "total": 12},
                "files": [{"filename": "app.py"}],
                "parents": [],
            },
            "/repos/sahar-saidani/ToDoList/pulls": [
                {
                    "title": "Improve UI",
                    "body": "Polish layout",
                    "user": {"login": "Alice"},
                    "state": "closed",
                    "merged_at": "2024-02-03T12:00:00Z",
                    "created_at": "2024-02-01T00:00:00Z",
                    "closed_at": "2024-02-03T12:00:00Z",
                    "requested_reviewers": [{"login": "Bob"}],
                    "comments": 2,
                    "labels": [{"name": "enhancement"}],
                }
            ],
            "/repos/sahar-saidani/ToDoList/issues": [
                {
                    "title": "Bug in validation",
                    "state": "closed",
                    "labels": [{"name": "bug"}],
                    "user": {"login": "Alice"},
                    "assignee": {"login": "Bob"},
                    "comments": 4,
                    "created_at": "2024-01-20T00:00:00Z",
                    "closed_at": "2024-01-22T12:00:00Z",
                }
            ],
            "/repos/sahar-saidani/ToDoList/releases": [
                {"tag_name": "v1.0.0", "name": "First release", "body": "Initial release", "published_at": "2024-02-01T00:00:00Z"}
            ],
            "/repos/sahar-saidani/ToDoList/branches/main": {
                "commit": {"commit": {"tree": {"sha": "tree-sha"}}}
            },
            "/repos/sahar-saidani/ToDoList/git/trees/tree-sha": {
                "tree": [
                    {"path": "README.md", "type": "blob", "size": 100},
                    {"path": "requirements.txt", "type": "blob", "size": 50},
                    {"path": ".github/workflows/ci.yml", "type": "blob", "size": 50},
                    {"path": "Dockerfile", "type": "blob", "size": 50},
                    {"path": "tests/test_app.py", "type": "blob", "size": 50},
                ]
            },
            "/repos/sahar-saidani/ToDoList/contents/requirements.txt": {
                "encoding": "base64",
                "content": base64.b64encode(b"Flask==3.0.0\n").decode("ascii"),
            },
        }
        value = payloads.get(path)
        if value is None:
            raise AssertionError(f"Unexpected path: {path}")
        return value


def test_github_client_builds_snapshot_from_mocked_responses() -> None:
    snapshot = FakeGitHubClient().get_repository_snapshot("sahar-saidani/ToDoList")

    assert snapshot.repository.name == "ToDoList"
    assert snapshot.repository.owner == "sahar-saidani"
    assert snapshot.branches[0].default_branch is True
    assert snapshot.commits[0].files_modified == ["app.py"]
    assert snapshot.contributors[0].name == "Alice"
    assert snapshot.technologies[0].name == "Python"
    assert any(dependency.name == "Flask" for dependency in snapshot.dependencies)
    assert snapshot.quality_indicators.ci_cd_configured is True
    assert snapshot.releases[0].latest is True
