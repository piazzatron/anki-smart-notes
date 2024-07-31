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

from typing import Any, Union

from anki.notes import Note
from aqt import mw

from .chat_provider import ChatProvider
from .constants import DEFAULT_TEMPERATURE
from .logger import logger
from .models import ChatModels, ChatProviders, TTSModels, TTSProviders, TTSVoices
from .nodes import ChatPayload, FieldNode, TTSPayload
from .notes import get_note_type
from .open_ai_client import OpenAIClient
from .prompts import interpolate_prompt
from .tts_provider import TTSProvider
from .utils import is_legacy_open_ai


class FieldResolver:

    def __init__(
        self,
        openai_provider: OpenAIClient,
        chat_provider: ChatProvider,
        tts_provider: TTSProvider,
    ):
        self.openai_provider = openai_provider
        self.chat_provider = chat_provider
        self.tts_provider = tts_provider

    async def resolve(self, node: FieldNode, note: Note) -> Union[str, None]:
        payload = node.payload

        if isinstance(payload, TTSPayload):
            if not mw:
                return None
            media = mw.col.media
            if not media:
                logger.error("No media")
                return None

            tts_response = await self.get_tts_response(
                note=note,
                input_text=payload.input,
                model=payload.model,
                voice=payload.voice,
                provider=payload.provider,
                options=payload.options,
            )

            note_type = get_note_type(note)
            file_name = f"{note_type}-{node.field}-{note.id}.mp3"
            path = media.write_data(file_name, tts_response)

            return f"[sound:{path}]"

        elif isinstance(node.payload, ChatPayload):
            return await self.get_chat_response(
                note=note,
                prompt=payload.prompt,
                model=payload.model,
                provider=payload.provider,
                temperature=payload.temperature,
            )

        else:
            logger.error(f"Unexpected payload type {type(payload)}")
            return None

    async def get_chat_response(
        self,
        note: Note,
        prompt: str,
        model: ChatModels,
        provider: ChatProviders,
        temperature: int = DEFAULT_TEMPERATURE,
    ) -> Union[str, None]:

        interpolated_prompt = interpolate_prompt(prompt, note)

        if not interpolated_prompt:
            return None

        if is_legacy_open_ai():
            return await self.openai_provider.async_get_chat_response(
                interpolated_prompt, temperature=temperature, retry_count=0
            )

        return await self.chat_provider.async_get_chat_response(
            interpolated_prompt,
            model=model,
            provider=provider,
            temperature=temperature,
        )

    async def get_tts_response(
        self,
        note: Note,
        input_text: str,
        model: TTSModels,
        provider: TTSProviders,
        voice: TTSVoices,
        options: Any,
    ):

        interpolated_prompt = interpolate_prompt(input_text, note)

        if not interpolated_prompt:
            return None

        logger.debug(f"Resolving: {interpolated_prompt}")
        return await self.tts_provider.async_get_tts_response(
            input=interpolated_prompt,
            model=model,
            provider=provider,
            options=options,
            voice=voice,
        )
