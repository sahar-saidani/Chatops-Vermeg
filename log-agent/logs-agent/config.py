from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field

from machine_identity import MachineIdentityConfig


class ServerConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    host: str = "0.0.0.0"
    port: int = 5000


class NormalizationConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_message_length: int = 8192
    dedup_window_seconds: int = 5


class LoggingConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    level: str = "INFO"


class RabbitMqConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    url: str = "amqp://guest:guest@localhost:5672/"


class AppConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    server: ServerConfig = Field(default_factory=ServerConfig)
    normalization: NormalizationConfig = Field(default_factory=NormalizationConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    rabbitmq: RabbitMqConfig = Field(default_factory=RabbitMqConfig)
    machine: MachineIdentityConfig = Field(default_factory=MachineIdentityConfig)


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_config(config_path: str | Path | None = None) -> AppConfig:
    path = Path(config_path) if config_path is not None else Path(__file__).with_name("config.yaml")
    if path.is_file():
        raw_data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    else:
        raw_data = {}

    if not isinstance(raw_data, dict):
        raise ValueError(f"Configuration file must contain a mapping: {path}")

    defaults = AppConfig().model_dump()
    merged = _deep_merge(defaults, raw_data)
    config = AppConfig.model_validate(merged)

    config.machine = config.machine.with_env_overrides()
    config.machine.validate_complete()

    return config