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

from typing import Any, Literal, Optional

import aiohttp
from aiohttp import ClientResponse

from .config import config
from .constants import get_server_url
from .logger import logger
from .utils import get_version


class OutOfCreditsError(Exception):
    pass


class UserDisplayableError(Exception):
    """A 4xx server rejection whose message is written for the user.

    The server decides which failures users should see (moderation blocks,
    plan restrictions, input too long, rate limits) by returning a 4xx with a
    JSON `message` or `error` string. Callers show that message and treat the
    failure as expected, so it is logged below error level and never reported
    to Sentry. 5xx responses are server failures and raise `ServerError`
    instead, even when they carry a message.
    """

    def __init__(self, message: str, *, status: int) -> None:
        super().__init__(message)
        self.status = status


class ServerError(Exception):
    """A 5xx server failure, worded generically so it is safe to show users.

    Unlike `UserDisplayableError`, this is an unexpected failure and callers
    report it.
    """

    def __init__(self, *, status: int, path: str) -> None:
        super().__init__("Something went wrong. Please try again soon.")
        self.status = status
        self.path = path


class APIClient:
    async def get_api_response(
        self,
        path: str,
        args: Optional[dict[str, Any]] = None,
        timeout_sec: Optional[int] = None,
        note_id: Optional[int] = None,
        method: Literal["GET", "POST"] = "POST",
    ) -> ClientResponse:
        if args is None:
            args = {}
        endpoint = f"{get_server_url()}/api/{path}"
        jwt = config.auth_token
        if not jwt:
            logger.error("APIClient: unexpectedly no JWT")
            raise Exception("User is not authenticated! Please sign up or log in")

        logger.debug(f"Making request to {path} with args {args}")

        if timeout_sec:
            timeout = aiohttp.ClientTimeout(total=timeout_sec)
        else:
            timeout = aiohttp.ClientTimeout(total=10)

        headers = {
            "Authorization": f"Bearer {jwt}",
            "Content-Type": "application/json",
            "x-sn-plugin-version": get_version(),
            "x-sn-source": "anki-plugin",
        }

        if note_id is not None:
            headers["Note-ID"] = f"{note_id}"

        async with (
            aiohttp.ClientSession() as session,
            (session.get if method == "GET" else session.post)(
                endpoint,
                headers=headers,
                json=args,
                timeout=timeout,
            ) as response,
        ):
            if response.status == 429:
                logger.warning("Got a 429 from server")

            logger.debug(f"Got response from {path}: {response.status}")
            if response.status == 402:
                raise OutOfCreditsError()
            if response.status == 401:
                response.raise_for_status()
            if response.status >= 500:
                raise ServerError(status=response.status, path=path)
            if response.status >= 400:
                try:
                    json = await response.json()
                except Exception:
                    json = None

                if isinstance(json, dict):
                    message = json.get("message") or json.get("error")
                    if isinstance(message, str):
                        raise UserDisplayableError(message, status=response.status)

                    if response.status == 400:
                        logger.error(json)

            response.raise_for_status()

            # Read it all into memory
            await response.read()

            return response


api = APIClient()
