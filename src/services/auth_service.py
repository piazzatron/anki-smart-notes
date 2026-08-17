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

"""
Authentication actions for the plugin.

Exchanges a browser-issued single-use code for a token from the Smart Notes
server, refreshes the account's subscription and usage, and logs out by
clearing the token and projecting the signed-out state.
"""

from typing import Any

import aiohttp

from ..app_state import app_state
from ..config import config
from ..constants import get_server_url
from ..logger import logger
from ..sentry import sentry

AUTH_CODE_ERROR_MESSAGES = {
    "INVALID_OR_EXPIRED": "That code is invalid or has expired. Please try again.",
    "RATE_LIMITED": "Too many attempts. Please wait a minute and try again.",
}


async def exchange_auth_code(code: str) -> str:
    """Exchange a browser-issued, single-use code for an authentication token."""
    try:
        async with (
            aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session,
            session.post(
                f"{get_server_url()}/auth/code/exchange",
                json={"code": code},
                headers={"x-sn-source": "anki-plugin"},
            ) as response,
        ):
            body: Any = await response.json()
    except (aiohttp.ClientError, TimeoutError) as error:
        logger.error(f"Auth code exchange failed: {error}")
        raise RuntimeError(
            "Could not reach the Smart Notes server. Check your connection."
        ) from error

    if response.status != 200:
        error_code = body.get("error") if isinstance(body, dict) else None
        if isinstance(error_code, str):
            raise ValueError(AUTH_CODE_ERROR_MESSAGES.get(error_code, error_code))
        raise ValueError(f"Server returned {response.status}")

    jwt = body.get("jwt") if isinstance(body, dict) else None
    if not isinstance(jwt, str) or not jwt:
        raise RuntimeError("Server returned an invalid response.")
    return jwt


def refresh_account() -> None:
    """Fetch the latest subscription and credit usage from the API."""
    app_state.update_account_state()


def logout() -> None:
    """Clear authentication and immediately project the signed-out state."""
    config.auth_token = None
    if sentry:
        sentry.set_user()
    app_state.update_account_state()
