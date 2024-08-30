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

from typing import Any

from .api_client import api
from .constants import TTS_PROVIDER_TIMEOUT_SEC
from .models import TTSModels, TTSProviders


class TTSProvider:
    async def async_get_tts_response(
        self,
        input: str,
        model: TTSModels,
        provider: TTSProviders,
        voice: str,
        options: Any = {},
        note_id: int = -1,
    ) -> bytes:

        response = await api.get_api_response(
            path="tts",
            args={
                "provider": provider,
                "model": model,
                "message": input,
                "voice": voice,
            },
            note_id=note_id,
            timeout_sec=TTS_PROVIDER_TIMEOUT_SEC,
        )
        # TODO: write it directly to a temp cache file so they're not all going into memory

        return response._body  # type: ignore
