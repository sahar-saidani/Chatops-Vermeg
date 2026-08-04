from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

THIS_DIR = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Settings:
    """Runtime configuration for the LLM Orchestrator.

    Loaded once from the environment (.env supported), the same convention
    used by every existing collection agent's ``Settings.from_env()``.
    """

    # PostgreSQL - read canonical_events, mirrors the Spring Boot datasource
    postgres_host: str
    postgres_port: int
    postgres_db: str
    postgres_user: str
    postgres_password: str

    # Spring Boot REST API - conversation history is a Java responsibility;
    # the orchestrator persists conversations through this API, it never
    # writes conversation rows to PostgreSQL directly.
    spring_api_base_url: str

    # OpenRouter API (OpenAI-compatible) - used for the final NL answer, and
    # as an intent-detection fallback when the rule-based classifier is not
    # confident.
    openrouter_api_key: str | None
    openrouter_base_url: str
    openrouter_model: str

    # Freshness wait after launching agents (Mode 1)
    agent_fresh_data_timeout_seconds: int
    agent_fresh_data_poll_interval_seconds: int

    # subprocess execution timeout per agent invocation
    agent_subprocess_timeout_seconds: int

    # Root directory that contains git-agent/, jenkins-agent/, etc.
    agents_root_dir: Path

    # Tenant-to-machine routing registry used by the orchestrator.
    tenant_machine_registry_path: Path
    default_tenant: str | None

    log_level: str

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @classmethod
    def from_env(cls) -> "Settings":
        agents_root = Path(os.getenv("AGENTS_ROOT_DIR", str(THIS_DIR.parent))).resolve()
        tenant_registry_path = Path(
            os.getenv(
                "TENANT_MACHINE_REGISTRY_PATH",
                str(THIS_DIR / "config" / "tenant_machines.yml"),
            )
        ).resolve()

        return cls(
            postgres_host=os.getenv("POSTGRES_HOST", "localhost"),
            postgres_port=int(os.getenv("POSTGRES_PORT", "5432")),
            postgres_db=os.getenv("POSTGRES_DB", "chatops"),
            postgres_user=os.getenv("POSTGRES_USER", "postgres"),
            postgres_password=os.getenv("POSTGRES_PASSWORD", ""),
            spring_api_base_url=os.getenv("SPRING_API_BASE_URL", "http://localhost:8080").rstrip("/"),
            openrouter_api_key=os.getenv("OPENROUTER_API_KEY") or None,
            openrouter_base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
            openrouter_model=os.getenv("OPENROUTER_MODEL", "openai/gpt-oss-20b:free"),
            agent_fresh_data_timeout_seconds=int(os.getenv("AGENT_FRESH_DATA_TIMEOUT_SECONDS", "60")),
            agent_fresh_data_poll_interval_seconds=int(
                os.getenv("AGENT_FRESH_DATA_POLL_INTERVAL_SECONDS", "2")
            ),
            agent_subprocess_timeout_seconds=int(os.getenv("AGENT_SUBPROCESS_TIMEOUT_SECONDS", "300")),
            agents_root_dir=agents_root,
            tenant_machine_registry_path=tenant_registry_path,
            default_tenant=(os.getenv("DEFAULT_TENANT") or None),
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings.from_env()
