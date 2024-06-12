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

from .config import Config

import aiohttp


class OpenAIClient:
    """Client for OpenAI's chat API."""

    def __init__(self, config: Config):
        self.config = config

    async def async_get_chat_response(self, prompt: str) -> str:
        """Gets a chat response from OpenAI's chat API. This method can throw; the caller should handle with care."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.config.openai_api_key}",
                },
                json={
                    "model": self.config.openai_model,
                    "messages": [{"role": "user", "content": prompt}],
                },
            ) as response:
                response.raise_for_status()
                resp = await response.json()
                msg: str = resp["choices"][0]["message"]["content"]
                return msg
