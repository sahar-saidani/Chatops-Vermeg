from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone

import requests

from config import Settings

logger = logging.getLogger(__name__)


@dataclass
class ConversationTurn:
    user_id: str
    request_mode: str
    agent_keys: list[str]
    user_message: str
    assistant_response: str
    environment: str | None = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ConversationHistoryClient:
    """Persists conversation turns via the Spring Boot REST API.

    NOTE - integration gap: as of this change, ``com.vermeg.chatops`` has no
    ``conversation`` package or ``conversation_history`` table/migration yet
    (only ``canonical_events`` and the identity/access/audit tables exist).
    This client is written against the contract the architecture specifies
    ("Conversation History" is explicitly a Java Spring Boot responsibility)
    so the orchestrator is ready the moment that endpoint exists. Until then,
    calls degrade to a logged warning instead of failing the user's request.
    """

    def __init__(self, settings: Settings, session: requests.Session | None = None):
        self._base_url = settings.spring_api_base_url
        self._session = session or requests.Session()

    def save(self, turn: ConversationTurn) -> bool:
        url = f"{self._base_url}/api/v1/conversations"
        try:
            response = self._session.post(url, json=asdict(turn), timeout=10)
            response.raise_for_status()
            return True
        except requests.RequestException as exc:
            logger.warning(
                "Could not persist conversation turn via Spring Boot API (%s). "
                "The response was still returned to the user. Error: %s",
                url, exc,
            )
            return False
