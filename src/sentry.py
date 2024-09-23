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
import sys
import traceback
from typing import Any, Callable, Coroutine, Dict, Union

import aiohttp
import sentry_sdk
from aqt import mw
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.session import Session

from .. import env
from .config import config
from .constants import get_server_url
from .logger import logger
from .tasks import run_async_in_background
from .ui.ui_utils import show_message_box
from .utils import get_version, is_production

dsn = os.getenv("SENTRY_DSN")


# Based on
# https://github.com/wandb/wandb/blob/2ff422b6e5f594c1e15ee03b60baba2e8a163f80/wandb/analytics/sentry.py
class Sentry:
    # For some reason, I need to not list hub here as an instance var for typechecking to work? idk

    uuid: str

    def __init__(self, dsn: str, release: str, uuid: str, env: str) -> None:
        logger.debug("Initializing sentry...")
        logger.debug(f"release: {release}, uuid: {uuid}, env: {env}")

        def before_send(event: Any, _: Dict[str, Any]) -> Union[Any, None]:
            if not is_production():
                return None

            if "logger" in event and event["logger"] != "smart_notes":
                logger.debug("Not sending event to sentry")
                return None
            logger.debug("Sending event to sentry...")
            return event

        client = sentry_sdk.Client(
            dsn=dsn,
            release=release,
            default_integrations=False,
            environment="production" if is_production() else "development",
            integrations=[LoggingIntegration(level=logging.DEBUG)],
            before_send=before_send,
        )
        hub = sentry_sdk.Hub(client)
        self.hub = hub
        self.uuid = uuid
        logger.debug("Sentry initialized...")

    def configure_scope(self) -> None:
        self._monekypatch_sys_excepthook()
        logger.debug("Configuring scope")
        with self.hub.configure_scope() as scope:
            scope.user = {"id": self.uuid}

        self._start_session()

    def _monekypatch_sys_excepthook(self) -> None:
        try:
            old_hook = sys.excepthook

            def new_hook(exc_type, exc_value, exc_traceback) -> None:
                try:
                    if is_production():
                        self.capture_exception(exc_value)
                except Exception as e:
                    logger.error(f"Error in excepthook: {e}")
                old_hook(exc_type, exc_value, exc_traceback)

            sys.excepthook = new_hook
        except Exception as e:
            logger.error(f"Error getting sys.excepthook: {e}")

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
            if not self._is_smartnotes_exception(e):
                logger.debug(f"Sentry: not capturing exception {e}")
                return

            logger.debug(f"Sentry: capturing exception {e}")
            scope.capture_exception(e)
            if scope._session:
                scope._session.update(status="crashed")
                client.flush()

    def _is_smartnotes_exception(self, e: Exception) -> bool:
        tb_str = "".join(traceback.format_exception(None, e, e.__traceback__))
        return (
            "1531888719" in tb_str
            or "smart-notes" in tb_str
            or "1531888719" in str(e)
            or "smart-notes" in str(e)
        )

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


def pinger(event: str) -> Callable[[], Coroutine[Any, Any, None]]:
    user_state = (
        "subscriber"
        if config.auth_token
        else ("legacy" if config.openai_api_key else "inactive")
    )
    ping_url = f"{get_server_url()}/ping"
    params = {
        "version": get_version(),
        "uuid": config.uuid,
        "event": event,
        "userState": user_state,
    }

    async def ping() -> None:
        try:
            # 10s timeout for users who can't connect for some reason (china/vpn etc)
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10)
            ) as session:
                async with session.get(ping_url, params=params) as response:
                    if response.status != 200:
                        logger.error(f"Error pinging server: {response.status}")
                    else:
                        logger.debug("Successfully pinged server")
        except Exception as e:
            logger.error(f"Error pinging server: {e}")

    return ping


def init_sentry() -> Union[Sentry, None]:
    try:
        if os.getenv("IS_TEST"):
            return None

        dsn = os.getenv("SENTRY_DSN")
        release = get_version()
        if not dsn or not release:
            logger.error("Sentry: no sentry DSN or release")
            return None

        sentry = Sentry(dsn, release, config.uuid, env.environment)

        return sentry
    except Exception as e:
        logger.error(f"Error initializing sentry: {e}")
        return None


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
    use_collection: bool = True,
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

    run_async_in_background(
        op, on_success, on_failure, with_progress, use_collection=use_collection
    )
