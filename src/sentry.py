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

import logging
import os
import random
from typing import Any, Callable, Coroutine, Union

import aiohttp
import sentry_sdk
from aqt import mw
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.session import Session

from .. import env
from .config import config
from .constants import get_server_url
from .logger import logger
from .ui.changelog import get_version
from .ui.ui_utils import show_message_box
from .utils import is_production, run_async_in_background

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
        logger.debug("Initializing sentry...")
        logger.debug(f"DSN: {dsn}, release: {release}, uuid: {uuid}, env: {env}")
        client = sentry_sdk.Client(
            dsn=dsn,
            release=release,
            default_integrations=False,
            environment="production" if is_production() else "development",
            integrations=[LoggingIntegration(level=logging.DEBUG)],
        )
        hub = sentry_sdk.Hub(client)
        self.hub = hub
        self.uuid = uuid
        logger.debug("Sentry initialized...")

    def configure_scope(self) -> None:
        logger.debug("Configuring scope")
        with self.hub.configure_scope() as scope:
            scope.user = {"id": self.uuid}

        self._start_session()

    def end_session(self) -> None:
        logger.debug("Sentry: ending session")
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
                if is_production():
                    logger.debug(f"Sentry: capturing exception {e}")

                    self.capture_exception(e)
                    self._show_error_message(e)
                else:
                    raise e

        return wrapped

    def wrap(self, fn: Callable[..., Any]) -> Any:
        def wrapped(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except Exception as e:
                if is_production():
                    logger.debug(f"Sentry: capturing exception {e}")
                    self.capture_exception(e)
                    self._show_error_message(e)
                else:
                    raise e

        return wrapped

    def _get_session(self) -> Union[Session, None]:
        _, scope = self.hub._stack[-1]
        return scope._session

    def _start_session(self) -> None:
        session = self._get_session()
        if session is None:
            self.hub.start_session()

            client, scope = self.hub._stack[-1]
            session = scope._session
            if client and session:
                client.capture_session(session)
                client.flush()

    def _show_error_message(self, e: Exception) -> None:
        if not mw:
            return
        # Show the error message on the main thread
        mw.taskman.run_on_main(
            lambda: show_message_box("Smart Notes has encountered an error", str(e))
        )


async def ping() -> None:
    try:
        ping_url = f"{get_server_url()}/ping"
        params = {"version": get_version(), "uuid": config.uuid}
        async with aiohttp.ClientSession() as session:
            async with session.get(ping_url, params=params) as response:
                if response.status != 200:
                    logger.error(f"Error pinging server: {response.status}")
                else:
                    logger.debug("Successfully pinged server")
    except Exception as e:
        logger.error(f"Error pinging server: {e}")


def init_sentry() -> Union[Sentry, None]:
    dsn = os.getenv("SENTRY_DSN")
    release = get_version()
    if not dsn or not release:
        logger.error("Sentry: no sentry DSN or release")
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


def run_async_in_background_with_sentry(
    op: Callable[[], Any],
    on_success: Callable[[Any], None],
    on_failure: Union[Callable[[Exception], None], None] = None,
    with_progress: bool = False,
):
    "Runs an async operation in the background and calls on_success when done."

    if not mw:
        raise Exception("Error: mw not found in run_async_in_background")

    # Wrap for sentry error reporting
    if sentry:
        op = sentry.wrap_async(op)
        on_success = sentry.wrap(on_success)
        if on_failure:
            on_failure = sentry.wrap(on_failure)

    run_async_in_background(op, on_success, on_failure, with_progress)
