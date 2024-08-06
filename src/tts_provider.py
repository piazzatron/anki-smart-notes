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
from typing import Any

import aiohttp

from .config import config
from .constants import (MAX_RETRIES, RETRY_BASE_SECONDS,
                        TTS_PROVIDER_TIMEOUT_SEC, get_server_url)
from .logger import logger
from .models import TTSModels, TTSProviders, TTSVoices

timeout = aiohttp.ClientTimeout(total=TTS_PROVIDER_TIMEOUT_SEC)


class TTSProvider:
    async def async_get_tts_response(
        self,
        input: str,
        model: TTSModels,
        provider: TTSProviders,
        voice: TTSVoices,
        options: Any = {},
        retry_count=0,
    ) -> bytes:

        # TODO: should probably extract this again so not duplicating logic between
        # chat provider
        endpoint = f"{get_server_url()}/api/tts"
        jwt = config.auth_token
        if not jwt:
            logger.error("ChatProvider: unexpectedly no JWT")
            ## TODO: raise here

        logger.debug(
            f"Making TTS request with model {model} provider: {provider} input {input} options {options}"
        )

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                endpoint,
                headers={
                    "Authorization": f"Bearer {jwt}",
                    "Content-Type": "application/json",
                },
                json={
                    "provider": provider,
                    "model": model,
                    "message": input,
                    "voice": voice,
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

                        return await self.async_get_tts_response(
                            input=input,
                            model=model,
                            provider=provider,
                            voice=voice,
                            options=options,
                            retry_count=retry_count + 1,
                        )

                # TODO: put this in chat provider too
                if response.status == 400:
                    json = await response.json()
                    print(json)
                    raise Exception(f"Validation error: {json['error']}")

                response.raise_for_status()

                # TODO: write it directly to a temp cache file so they're not all going into memory

                return await response.read()
