from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv


@dataclass(slots=True)
class Settings:
    output_dir: Path = Path("reports")
    github_token: str | None = None
    stale_branch_days: int = 90
    active_window_days: int = 30
    request_timeout_seconds: int = 30
    per_page: int = 100
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"
    rabbitmq_enabled: bool = True

    @classmethod
    def from_env(
        cls,
        *,
        output_dir: Path | None = None,
        github_token: str | None = None,
        stale_branch_days: int = 90,
        active_window_days: int = 30,
    ) -> "Settings":
        load_dotenv()
        return cls(
            output_dir=output_dir or Path("reports"),
            github_token=github_token or os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN"),
            stale_branch_days=stale_branch_days,
            active_window_days=active_window_days,
            rabbitmq_url=os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/"),
            rabbitmq_enabled=os.getenv("RABBITMQ_ENABLED", "true").lower() == "true",
        )