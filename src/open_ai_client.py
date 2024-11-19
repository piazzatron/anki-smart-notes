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
)
from .logger import logger
from .models import openai_chat_models

OPENAI_ENDPOINT = "https://api.openai.com"


timeout = aiohttp.ClientTimeout(total=CHAT_CLIENT_TIMEOUT_SEC)


class OpenAIClient:
    """Client for OpenAI's chat API."""

    async def async_get_chat_response(
        self, prompt: str, temperature=DEFAULT_TEMPERATURE, retry_count=0
    ) -> str:
        """Gets a chat response from OpenAI's chat API. This method can throw; the caller should handle with care."""
        endpoint = f"{config.openai_endpoint or OPENAI_ENDPOINT}/v1/chat/completions"

        # Extra defensive: ensure that the chat model is valid
        chat_model = config.chat_model
        if chat_model not in openai_chat_models:
            logger.error(f"Unexpected non-openAI chat model: {chat_model}")
            chat_model = "gpt-4o-mini"

        logger.debug(
            f"OpenAI: hitting {endpoint} model: {chat_model} retries {retry_count} for prompt: {prompt}"
        )
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                endpoint,
                headers={
                    "Authorization": f"Bearer {config.openai_api_key}",
                },
                json={
                    "model": chat_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": temperature,
                },
            ) as response:
                if response.status == 429:
                    logger.debug("Got a 429 from OpenAI")
                    if retry_count < MAX_RETRIES:
                        wait_time = (2**retry_count) * RETRY_BASE_SECONDS
                        logger.debug(
                            f"Retry: {retry_count} Waiting {wait_time} seconds before retrying"
                        )
                        await asyncio.sleep(wait_time)

                        return await self.async_get_chat_response(
                            prompt, retry_count + 1
                        )

                response.raise_for_status()
                resp = await response.json()
                msg: str = resp["choices"][0]["message"]["content"]
                logger.debug(f"Got response from OpenAI: {msg}")
                return msg


openai_provider = OpenAIClient()
