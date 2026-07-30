from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import requests
from requests import Response

from config.settings import Settings


logger = logging.getLogger(__name__)


class JiraAPIError(RuntimeError):
    pass


@dataclass(slots=True)
class JiraConnectionInfo:
    server_version: str
    api_version: str
    authenticated_user: dict[str, Any]


class JiraClient:
    def __init__(
        self,
        base_url: str,
        email: str,
        api_token: str,
        verify_ssl: bool = True,
        api_version: str = "auto",
    ) -> None:

        self.base_url = base_url.rstrip("/")
        self.email = email
        self.api_token = api_token
        self.verify_ssl = verify_ssl
        self.api_version = api_version.lower()

        self.session = requests.Session()
        self.session.auth = (email, api_token)

        self.session.headers.update(
            {
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
        )

        self._resolved_api_version: str | None = None


    @classmethod
    def from_settings(cls, settings: Settings) -> "JiraClient":
        return cls(
            base_url=settings.jira_url,
            email=settings.jira_email,
            api_token=settings.jira_api_token,
            verify_ssl=settings.jira_verify_ssl,
            api_version=settings.jira_api_version,
        )


    @property
    def resolved_api_version(self) -> str:
        return self._resolved_api_version or (
            "3" if self.api_version == "auto" else self.api_version
        )


    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:

        url = f"{self.base_url}{path}"

        try:
            logger.info("URL        : %s", url)
            logger.info("METHOD     : %s", method)
            logger.info("EMAIL      : %s", self.email)
            logger.info("TOKEN LEN  : %d", len(self.api_token))
            logger.info("API VERSION: %s", self.resolved_api_version)
            response = self.session.request(
                method,
                url,
                params=params,
                json=json,
                timeout=30,
                verify=self.verify_ssl,
            )
            logger.info("STATUS CODE: %s", response.status_code)
            logger.info("FINAL URL  : %s", response.url)
            logger.info("BODY       : %s", response.text[:500])

        except requests.RequestException as exc:
            raise JiraAPIError(
                f"Failed to reach Jira at {url}: {exc}"
            ) from exc


        if response.status_code >= 400:
            raise JiraAPIError(
                self._format_http_error(response)
            )


        if response.status_code == 204:
            return {}


        try:
            payload = response.json()

        except ValueError as exc:
            raise JiraAPIError(
                f"Jira returned invalid JSON for {url}"
            ) from exc


        if not isinstance(payload, dict):
            raise JiraAPIError(
                f"Expected JSON object from {url}, got {type(payload).__name__}"
            )


        return payload



    def _format_http_error(self, response: Response) -> str:

        try:
            details = response.json()

        except ValueError:
            details = response.text

        return (
            f"Jira API error {response.status_code} "
            f"for {response.url}: {details}"
        )



    def _api_path(self, suffix: str) -> str:
        return f"/rest/api/{self.resolved_api_version}{suffix}"



    def _ensure_api_version(self):

        if self._resolved_api_version is not None:
            return


        if self.api_version in {"2", "3"}:
            self._resolved_api_version = self.api_version
            return


        for candidate in ("3", "2"):

            try:
                self._resolved_api_version = candidate
                self.get_myself()

                logger.info(
                    "Detected Jira API version %s",
                    candidate
                )

                return


            except JiraAPIError:
                continue


        raise JiraAPIError(
            "Unable to detect a working Jira REST API version"
        )



    def get_myself(self) -> dict[str, Any]:
        return self._request(
            "GET",
            self._api_path("/myself")
        )



    def test_connection(self) -> JiraConnectionInfo:

        self._ensure_api_version()

        myself = self.get_myself()

        return JiraConnectionInfo(
            server_version=self.base_url,
            api_version=self.resolved_api_version,
            authenticated_user=myself,
        )



    def get_project(
        self,
        project_key: str
    ) -> dict[str, Any]:

        return self._request(
            "GET",
            self._api_path(
                f"/project/{project_key}"
            )
        )



    def list_projects(self) -> list[dict[str, Any]]:

        payload = self._request(
            "GET",
            self._api_path("/project/search"),
            params={
                "maxResults": 1000
            },
        )

        return list(
            payload.get("values", [])
        )



    # ==============================
    # NEW JIRA CLOUD SEARCH API
    # ==============================

    def search_issues(
        self,
        jql: str,
        max_results: int = 100
    ) -> list[dict[str, Any]]:

        issues = []

        next_page_token = None


        while True:

            params = {

                "jql": jql,

                "maxResults": max_results,

                "fields": (
                    "summary,"
                    "description,"
                    "issuetype,"
                    "priority,"
                    "status,"
                    "creator,"
                    "assignee,"
                    "created,"
                    "updated,"
                    "labels,"
                    "components,"
                    "project,"
                    "subtasks"
                ),

                "expand": "changelog",
            }


            if next_page_token:
                params["nextPageToken"] = next_page_token



            payload = self._request(
                "GET",
                self._api_path("/search/jql"),
                params=params,
            )


            batch = payload.get(
                "issues",
                []
            )


            issues.extend(batch)


            next_page_token = payload.get(
                "nextPageToken"
            )


            if not next_page_token:
                break



        return issues



    def get_active_sprints(
        self,
        board_id: int
    ) -> list[dict[str, Any]]:


        payload = self._request(
            "GET",
            f"/rest/agile/1.0/board/{board_id}/sprint",
            params={
                "state": "active"
            },
        )

        return list(
            payload.get(
                "values",
                []
            )
        )



    def get_sprint_issues(
        self,
        sprint_id: int
    ) -> list[dict[str, Any]]:


        payload = self._request(
            "GET",
            f"/rest/agile/1.0/sprint/{sprint_id}/issue"
        )

        return list(
            payload.get(
                "issues",
                []
            )
        )



    def get_issue_changelog(
        self,
        issue_key: str
    ) -> list[dict[str, Any]]:


        payload = self._request(
            "GET",
            self._api_path(
                f"/issue/{issue_key}"
            ),
            params={
                "expand": "changelog"
            },
        )


        return list(
            payload.get(
                "changelog",
                {}
            ).get(
                "histories",
                []
            )
        )