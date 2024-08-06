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

import aiohttp

from .config import config
from .constants import (
    CHAT_CLIENT_TIMEOUT_SEC,
    DEFAULT_TEMPERATURE,
    MAX_RETRIES,
    RETRY_BASE_SECONDS,
    get_server_url,
)
from .logger import logger
from .models import ChatModels, ChatProviders

timeout = aiohttp.ClientTimeout(total=CHAT_CLIENT_TIMEOUT_SEC)


class ChatProvider:

    async def async_get_chat_response(
        self,
        prompt: str,
        model: ChatModels,
        provider: ChatProviders,
        temperature=DEFAULT_TEMPERATURE,
        retry_count=0,
    ) -> str:
        endpoint = f"{get_server_url()}/api/chat"
        jwt = config.auth_token
        if not jwt:
            logger.error("ChatProvider: unexpectedly no JWT")
            ## TODO: raise here

        logger.debug(
            f"Making chat request with model {model} provider: {provider} prompt {prompt} temperature {temperature}"
        )

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                endpoint,
                headers={
                    "Authorization": f"Bearer {jwt}",
                },
                json={
                    "provider": provider,
                    "model": model,
                    "temperature": temperature,
                    "message": prompt,
                },
            ) as response:

                if response.status == 429:
                    logger.warning("Got a 429 from server")
                    if retry_count < MAX_RETRIES:
                        wait_time = (2**retry_count) * RETRY_BASE_SECONDS
                        logger.debug(
                            f"Retry: {retry_count} Waiting {wait_time} seconds before retrying"
                        )
                        await asyncio.sleep(wait_time)

                        return await self.async_get_chat_response(
                            prompt,
                            model=model,
                            provider=provider,
                            retry_count=retry_count + 1,
                        )

                if response.status == 400:
                    json = await response.json()
                    print(json)
                    raise Exception(f"Validation error: {json['error']}")

                response.raise_for_status()
                resp = await response.json()
                msg: str = resp["messages"][0]
                return msg
