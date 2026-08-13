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
    tenant: str | None
    agent_keys: list[str]
    user_message: str
    assistant_response: str
    environment: str | None = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ConversationHistoryClient:
    """Persists conversation turns via the Spring Boot REST API.

    The endpoint is ``POST /api/v1/conversations``, backed by
    ``com.vermeg.chatops.conversation``. It is restricted to trusted backend
    callers, which the orchestrator proves with the ``X-Internal-Api-Key``
    header (Spring reads the expected value from ``chatops.internal.api-key``
    / ``INTERNAL_API_KEY``). The two sides must be configured with the same
    secret; when ``INTERNAL_API_KEY`` is unset here the request is still
    attempted and Spring answers 403, which -- like any other failure -- is
    logged and swallowed so a history outage never fails the user's request.
    """

    def __init__(self, settings: Settings, session: requests.Session | None = None):
        self._base_url = settings.spring_api_base_url
        self._api_key = settings.internal_api_key
        self._session = session or requests.Session()

    def save(self, turn: ConversationTurn) -> bool:
        url = f"{self._base_url}/api/v1/conversations"
        headers = {"X-Internal-Api-Key": self._api_key} if self._api_key else {}
        try:
            response = self._session.post(
                url,
                json=asdict(turn),
                headers=headers,
                timeout=10,
            )
            response.raise_for_status()
            return True
        except requests.RequestException as exc:
            logger.warning(
                "Could not persist conversation turn via Spring Boot API (%s). "
                "The response was still returned to the user. Error: %s",
                url, exc,
            )
            return False
