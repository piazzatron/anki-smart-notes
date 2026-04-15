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
from typing import Optional

import aiohttp

from .app_state import app_state
from .config import config
from .constants import get_server_url, get_site_url
from .logger import logger
from .sentry import sentry
from .tasks import run_async_in_background


def start_browser_signup(path: str) -> None:
    """Open the system browser to the given site path. No query params."""
    url = f"{get_site_url()}{path}"
    logger.info(f"Opening browser for signup: {url}")
    webbrowser.open_new_tab(url)


def submit_code(
    code: str,
    on_result: Callable[[Optional[str]], None],
) -> None:
    """Exchange an auth code for a JWT. Calls on_result(None) on success,
    on_result(error_message) on failure. Runs the HTTP call in the background."""

    cleaned = code.strip().upper()
    if not cleaned:
        on_result("Please enter a code.")
        return

    async def do_exchange() -> Optional[str]:
        url = f"{get_server_url()}/auth/code/exchange"
        timeout = aiohttp.ClientTimeout(total=10)
        try:
            async with (
                aiohttp.ClientSession(timeout=timeout) as session,
                session.post(url, json={"code": cleaned}) as resp,
            ):
                body = await resp.json()
                if resp.status != 200:
                    return body.get("error") or f"Server returned {resp.status}"
                jwt = body.get("jwt")
                if not isinstance(jwt, str) or not jwt:
                    return "Server returned an invalid response."
                return jwt
        except Exception as e:
            logger.error(f"Auth code exchange failed: {e}")
            return "Could not reach the Smart Notes server. Check your connection."

    def on_success(result: Optional[str]) -> None:
        if result is None:
            on_result("Unexpected error.")
            return
        # If result is a JWT it won't match known error codes.
        if result == "INVALID_OR_EXPIRED":
            on_result("That code is invalid or has expired. Please try again.")
            return
        if result == "RATE_LIMITED":
            on_result("Too many attempts. Please wait a minute and try again.")
            return
        if result.count(".") != 2 or len(result) < 20:
            # Treat as error string, not a JWT
            on_result(result)
            return
        config.auth_token = result
        if sentry:
            sentry.set_user()
        app_state.update_subscription_state()
        on_result(None)

    run_async_in_background(do_exchange, on_success=on_success, use_collection=False)


def is_authenticated() -> bool:
    return bool(config.auth_token)
