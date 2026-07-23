"""Unit tests for JenkinsClient."""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest
import requests

from jenkins.jenkins_client import JenkinsClient
from utils.exceptions import JenkinsHTTPError, JenkinsTimeoutError


@patch("requests.Session.request")
def test_get_jobs_success(mock_request: Mock) -> None:
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = {"jobs": [{"name": "ToDoList-CI"}]}
    mock_request.return_value = response

    client = JenkinsClient("http://localhost:8080", "user", "token")
    jobs = client.get_jobs()

    assert len(jobs) == 1
    assert jobs[0]["name"] == "ToDoList-CI"


@patch("requests.Session.request")
def test_invalid_token_raises_http_error(mock_request: Mock) -> None:
    response = Mock()
    response.raise_for_status.side_effect = requests.HTTPError(response=Mock(status_code=401, text="Unauthorized"))
    mock_request.return_value = response

    client = JenkinsClient("http://localhost:8080", "user", "bad-token")

    with pytest.raises(JenkinsHTTPError):
        client.get_jobs()


@patch("requests.Session.request")
def test_timeout_raises_timeout_error(mock_request: Mock) -> None:
    mock_request.side_effect = requests.Timeout("Timeout")

    client = JenkinsClient("http://localhost:8080", "user", "token")

    with pytest.raises(JenkinsTimeoutError):
        client.get_jobs()


@patch("requests.Session.request")
def test_http_error_raises_custom_error(mock_request: Mock) -> None:
    response = Mock()
    response.raise_for_status.side_effect = requests.HTTPError(response=Mock(status_code=500, text="Server Error"))
    mock_request.return_value = response

    client = JenkinsClient("http://localhost:8080", "user", "token")

    with pytest.raises(JenkinsHTTPError):
        client.get_job("ToDoList-CI")
