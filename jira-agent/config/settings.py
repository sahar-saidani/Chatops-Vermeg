from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    jira_url: str
    jira_email: str
    jira_api_token: str
    jira_project_key: str | None = None
    jira_verify_ssl: bool = True
    jira_api_version: str = "auto"
    reports_dir: str = "reports"
    data_dir: str = "data"
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> "Settings":
        jira_url = os.getenv("JIRA_URL", "").strip()
        jira_email = os.getenv("JIRA_EMAIL", "").strip()
        jira_api_token = os.getenv("JIRA_API_TOKEN", "").strip()

        if not jira_url:
            raise ValueError("JIRA_URL is required")
        if not jira_email:
            raise ValueError("JIRA_EMAIL is required")
        if not jira_api_token:
            raise ValueError("JIRA_API_TOKEN is required")

        return cls(
            jira_url=jira_url.rstrip("/"),
            jira_email=jira_email,
            jira_api_token=jira_api_token,
            jira_project_key=os.getenv("JIRA_PROJECT_KEY") or None,
            jira_verify_ssl=os.getenv("JIRA_VERIFY_SSL", "true").strip().lower() in {"1", "true", "yes", "y"},
            jira_api_version=os.getenv("JIRA_API_VERSION", "auto").strip().lower(),
            reports_dir=os.getenv("REPORTS_DIR", "reports").strip(),
            data_dir=os.getenv("DATA_DIR", "data").strip(),
            log_level=os.getenv("LOG_LEVEL", "INFO").strip().upper(),
        )

    def ensure_directories(self) -> None:
        Path(self.reports_dir).mkdir(parents=True, exist_ok=True)
        Path(self.data_dir).mkdir(parents=True, exist_ok=True)
