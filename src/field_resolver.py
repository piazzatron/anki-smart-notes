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

from typing import Optional, Union

import marko
from anki.decks import DeckId
from anki.notes import Note
from aqt import mw

from .app_state import (
    has_api_key,
    is_app_unlocked,
    is_at_text_capacity,
    is_at_voice_capacity,
)
from .chat_provider import ChatProvider
from .config import key_or_config_val
from .logger import logger
from .models import DEFAULT_EXTRAS, ChatModels, ChatProviders, TTSModels, TTSProviders
from .nodes import ChatPayload, FieldNode, TTSPayload
from .notes import get_chained_ai_fields, get_note_type
from .open_ai_client import OpenAIClient
from .prompts import get_extras, interpolate_prompt
from .tts_provider import TTSProvider


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

        extras = (
            get_extras(
                note_type=get_note_type(note),
                field=node.field,
                deck_id=node.deck_id,
                fallback_to_global_deck=True,
            )
            or DEFAULT_EXTRAS
        )

        if isinstance(payload, TTSPayload):
            if not is_app_unlocked():
                logger.debug("Skipping TTS field for locked app")
                return None

            if not mw:
                return None
            media = mw.col.media
            if not media:
                logger.error("No media")
                return None

            should_strip_html: bool = key_or_config_val(extras, "tts_strip_html")
            tts_provider: TTSProviders = key_or_config_val(extras, "tts_provider")
            tts_model: TTSModels = key_or_config_val(extras, "tts_model")
            tts_voice: str = key_or_config_val(extras, "tts_voice")

            tts_response = await self.get_tts_response(
                note=note,
                input_text=payload.input,
                model=tts_model,
                voice=tts_voice,
                provider=tts_provider,
                strip_html=should_strip_html,
            )

            if not tts_response:
                return None

            note_type = get_note_type(note)
            file_name = f"{note_type}-{node.field}-{note.id}.mp3"
            path = media.write_data(file_name, tts_response)

            return f"[sound:{path}]"

        elif isinstance(node.payload, ChatPayload):
            chat_model: ChatModels = key_or_config_val(extras, "chat_model")
            chat_provider: ChatProviders = key_or_config_val(extras, "chat_provider")
            chat_temperature: int = key_or_config_val(extras, "chat_temperature")
            should_convert: bool = key_or_config_val(extras, "chat_markdown_to_html")

            return await self.get_chat_response(
                note=note,
                deck_id=node.deck_id,
                prompt=payload.prompt,
                model=chat_model,
                provider=chat_provider,
                temperature=chat_temperature,
                field_lower=node.field,
                should_convert_to_html=should_convert,
            )

        else:
            logger.error(f"Unexpected payload type {type(payload)}")
            return None

    async def get_chat_response(
        self,
        note: Note,
        deck_id: DeckId,
        prompt: str,
        model: ChatModels,
        provider: ChatProviders,
        field_lower: str,
        temperature: int,
        should_convert_to_html: bool,
    ) -> Union[str, None]:

        interpolated_prompt = interpolate_prompt(prompt, note)

        if not interpolated_prompt:
            return None

        resp: Optional[str] = None

        if is_app_unlocked() and not is_at_text_capacity():
            resp = await self.chat_provider.async_get_chat_response(
                interpolated_prompt,
                model=model,
                provider=provider,
                temperature=temperature,
                note_id=note.id,
            )
        elif has_api_key():
            logger.debug("On legacy path....")
            # Check that this isn't a chained smart field
            chained_fields = get_chained_ai_fields(
                note_type=get_note_type(note), deck_id=deck_id
            )
            logger.debug(f"Chained fields: {chained_fields}")
            if field_lower in chained_fields:
                logger.debug(f"Skipping chained field: ${field_lower}")
                return None

            resp = await self.openai_provider.async_get_chat_response(
                interpolated_prompt, temperature=temperature, retry_count=0
            )

        if resp and should_convert_to_html:
            resp = marko.convert(resp)

        return resp

    async def get_tts_response(
        self,
        note: Note,
        input_text: str,
        model: TTSModels,
        provider: TTSProviders,
        voice: str,
        strip_html: bool,
    ):

        interpolated_prompt = interpolate_prompt(input_text, note)

        if not interpolated_prompt:
            return None

        logger.debug(f"Resolving: {interpolated_prompt}")
        if is_at_voice_capacity():
            logger.debug("App at voice capacity, returning early")
            return None

        return await self.tts_provider.async_get_tts_response(
            input=interpolated_prompt,
            model=model,
            provider=provider,
            voice=voice,
            note_id=note.id,
            strip_html=strip_html,
        )
