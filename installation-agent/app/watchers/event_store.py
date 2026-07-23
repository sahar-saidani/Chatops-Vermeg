from __future__ import annotations

from datetime import datetime
from threading import Lock
from typing import List

from app.models.schemas import WatchdogEvent

_events: List[WatchdogEvent] = []
_lock = Lock()


def record_watchdog_event(event_type: str, path: str, is_directory: bool = False, timestamp: str | None = None) -> WatchdogEvent:
    event = WatchdogEvent(
        timestamp=timestamp or datetime.utcnow().isoformat() + "Z",
        event_type=event_type,
        path=path,
        is_directory=is_directory,
    )
    with _lock:
        _events.append(event)
    return event


def get_watchdog_events() -> List[WatchdogEvent]:
    with _lock:
        return list(_events)


def clear_watchdog_events() -> None:
    with _lock:
        _events.clear()
