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

from .api_client import api
from .constants import CHAT_CLIENT_TIMEOUT_SEC, DEFAULT_TEMPERATURE
from .logger import logger
from .models import ChatModels, ChatProviders


class ChatProvider:

    async def async_get_chat_response(
        self,
        prompt: str,
        model: ChatModels,
        provider: ChatProviders,
        note_id: int,
        temperature=DEFAULT_TEMPERATURE,
    ) -> str:
        response = await api.get_api_response(
            path="chat",
            args={
                "provider": provider,
                "model": model,
                "message": prompt,
                "temperature": temperature,
            },
            note_id=note_id,
            timeout_sec=CHAT_CLIENT_TIMEOUT_SEC,
        )

        resp = await response.json()
        if not len(resp["messages"]):
            logger.debug(f"Empty response from chat provider {provider}")
            return ""
        return resp["messages"][0]  # type: ignore
