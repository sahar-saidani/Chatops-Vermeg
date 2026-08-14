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
    """Runtime configuration for the LLM Orchestrator."""

    # PostgreSQL
    postgres_host: str
    postgres_port: int
    postgres_db: str
    postgres_user: str
    postgres_password: str

    # Spring Boot
    spring_api_base_url: str
    # Shared secret sent as X-Internal-Api-Key on service-to-service calls;
    # must match Spring's chatops.internal.api-key.
    internal_api_key: str | None

    # OpenRouter API
    openrouter_api_key: str | None
    openrouter_base_url: str
    openrouter_model: str
    openrouter_fallback_model: str

    # Agent freshness
    agent_fresh_data_timeout_seconds: int
    agent_fresh_data_poll_interval_seconds: int

    # Agent subprocess
    agent_subprocess_timeout_seconds: int

    # Agents
    agents_root_dir: Path

    # Tenant routing
    tenant_machine_registry_path: Path
    default_tenant: str | None

    # Browser origins allowed to call this API directly (the chat UI talks to
    # the orchestrator, not just to Spring). Same variable Spring reads, so
    # there is one place to configure both.
    cors_allowed_origins: list[str]

    log_level: str

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @classmethod
    def from_env(cls) -> "Settings":
        agents_root = Path(
            os.getenv(
                "AGENTS_ROOT_DIR",
                str(THIS_DIR.parent),
            )
        ).resolve()

        tenant_registry_path = Path(
            os.getenv(
                "TENANT_MACHINE_REGISTRY_PATH",
                str(THIS_DIR / "config" / "tenant_machines.yml"),
            )
        ).resolve()

        return cls(
            # PostgreSQL
            postgres_host=os.getenv(
                "POSTGRES_HOST",
                "localhost",
            ),
            postgres_port=int(
                os.getenv(
                    "POSTGRES_PORT",
                    "5432",
                )
            ),
            postgres_db=os.getenv(
                "POSTGRES_DB",
                "chatops",
            ),
            postgres_user=os.getenv(
                "POSTGRES_USER",
                "postgres",
            ),
            postgres_password=os.getenv(
                "POSTGRES_PASSWORD",
                "",
            ),

            # Spring Boot
            spring_api_base_url=os.getenv(
                "SPRING_API_BASE_URL",
                "http://localhost:8080",
            ).rstrip("/"),

            internal_api_key=(
                os.getenv("INTERNAL_API_KEY") or None
            ),

            # OpenRouter
            openrouter_api_key=(
                os.getenv("OPENROUTER_API_KEY") or None
            ),

            openrouter_base_url=os.getenv(
                "OPENROUTER_BASE_URL",
                "https://openrouter.ai/api/v1",
            ).rstrip("/"),

            openrouter_model=os.getenv(
                "OPENROUTER_MODEL",
                "nvidia/nemotron-3-ultra-550b-a55b:free",
            ),

            openrouter_fallback_model=os.getenv(
                "OPENROUTER_FALLBACK_MODEL",
                "openai/gpt-oss-20b:free",
            ),

            # Agent freshness
            agent_fresh_data_timeout_seconds=int(
                os.getenv(
                    "AGENT_FRESH_DATA_TIMEOUT_SECONDS",
                    "60",
                )
            ),

            agent_fresh_data_poll_interval_seconds=int(
                os.getenv(
                    "AGENT_FRESH_DATA_POLL_INTERVAL_SECONDS",
                    "2",
                )
            ),

            # Agent subprocess
            agent_subprocess_timeout_seconds=int(
                os.getenv(
                    "AGENT_SUBPROCESS_TIMEOUT_SECONDS",
                    "300",
                )
            ),

            # Agents
            agents_root_dir=agents_root,

            # Tenant routing
            tenant_machine_registry_path=tenant_registry_path,

            default_tenant=(
                os.getenv("DEFAULT_TENANT") or None
            ),

            # CORS - same default pair Spring's CorsProperties uses.
            cors_allowed_origins=[
                origin.strip()
                for origin in os.getenv(
                    "CORS_ALLOWED_ORIGINS",
                    "http://localhost:5173,http://localhost:8443",
                ).split(",")
                if origin.strip()
            ],

            # Logging
            log_level=os.getenv(
                "LOG_LEVEL",
                "INFO",
            ).upper(),
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings.from_env()