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

import os
from aqt import mw
import sentry_sdk
from sentry_sdk.session import Session
import random
from typing import Union, Callable, Any, Coroutine

from .ui.ui_utils import show_message_box

from .ui.changelog import get_version
from .. import env
from .config import config

dsn = os.getenv("SENTRY_DSN")


def make_uuid() -> str:
    letters = "abcdefghijklmnopqrstuvwxyz1234567890"
    uuid = []
    for _ in range(16):
        uuid.append(random.choice(letters))
    return "".join(uuid)


# Based on
# https://github.com/wandb/wandb/blob/2ff422b6e5f594c1e15ee03b60baba2e8a163f80/wandb/analytics/sentry.py
class Sentry:
    # For some reason, I need to not list hub here as an instance var for typechecking to work? idk

    uuid: str

    def __init__(self, dsn: str, release: str, uuid: str, env: str) -> None:
        print("Initializing sentry...")
        print(f"DSN: {dsn}, release: {release}, uuid: {uuid}, env: {env}")
        client = sentry_sdk.Client(
            dsn=dsn,
            release=release,
            default_integrations=False,
            environment="development" if env == "DEV" else "production",
        )
        hub = sentry_sdk.Hub(client)
        self.hub = hub
        self.uuid = uuid
        print("Sentry initialized...")

    def configure_scope(self) -> None:
        with self.hub.configure_scope() as scope:
            scope.user = {"id": self.uuid}

        client, _ = self.hub._stack[-1]
        self._start_session()
        if client:
            client.flush()

    def end_session(self) -> None:
        print("Sentry: ending session")
        client, scope = self.hub._stack[-1]
        session = scope._session

        if session is not None and client is not None:
            self.hub.end_session()
            client.flush()

    def capture_exception(self, e: Exception) -> None:
        client, scope = self.hub._stack[-1]
        if scope and client:
            scope.capture_exception(e)
            if scope._session:
                scope._session.update(status="crashed")
                client.flush()

    def wrap_async(
        self, fn: Callable[..., Any]
    ) -> Callable[[], Coroutine[Any, Any, Any]]:
        async def wrapped(*args, **kwargs):
            try:
                return await fn(*args, **kwargs)
            except Exception as e:
                print(f"Sentry: capturing exception {e}")
                self.capture_exception(e)
                self._show_error_message(e)

        return wrapped

    def wrap(self, fn: Callable[..., Any]) -> Any:
        def wrapped(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except Exception as e:
                print(f"Sentry: capturing exception {e}")
                self.capture_exception(e)
                self._show_error_message(e)

        return wrapped

    def _get_session(self) -> Union[Session, None]:
        _, scope = self.hub._stack[-1]
        return scope._session

    def _start_session(self) -> None:
        session = self._get_session()
        if session is None:
            self.hub.start_session()

    def _show_error_message(self, e: Exception) -> None:
        if not mw:
            return
        # Show the error message on the main thread
        mw.taskman.run_on_main(
            lambda: show_message_box("Smart Notes has encountered an error", str(e))
        )


def init_sentry() -> Union[Sentry, None]:
    dsn = os.getenv("SENTRY_DSN")
    release = get_version()
    if not dsn or not release:
        print("Sentry: no sentry DSN or release")
        return None

    if not config.uuid:
        config.uuid = make_uuid()

    sentry = Sentry(dsn, release, config.uuid, env.environment)

    return sentry


def with_sentry(fn: Callable[..., Any]) -> Callable[..., Any]:
    def wrapper(*args, **kwargs):
        if not sentry:
            return fn(*args, **kwargs)
        return sentry.wrap(fn)(*args, **kwargs)

    return wrapper


sentry = init_sentry()
