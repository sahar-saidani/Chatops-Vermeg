from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from agent.jira_client import JiraAPIError, JiraClient


def test_jira_client_connection_success(monkeypatch):
    client = JiraClient("https://example.atlassian.net", "user@example.com", "token", api_version="3")
    response = SimpleNamespace(status_code=200, url="https://example.atlassian.net/rest/api/3/myself")
    response.json = lambda: {"displayName": "Test User"}
    mock_request = Mock(return_value=response)
    monkeypatch.setattr(client.session, "request", mock_request)

    info = client.test_connection()

    assert info.api_version == "3"
    assert info.authenticated_user["displayName"] == "Test User"
    assert mock_request.called


def test_jira_client_connection_failure(monkeypatch):
    client = JiraClient("https://example.atlassian.net", "user@example.com", "token", api_version="3")
    response = SimpleNamespace(status_code=401, url="https://example.atlassian.net/rest/api/3/myself", text="Unauthorized")
    response.json = lambda: {"errorMessages": ["Unauthorized"]}
    monkeypatch.setattr(client.session, "request", Mock(return_value=response))

    with pytest.raises(JiraAPIError):
        client.test_connection()
