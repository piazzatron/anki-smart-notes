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

import webbrowser
from collections.abc import Callable
from dataclasses import dataclass
from typing import Optional, Union

import aiohttp

from .app_state import app_state
from .config import config
from .constants import get_server_url, get_site_url
from .logger import logger
from .sentry import sentry
from .tasks import run_async_in_background


def open_browser(path: str) -> None:
    url = f"{get_site_url()}{with_plugin_utm_params(path)}"
    logger.info(f"Opening browser for signup: {url}")
    webbrowser.open(url, new=1)


def submit_code(
    code: str,
    on_result: Callable[[Optional[str]], None],
) -> None:
    """Exchange an auth code for a JWT. Calls on_result(None) on success,
    on_result(error_message) on failure. Runs the HTTP call in the background."""

    cleaned = code.strip().upper()
    if not cleaned:
        logger.info("Auth code submit: empty input, rejecting")
        on_result("Please enter a code.")
        return

    logger.info(f"Auth code submit: attempting exchange (code len={len(cleaned)})")

    def on_exchange_done(result: "ExchangeResult") -> None:
        if isinstance(result, ExchangeError):
            logger.warning(f"Auth code submit: exchange failed: {result.message}")
            on_result(result.message)
            return
        logger.info("Auth code submit: exchange succeeded, writing token")
        config.auth_token = result.jwt
        if sentry:
            sentry.set_user()
        app_state.update_subscription_state()
        on_result(None)

    run_async_in_background(
        lambda: exchange_code(cleaned),
        on_success=on_exchange_done,
        use_collection=False,
    )


def is_authenticated() -> bool:
    return bool(config.auth_token)


# -- Internals --


def with_plugin_utm_params(path: str) -> str:
    separator = "&" if "?" in path else "?"
    return f"{path}{separator}utm_source=ankiweb&utm_medium=plugin"


@dataclass
class ExchangeSuccess:
    jwt: str


@dataclass
class ExchangeError:
    message: str


ExchangeResult = Union[ExchangeSuccess, ExchangeError]

# Server error codes mapped to user-facing messages.
ERROR_MESSAGES = {
    "INVALID_OR_EXPIRED": "That code is invalid or has expired. Please try again.",
    "RATE_LIMITED": "Too many attempts. Please wait a minute and try again.",
}


async def exchange_code(code: str) -> ExchangeResult:
    url = f"{get_server_url()}/auth/code/exchange"
    logger.debug(f"Auth code exchange: POST {url}")
    timeout = aiohttp.ClientTimeout(total=10)
    try:
        async with (
            aiohttp.ClientSession(timeout=timeout) as session,
            session.post(
                url, json={"code": code}, headers={"x-sn-source": "anki-plugin"}
            ) as resp,
        ):
            body = await resp.json()
            logger.debug(f"Auth code exchange: response status={resp.status}")
            if resp.status != 200:
                raw = body.get("error")
                logger.warning(
                    f"Auth code exchange: server rejected with status={resp.status} error={raw}"
                )
                return ExchangeError(
                    ERROR_MESSAGES.get(raw) or raw or f"Server returned {resp.status}"
                )
            jwt = body.get("jwt")
            if not isinstance(jwt, str) or not jwt:
                logger.warning("Auth code exchange: 200 but response missing jwt field")
                return ExchangeError("Server returned an invalid response.")
            logger.debug(f"Auth code exchange: got jwt (len={len(jwt)})")
            return ExchangeSuccess(jwt)
    except Exception as e:
        logger.error(f"Auth code exchange failed: {e}")
        return ExchangeError(
            "Could not reach the Smart Notes server. Check your connection."
        )
