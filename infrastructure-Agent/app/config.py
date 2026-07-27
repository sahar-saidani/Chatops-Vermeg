"""Application configuration helpers for the health monitoring MVP."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


@dataclass(slots=True)
class Settings:
	"""Runtime settings loaded from environment variables and .env files."""

	prometheus_url: str = "http://127.0.0.1:9090"
	prometheus_timeout_seconds: float = 10.0
	log_level: str = "INFO"
	log_file: str = "logs/infrastructure_agent.log"
	target_name: str = "CentOS VM"
    rabbitmq_url: str | None = None

	@classmethod
	def from_env(cls) -> "Settings":
		"""Build settings from environment variables and .env files."""

		defaults = cls()
		return cls(
			prometheus_url=os.getenv("PROMETHEUS_URL", defaults.prometheus_url),
			prometheus_timeout_seconds=float(
				os.getenv("PROMETHEUS_TIMEOUT_SECONDS", str(defaults.prometheus_timeout_seconds))
			),
			log_level=os.getenv("LOG_LEVEL", defaults.log_level),
			log_file=os.getenv("LOG_FILE", defaults.log_file),
			target_name=os.getenv("TARGET_NAME", defaults.target_name),
            rabbitmq_url=os.getenv("RABBITMQ_URL") or None,
		)


def ensure_log_directory(log_file: str) -> None:
	"""Create the parent directory for the configured log file."""

	Path(log_file).parent.mkdir(parents=True, exist_ok=True)


def resolve_project_path(relative_path: str) -> Path:
	"""Resolve a path relative to the project root unless it is already absolute."""

	path = Path(relative_path)
	if path.is_absolute():
		return path
	return Path(__file__).resolve().parents[1] / path
