from __future__ import annotations

import asyncio
import contextlib
import json
import time
from collections import deque
from dataclasses import dataclass
from typing import Any

from config import AppConfig
from parser import LogParser
from utils import dedup_key


@dataclass(slots=True)
class _SeenItem:
    key: str
    created_at: float


class DuplicateDetector:
    def __init__(self, window_seconds: int) -> None:
        self._window_seconds = max(1, window_seconds)
        self._items: deque[_SeenItem] = deque()
        self._index: set[str] = set()

    def seen(self, payload: dict[str, Any]) -> bool:
        now = time.monotonic()
        self._purge(now)
        key = dedup_key(payload)
        if key in self._index:
            return True
        self._items.append(_SeenItem(key=key, created_at=now))
        self._index.add(key)
        return False

    def _purge(self, now: float) -> None:
        while self._items and now - self._items[0].created_at > self._window_seconds:
            item = self._items.popleft()
            self._index.discard(item.key)


class LogCollector:
    def __init__(self, config: AppConfig, logger: Any, identity: Any = None) -> None:
        self._config = config
        self._logger = logger
        self._identity = identity
        self._parser = LogParser(config.normalization)
        self._duplicates = DuplicateDetector(config.normalization.dedup_window_seconds)
        self._server: asyncio.base_events.Server | None = None
        self._publisher = None
        if config.rabbitmq.enabled:
            from rabbitmq_publisher import RabbitMqPublisher

            self._publisher = RabbitMqPublisher(url=config.rabbitmq.url)

    async def run(self) -> None:
        self._server = await asyncio.start_server(
            self._handle_client,
            host=self._config.server.host,
            port=self._config.server.port,
            limit=max(65536, self._config.normalization.max_message_length * 2),
        )

        sockets = self._server.sockets or []
        addresses = ", ".join(str(socket.getsockname()) for socket in sockets)
        self._logger.info("logs_agent_started", host=self._config.server.host, port=self._config.server.port, sockets=addresses)

        async with self._server:
            await self._server.serve_forever()

    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        peer = writer.get_extra_info("peername")
        self._logger.info("client_connected", peer=str(peer))
        try:
            while True:
                raw_line = await reader.readline()
                if not raw_line:
                    break
                await self._process_line(raw_line)
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # pragma: no cover - defensive
            self._logger.error("client_error", peer=str(peer), error=str(exc))
        finally:
            writer.close()
            with contextlib.suppress(Exception):
                await writer.wait_closed()
            self._logger.info("client_disconnected", peer=str(peer))

    async def _process_line(self, raw_line: bytes) -> None:
        if not raw_line.strip():
            return

        decoded = raw_line.decode("utf-8", errors="replace").strip()
        try:
            payload = json.loads(decoded)
        except json.JSONDecodeError:
            self._logger.warning("malformed_json", sample=decoded[:256])
            return

        if not isinstance(payload, dict):
            self._logger.warning("unexpected_payload_type", payload_type=type(payload).__name__)
            return

        if self._duplicates.seen(payload):
            self._logger.debug("duplicate_log_skipped")
            return

        try:
            normalized = self._parser.parse(payload)
        except Exception as exc:  # pragma: no cover - defensive
            self._logger.error("normalization_failed", error=str(exc))
            return

        event_data = normalized.model_dump(mode="json")
        self._logger.debug("log_normalized", event=event_data)

        if self._publisher is not None:
            try:
                self._publisher.publish(agent_key="log", data=event_data, identity=self._identity)
            except Exception as exc:  # pragma: no cover - defensive
                self._logger.error("rabbitmq_publish_failed", error=str(exc))