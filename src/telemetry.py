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

from typing import Any, Optional

from .api_client import api
from .config import config
from .logger import logger
from .tasks import run_async_in_background


def track_event(event: str, properties: Optional[dict[str, Any]] = None) -> None:
    """
    Fire-and-forget client-side telemetry.

    Posts to /api/events on the server, which validates and forwards to Amplitude.
    Identity is resolved server-side from the authenticated user. Properties must
    match the server-side schema for the event (see metrics/events.ts).

    Silently no-ops if the user isn't signed in. Errors are swallowed so the UI
    is never disrupted by telemetry.
    """
    if not config.auth_token:
        return

    body: dict[str, Any] = {"event": event}
    if properties is not None:
        body["properties"] = properties

    async def send() -> None:
        await api.get_api_response(path="events", args=body, method="POST")

    run_async_in_background(
        send,
        on_failure=lambda e: logger.debug(f"telemetry: {event} failed: {e}"),
    )
