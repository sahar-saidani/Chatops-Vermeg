"""HTTP client for interacting with Jenkins REST API."""

from __future__ import annotations

from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from jenkins.api import JenkinsAPI
from utils.exceptions import JenkinsHTTPError, JenkinsTimeoutError


class JenkinsClient:
    """Jenkins REST API client with authentication, timeout and retry."""

    def __init__(
        self,
        base_url: str,
        username: str,
        token: str,
        timeout: int = 15,
        retries: int = 3,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.auth = (username, token)

        retry = Retry(
            total=retries,
            connect=retries,
            read=retries,
            status=retries,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET",),
            backoff_factor=0.5,
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def _request(self, endpoint: str, expect_json: bool = True) -> Any:
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.request("GET", url, timeout=self.timeout)
            response.raise_for_status()
            if expect_json:
                return response.json()
            return response.text
        except requests.Timeout as exc:
            raise JenkinsTimeoutError(f"Timeout while calling {url}") from exc
        except requests.HTTPError as exc:
            code = exc.response.status_code if exc.response is not None else "unknown"
            body = exc.response.text if exc.response is not None else ""
            raise JenkinsHTTPError(
                f"HTTP error {code} on {url}: {body[:300]}"
            ) from exc
        except requests.RequestException as exc:
            raise JenkinsHTTPError(f"Request error on {url}: {exc}") from exc

    def get_info(self) -> dict[str, Any]:
        return self._request(JenkinsAPI.INFO)

    def get_jobs(self) -> list[dict[str, Any]]:
        data = self._request(JenkinsAPI.JOBS)
        return data.get("jobs", [])

    def get_job(self, job_name: str) -> dict[str, Any]:
        return self._request(JenkinsAPI.job(job_name))

    def get_builds(self, job_name: str) -> list[dict[str, Any]]:
        data = self._request(JenkinsAPI.builds(job_name))
        return data.get("builds", [])

    def get_build(self, job_name: str, build_number: int) -> dict[str, Any]:
        return self._request(JenkinsAPI.build(job_name, build_number))

    def get_console_logs(self, job_name: str, build_number: int) -> str:
        return self._request(JenkinsAPI.console(job_name, build_number), expect_json=False)

    def get_pipeline_status(self, job_name: str, build_number: int) -> dict[str, Any]:
        return self._request(JenkinsAPI.wfapi(job_name, build_number))
