from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from config import Settings

logger = logging.getLogger(__name__)

# Matches src/main/resources/db/migration/V6__create_canonical_events_table.sql
_SELECT_COLUMNS = (
    "id, agent_key, message_timestamp, environment, data, created_at"
)


@dataclass(frozen=True)
class CanonicalEvent:
    id: str
    agent_key: str
    message_timestamp: datetime
    environment: str
    data: dict
    created_at: datetime


class CanonicalEventsRepository:
    """Read-only access to the canonical_events table."""

    def __init__(self, settings: Settings, engine: Engine | None = None):
        self._settings = settings
        self._engine = engine or create_engine(
            settings.database_url,
            pool_pre_ping=True,
        )

    def find_recent(
        self,
        agent_keys: list[str],
        since: datetime | None = None,
        environment: str | None = None,
        tenant: str | None = None,
        limit: int = 200,
    ) -> list[CanonicalEvent]:

        if not agent_keys:
            return []

        clauses = ["agent_key = ANY(:agent_keys)"]
        params = {
            "agent_keys": agent_keys,
            "limit": limit,
        }

        if since is not None:
            clauses.append("message_timestamp >= :since")
            params["since"] = since

        if environment:
            clauses.append("LOWER(environment) = LOWER(:environment)")
            params["environment"] = environment

        if tenant:
            clauses.append("LOWER(tenant) = LOWER(:tenant)")
            params["tenant"] = tenant

        sql = (
            f"SELECT {_SELECT_COLUMNS} "
            "FROM canonical_events "
            f"WHERE {' AND '.join(clauses)} "
            "ORDER BY message_timestamp DESC "
            "LIMIT :limit"
        )

        logger.info("====================================================")
        logger.info("DATABASE URL : %s", self._settings.database_url)
        logger.info("SQL          : %s", sql)
        logger.info("PARAMS       : %s", params)
        logger.info("====================================================")

        with self._engine.connect() as conn:
            rows = conn.execute(text(sql), params).mappings().all()

        logger.info("Returned %d rows", len(rows))

        if rows:
            logger.info("First row : %s", rows[0])

        return [self._to_event(row) for row in rows]

    def wait_for_fresh_data(
        self,
        agent_key: str,
        since: datetime,
        environment: str | None = None,
        tenant: str | None = None,
        timeout_seconds: int | None = None,
        poll_interval_seconds: int | None = None,
    ) -> CanonicalEvent | None:
        """Wait until a fresh canonical event appears."""

        timeout = (
            timeout_seconds
            or self._settings.agent_fresh_data_timeout_seconds
        )

        interval = (
            poll_interval_seconds
            or self._settings.agent_fresh_data_poll_interval_seconds
        )

        deadline = time.monotonic() + timeout

        while time.monotonic() < deadline:
            events = self.find_recent(
                [agent_key],
                since=since,
                environment=environment,
                tenant=tenant,
                limit=1,
            )

            if events:
                return events[0]

            time.sleep(interval)

        logger.warning(
            "Timed out after %ss waiting for fresh canonical_events data from agent '%s'",
            timeout,
            agent_key,
        )

        return None

    @staticmethod
    def _to_event(row) -> CanonicalEvent:
        return CanonicalEvent(
            id=str(row["id"]),
            agent_key=row["agent_key"],
            message_timestamp=row["message_timestamp"],
            environment=row["environment"],
            data=row["data"],
            created_at=row["created_at"],
        )


def utcnow() -> datetime:
    return datetime.now(timezone.utc)