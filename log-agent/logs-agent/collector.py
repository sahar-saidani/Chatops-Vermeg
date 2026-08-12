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

        self._items.append(
            _SeenItem(
                key=key,
                created_at=now,
            )
        )

        self._index.add(key)

        return False

    def _purge(self, now: float) -> None:
        while (
            self._items
            and now - self._items[0].created_at > self._window_seconds
        ):
            item = self._items.popleft()
            self._index.discard(item.key)


class LogCollector:
    """
    Collects normalized log events received from Logstash.
    """

    def __init__(
        self,
        config: AppConfig,
        logger: Any,
        identity: Any = None,
    ) -> None:
        self._config = config
        self._logger = logger
        self._identity = identity

        self._parser = LogParser(config.normalization)

        self._duplicates = DuplicateDetector(
            config.normalization.dedup_window_seconds
        )

        self._server: asyncio.base_events.Server | None = None

        self._publisher = None

        if config.rabbitmq.enabled:
            from rabbitmq_publisher import RabbitMqPublisher

            self._publisher = RabbitMqPublisher(
                url=config.rabbitmq.url
            )

        self.collected_events: list[dict[str, Any]] = []

        self._clients: set[asyncio.StreamWriter] = set()

    async def run(
        self,
        duration_seconds: float | None = None,
    ) -> None:
        """
        Start the Logstash receiver.

        duration_seconds=None:
            Run continuously.

        duration_seconds=N:
            Run for N seconds and then stop.
        """

        self._server = await asyncio.start_server(
            self._handle_client,
            host=self._config.server.host,
            port=self._config.server.port,
            limit=max(
                65536,
                self._config.normalization.max_message_length * 2,
            ),
        )

        sockets = self._server.sockets or []

        addresses = ", ".join(
            str(socket.getsockname())
            for socket in sockets
        )

        self._logger.info(
            "logs_agent_started",
            host=self._config.server.host,
            port=self._config.server.port,
            sockets=addresses,
            duration_seconds=duration_seconds,
        )

        async with self._server:
            if duration_seconds is None:
                await self._server.serve_forever()
                return

            duration_seconds = max(
                1.0,
                float(duration_seconds),
            )

            self._logger.info(
                "logs_agent_bounded_run_started",
                duration_seconds=duration_seconds,
            )

            serve_task = asyncio.create_task(
                self._server.serve_forever()
            )

            try:
                await asyncio.sleep(duration_seconds)

            finally:
                # Stop accepting new connections first, then force-close
                # any still-open client connections (e.g. a persistent
                # Logstash beats->tcp output) *before* wait_closed().
                #
                # Since Python 3.12, Server.wait_closed() blocks until
                # every active connection handled by this server has
                # finished, not just until the listening socket closes.
                # A client that never disconnects on its own (Logstash
                # keeps its TCP output connection open indefinitely)
                # would otherwise make wait_closed() hang forever,
                # regardless of --duration.
                self._server.close()
                await self._close_clients()
                await self._server.wait_closed()

                serve_task.cancel()

                with contextlib.suppress(asyncio.CancelledError):
                    await serve_task

                self._logger.info(
                    "logs_agent_bounded_run_completed",
                    duration_seconds=duration_seconds,
                    events_collected=len(self.collected_events),
                )

    async def _handle_client(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        print(">>> _handle_client CALLED")
        peer = writer.get_extra_info("peername")
        self._clients.add(writer)
        self._logger.info("client_connected", peer=str(peer))

        buffer = b""
        try:
            while True:
                chunk = await reader.read(4096)
                if not chunk:
                    break
                buffer += chunk
                # Découper les lignes
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    if line:
                        await self._process_line(line + b"\n")
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            self._logger.error("client_error", peer=str(peer), error=str(exc))
        finally:
            self._clients.discard(writer)
            writer.close()
            with contextlib.suppress(Exception):
                await writer.wait_closed()
            self._logger.info("client_disconnected", peer=str(peer))

    async def _close_clients(self) -> None:
        if not self._clients:
            return

        clients = list(self._clients)

        for writer in clients:
            writer.close()

        for writer in clients:
            with contextlib.suppress(Exception):
                await writer.wait_closed()

        self._clients.clear()

    async def _process_line(
        self,
        raw_line: bytes,
    ) -> None:
        self._logger.debug(
            "_process_line CALLED",
            raw_line_preview=raw_line[:100],
        )

        if not raw_line.strip():
            self._logger.debug("_process_line: empty line (only whitespace)")
            return

        decoded = raw_line.decode(
            "utf-8",
            errors="replace",
        ).strip()

        try:
            payload = json.loads(decoded)

        except json.JSONDecodeError:
            self._logger.warning(
                "malformed_json",
                sample=decoded[:256],
            )
            return

        if not isinstance(payload, dict):
            self._logger.warning(
                "unexpected_payload_type",
                payload_type=type(payload).__name__,
            )
            return

        if self._duplicates.seen(payload):
            self._logger.debug(
                "duplicate_log_skipped"
            )
            return

        try:
            normalized = self._parser.parse(payload)

        except Exception as exc:
            self._logger.error(
                "normalization_failed",
                error=str(exc),
            )
            return

        event_data = normalized.model_dump(
            mode="json"
        )

        self._logger.debug(
            "log_normalized",
            normalized_event=event_data,
        )

        self.collected_events.append(event_data)

        if self._publisher is not None:
            try:
                self._publisher.publish(
                    agent_key="log",
                    data=event_data,
                    identity=self._identity,
                )

            except Exception as exc:
                self._logger.error(
                    "rabbitmq_publish_failed",
                    error=str(exc),
                )