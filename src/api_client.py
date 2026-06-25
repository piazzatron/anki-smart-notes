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


class ClientFacingAPIError(Exception):
    pass


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
            if response.status >= 400:
                try:
                    json = await response.json()
                except Exception:
                    json = None

                if isinstance(json, dict):
                    message = json.get("message") or json.get("error")
                    if isinstance(message, str):
                        raise ClientFacingAPIError(message)

                    if response.status == 400:
                        logger.error(json)

            response.raise_for_status()

            # Read it all into memory
            await response.read()

            return response


api = APIClient()
