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
from typing import Any, Dict, Literal, Union

import aiohttp
from aiohttp import ClientResponse

from .config import config
from .constants import MAX_RETRIES, RETRY_BASE_SECONDS, get_server_url
from .logger import logger


class APIClient:

    async def get_api_response(
        self,
        path: str,
        args: Dict[str, Any] = {},
        timeout_sec: Union[int, None] = None,
        retry_count: int = 0,
        note_id: Union[int, None] = None,
        method: Literal["GET", "POST"] = "POST",
    ) -> ClientResponse:
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

        headers = {"Authorization": f"Bearer {jwt}", "Content-Type": "application/json"}

        if note_id is not None:
            headers["Note-ID"] = f"{note_id}"

        async with aiohttp.ClientSession() as session:
            async with (session.get if method == "GET" else session.post)(
                endpoint,
                headers=headers,
                json=args,
                timeout=timeout,
            ) as response:
                if response.status == 429:
                    logger.warning("Got a 429 from server")
                    if retry_count < MAX_RETRIES:
                        wait_time = (2**retry_count) * RETRY_BASE_SECONDS
                        logger.debug(
                            f"Retry: {retry_count} Waiting {wait_time} seconds before retrying"
                        )
                        await asyncio.sleep(wait_time)

                        return await self.get_api_response(
                            path=path,
                            args=args,
                            timeout_sec=timeout_sec,
                            retry_count=retry_count + 1,
                            note_id=note_id,
                            method=method,
                        )

                logger.debug(f"Got response from {path}: {response.status}")
                if response.status == 400:
                    json = await response.json()
                    logger.error(json)
                    raise Exception(f"Validation error: {json['error']}")
                response.raise_for_status()

                # Read it all into memory
                await response.read()

                return response


api = APIClient()
