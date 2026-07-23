from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator


class LogstashEvent(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    timestamp: Any | None = Field(default=None, alias="@timestamp")
    message: str | None = None
    hostname: str | None = None
    service: Any | None = None
    process: Any | None = None
    severity: Any | None = None
    source: str | None = None
    tags: list[str] | str | None = None
    host: Any | None = None
    agent: Any | None = None
    event: Any | None = None
    log: Any | None = None
    fields: Any | None = None

    @field_validator("tags", mode="before")
    @classmethod
    def normalize_tags(cls, value: Any) -> list[str] | str | None:
        if value is None:
            return None
        if isinstance(value, str):
            return [value]
        if isinstance(value, list):
            return [str(item) for item in value if str(item).strip()]
        return value


class NormalizedLogEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    timestamp: datetime
    hostname: str
    service: str
    level: str
    process: str | None = None
    source: str
    message: str
    tags: list[str] = Field(default_factory=list)

    @field_serializer("timestamp")
    def serialize_timestamp(self, value: datetime) -> str:
        normalized = value.replace(tzinfo=None) if value.tzinfo is not None else value
        return normalized.isoformat(timespec="seconds")
