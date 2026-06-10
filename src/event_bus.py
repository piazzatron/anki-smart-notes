"""
Copyright (C) 2024 Michael Piazza

This file is part of Smart Notes.

Smart Notes is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Smart Notes is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Smart Notes.  If not, see <https://www.gnu.org/licenses/>.
"""

import asyncio
import functools
import threading
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, TypeVar, Union


@dataclass(frozen=True)
class StateInvalidated:
    """Domain state changed. Carries no payload: consumers re-read current
    state and serialize it fresh, so producers never build wire payloads."""


@dataclass(frozen=True)
class BrowserSelectionChanged:
    """Ephemeral event with a wire-ready payload (see dto.py)."""

    payload: dict[str, Any]


WebEvent = Union[StateInvalidated, BrowserSelectionChanged]


class EventBus:
    """Thread-safe pub/sub bridging Anki's main thread to the local server's
    asyncio loop. publish() may be called from any thread; subscribers receive
    events on the asyncio queue/loop they registered with."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._subscribers: list[
            tuple[asyncio.AbstractEventLoop, asyncio.Queue[WebEvent]]
        ] = []

    def subscribe(
        self, loop: asyncio.AbstractEventLoop, queue: asyncio.Queue[WebEvent]
    ) -> None:
        with self._lock:
            self._subscribers.append((loop, queue))

    def unsubscribe(self, queue: asyncio.Queue[WebEvent]) -> None:
        with self._lock:
            self._subscribers = [
                (loop, q) for loop, q in self._subscribers if q is not queue
            ]

    def publish(self, event: WebEvent) -> None:
        with self._lock:
            subscribers = list(self._subscribers)
        for loop, queue in subscribers:
            loop.call_soon_threadsafe(queue.put_nowait, event)


event_bus = EventBus()

F = TypeVar("F", bound=Callable[..., Any])


def republish_state(fn: F) -> F:
    """Marks a function as mutating domain state the web UI renders: after it
    runs, the full state is republished to connected clients.

    The publish travels with the function, so every caller — Qt dialogs, HTTP
    commands, future code — keeps webviews live without routing through a
    dedicated write path. Redundant publishes are fine: the SSE layer
    coalesces them into a single state push."""

    @functools.wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        result = fn(*args, **kwargs)
        event_bus.publish(StateInvalidated())
        return result

    return wrapper  # type: ignore[return-value]
