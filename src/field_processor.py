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

from anki.decks import DeckId
from anki.notes import Note
from aqt import mw

from .app_state import has_api_key, is_capacity_remaining
from .chat_provider import ChatProvider, chat_provider
from .config import key_or_config_val
from .constants import GENERIC_CREDITS_MESSAGE
from .image_provider import ImageProvider, image_provider
from .logger import logger
from .markdown import convert_markdown_to_html
from .media_utils import get_media_path
from .models import (
    DEFAULT_EXTRAS,
    ChatModels,
    ChatProviders,
    ElevenVoices,
    ImageModels,
    ImageProviders,
    OpenAIVoices,
    SmartFieldType,
    TTSModels,
    TTSProviders,
)
from .nodes import FieldNode
from .notes import get_chained_ai_fields, get_note_type
from .open_ai_client import OpenAIClient, openai_provider
from .prompts import get_extras, interpolate_prompt
from .tts_provider import TTSProvider, tts_provider
from .ui.ui_utils import show_message_box
from .utils import run_on_main


class FieldProcessor:
    def __init__(
        self,
        openai_provider: OpenAIClient,
        chat_provider: ChatProvider,
        tts_provider: TTSProvider,
        image_provider: ImageProvider,
    ):
        self.openai_provider = openai_provider
        self.chat_provider = chat_provider
        self.tts_provider = tts_provider
        self.image_provider = image_provider

    async def resolve(
        self, node: FieldNode, note: Note, show_error_box: bool = False
    ) -> Optional[str]:
        # Only show error box if we're running on the target node
        input = node.input
        field_type: SmartFieldType = node.field_type

        extras = (
            get_extras(
                note_type=get_note_type(note),
                field=node.field,
                deck_id=node.deck_id,
                fallback_to_global_deck=True,
            )
            or DEFAULT_EXTRAS
        )

        if field_type == "tts":
            if not is_capacity_remaining():
                logger.debug("Skipping TTS field for locked app")
                return None

            if not mw or not mw.col:
                return None
            media = mw.col.media
            if not media:
                logger.error("No media")
                return None

            should_strip_html: bool = key_or_config_val(extras, "tts_strip_html")
            tts_provider: TTSProviders = key_or_config_val(extras, "tts_provider")
            tts_model: TTSModels = key_or_config_val(extras, "tts_model")
            tts_voice: Union[OpenAIVoices, ElevenVoices] = key_or_config_val(
                extras, "tts_voice"
            )

            tts_response = await self.get_tts_response(
                note=note,
                input_text=input,
                model=tts_model,
                voice=tts_voice,
                provider=tts_provider,
                strip_html=should_strip_html,
                show_error_box=show_error_box,
            )

            if not tts_response:
                return None

            file_name = get_media_path(note, node.field, "mp3")
            path = media.write_data(file_name, tts_response)

            return f"[sound:{path}]"

        elif field_type == "chat":
            chat_model: ChatModels = key_or_config_val(extras, "chat_model")
            chat_provider: ChatProviders = key_or_config_val(extras, "chat_provider")
            chat_temperature: float = key_or_config_val(extras, "chat_temperature")
            should_convert: bool = key_or_config_val(extras, "chat_markdown_to_html")

            return await self.get_chat_response(
                note=note,
                deck_id=node.deck_id,
                prompt=input,
                model=chat_model,
                provider=chat_provider,
                temperature=chat_temperature,
                field_lower=node.field,
                should_convert_to_html=should_convert,
                show_error_box=show_error_box,
            )

        elif field_type == "image":
            if not mw or not mw.col:
                return None

            media = mw.col.media
            if not media:
                logger.error("No media")
                return None

            image_model: ImageModels = key_or_config_val(extras, "image_model")
            image_provider: ImageProviders = key_or_config_val(extras, "image_provider")

            image_response = await self.get_image_response(
                note=note,
                input_text=input,
                model=image_model,
                provider=image_provider,
                show_error_box=show_error_box,
            )
            if not image_response:
                return None

            file_name = get_media_path(note, node.field, "webp")
            path = media.write_data(file_name, image_response)
            return f'<img src="{path}"/>'
        else:
            raise Exception(f"Unexpected note type {field_type}")

    async def get_chat_response(
        self,
        note: Note,
        deck_id: DeckId,
        prompt: str,
        model: ChatModels,
        provider: ChatProviders,
        field_lower: str,
        temperature: float,
        should_convert_to_html: bool,
        show_error_box: bool = True,
    ) -> Optional[str]:
        interpolated_prompt = interpolate_prompt(prompt, note)

        if not interpolated_prompt:
            return None

        resp: Optional[str] = None

        if is_capacity_remaining():
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
        else:
            logger.error("App is at capacity + no API key")
            if show_error_box:
                run_on_main(lambda: show_message_box(GENERIC_CREDITS_MESSAGE))
            return None

        if resp and should_convert_to_html:
            resp = convert_markdown_to_html(resp)

        return resp

    async def get_tts_response(
        self,
        note: Note,
        input_text: str,
        model: TTSModels,
        provider: TTSProviders,
        voice: str,
        strip_html: bool,
        show_error_box: bool = True,
    ) -> Optional[bytes]:
        interpolated_prompt = interpolate_prompt(input_text, note)

        if not interpolated_prompt:
            return None

        logger.debug(f"Resolving: {interpolated_prompt}")

        if not is_capacity_remaining():
            logger.debug("App at capacity, returning early")
            if show_error_box:
                run_on_main(lambda: show_message_box(GENERIC_CREDITS_MESSAGE))
            return None

        return await self.tts_provider.async_get_tts_response(
            input=interpolated_prompt,
            model=model,
            provider=provider,
            voice=voice,
            note_id=note.id,
            strip_html=strip_html,
        )

    async def get_image_response(
        self,
        note: Note,
        input_text: str,
        model: ImageModels,
        provider: ImageProviders,
        show_error_box: bool = True,
    ) -> Optional[bytes]:
        if not is_capacity_remaining():
            logger.debug("App at capacity, returning early")
            if show_error_box:
                run_on_main(lambda: show_message_box(GENERIC_CREDITS_MESSAGE))
            return None

        interpolated_prompt = interpolate_prompt(input_text, note)

        if not interpolated_prompt:
            return None

        return await self.image_provider.async_get_image_response(
            prompt=interpolated_prompt, model=model, provider=provider, note_id=note.id
        )


field_processor = FieldProcessor(
    openai_provider=openai_provider,
    chat_provider=chat_provider,
    tts_provider=tts_provider,
    image_provider=image_provider,
)
