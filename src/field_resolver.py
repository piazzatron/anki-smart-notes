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

from typing import Optional, Union, cast
from uuid import uuid4
from weakref import WeakKeyDictionary

from anki.decks import DeckId
from anki.notes import Note
from aqt import mw

from .app_state import has_legacy_openai_access, is_capacity_remaining, is_free_plan
from .chat_provider import ChatProvider, chat_provider
from .image_provider import ImageProvider, ImageResponse, image_provider
from .image_utils import download_and_embed_images
from .logger import logger
from .markdown import convert_markdown_to_html
from .media_utils import ext_from_content_type, get_media_path
from .models import (
    ChatModels,
    ChatProviders,
    ChatReasoningLevel,
    ElevenVoices,
    GenerationSource,
    ImageModels,
    ImageProviders,
    OpenAIVoices,
    SmartFieldType,
    TTSModels,
    TTSProviders,
)
from .models.smart_fields import (
    ChatSmartFieldSettings,
    ImageSmartFieldSettings,
    TTSSmartFieldSettings,
)
from .nodes import FieldNode
from .open_ai_client import OpenAIClient, openai_provider
from .prompt_helpers import interpolate_prompt
from .tts_provider import TTSProvider, tts_provider
from .utils.notes_utils import get_chained_ai_fields, get_note_type


class FieldResolver:
    """Turns one DAG node into the text, audio, or image value written to a note."""

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
        field_type: SmartFieldType = node.smart_field.field_type
        settings = node.smart_field.settings

        # The free plan has no voice or image generation. Skip those fields
        # quietly rather than fail every note that has one.
        if field_type in ("tts", "image") and is_free_plan():
            logger.debug(f"Skipping {field_type} field {node.field} on the free plan")
            return None

        if field_type == "tts":
            if not isinstance(settings, TTSSmartFieldSettings):
                raise Exception(f"Unexpected settings for TTS field {node.field}")

            if not is_capacity_remaining():
                logger.debug("Skipping TTS field for locked app")
                return None

            if not mw or not mw.col:
                return None
            media = mw.col.media
            if not media:
                logger.error("No media")
                return None

            # Anki field names are user-defined, so match case-insensitively while
            # preserving the original note field key/value.
            source_value = None
            source_field_name_lower = settings.source_field_name.lower()
            for note_field, value in note.items():  # type: ignore[attr-defined]
                if note_field.lower() == source_field_name_lower:
                    source_value = cast(Optional[str], value)
                    break
            if not source_value:
                return None

            tts_response = await self.get_tts_response(
                note=note,
                input_text=source_value,
                model=settings.model,
                voice=cast(Union[OpenAIVoices, ElevenVoices], settings.voice_id),
                provider=settings.provider,
                show_error_box=show_error_box,
                generation_source="card_generation",
            )

            if not tts_response:
                return None

            audio_ext = "wav" if settings.provider == "voicevox" else "mp3"
            file_name = get_media_path(note, node.field, audio_ext)
            path = media.write_data(file_name, tts_response)

            return f"[sound:{path}]"

        elif field_type == "chat":
            if not isinstance(settings, ChatSmartFieldSettings):
                raise Exception(f"Unexpected settings for chat field {node.field}")

            return await self.get_chat_response(
                note=note,
                deck_id=node.smart_field.deck_id,
                prompt=input,
                model=settings.model,
                provider=settings.provider,
                field_lower=node.field,
                should_convert_to_html=True,
                strip_html=settings.strip_html,
                web_search=settings.web_search_enabled,
                reasoning_level=settings.reasoning_level,
                show_error_box=show_error_box,
                generation_source="card_generation",
            )

        elif field_type == "image":
            if not isinstance(settings, ImageSmartFieldSettings):
                raise Exception(f"Unexpected settings for image field {node.field}")

            if not mw or not mw.col:
                return None

            media = mw.col.media
            if not media:
                logger.error("No media")
                return None

            image_response = await self.get_image_response(
                note=note,
                input_text=input,
                model=settings.model,
                provider=settings.provider,
                strip_html=settings.strip_html,
                show_error_box=show_error_box,
                generation_source="card_generation",
            )
            if not image_response:
                return None

            ext = ext_from_content_type(image_response["content_type"])
            file_name = get_media_path(note, node.field, ext)
            path = media.write_data(file_name, image_response["data"])
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
        should_convert_to_html: bool,
        strip_html: bool,
        generation_source: GenerationSource,
        web_search: bool = False,
        reasoning_level: ChatReasoningLevel = "off",
        show_error_box: bool = True,
        should_embed_images: bool = True,
    ) -> Optional[str]:
        interpolated_prompt = interpolate_prompt(prompt, note, strip_html)

        if not interpolated_prompt:
            return None

        resp: Optional[str] = None

        # The free plan includes Auto at Standard only. Send that instead of
        # failing, and leave the saved settings for when the user upgrades.
        if is_free_plan():
            provider, model, reasoning_level, web_search = "auto", "auto", "off", False

        if is_capacity_remaining():
            resp = await self.chat_provider.async_get_chat_response(
                interpolated_prompt,
                model=model,
                provider=provider,
                note_id=_server_note_id(note),
                web_search=web_search,
                reasoning_level=reasoning_level,
                generation_source=generation_source,
            )
        elif has_legacy_openai_access():
            logger.debug("On legacy path....")
            chained_fields = get_chained_ai_fields(
                note_type=get_note_type(note), deck_id=deck_id
            )
            logger.debug(f"Chained fields: {chained_fields}")
            if field_lower in chained_fields:
                logger.debug(f"Skipping chained field: ${field_lower}")
                return None

            resp = await self.openai_provider.async_get_chat_response(
                interpolated_prompt, retry_count=0
            )
        else:
            logger.error("App is at capacity + no API key")
            return None

        if resp and web_search and should_embed_images:
            resp = await download_and_embed_images(
                resp, note, field_lower, show_error_box=show_error_box
            )

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
        generation_source: GenerationSource,
        show_error_box: bool = True,
    ) -> Optional[bytes]:
        # The server strips HTML from TTS input itself, before it bills.
        interpolated_prompt = interpolate_prompt(input_text, note, strip_html=False)

        if not interpolated_prompt:
            return None

        logger.debug(f"Resolving: {interpolated_prompt}")

        if not is_capacity_remaining():
            logger.debug("App at capacity, returning early")
            return None

        return await self.tts_provider.async_get_tts_response(
            input=interpolated_prompt,
            model=model,
            provider=provider,
            voice=voice,
            note_id=_server_note_id(note),
            generation_source=generation_source,
        )

    async def get_image_response(
        self,
        note: Note,
        input_text: str,
        model: ImageModels,
        provider: ImageProviders,
        strip_html: bool,
        generation_source: GenerationSource,
        show_error_box: bool = True,
    ) -> Optional[ImageResponse]:
        if not is_capacity_remaining():
            logger.debug("App at capacity, returning early")
            return None

        interpolated_prompt = interpolate_prompt(input_text, note, strip_html)

        if not interpolated_prompt:
            return None

        return await self.image_provider.async_get_image_response(
            prompt=interpolated_prompt,
            model=model,
            provider=provider,
            note_id=_server_note_id(note),
            generation_source=generation_source,
        )


# Notes in the Add dialog aren't saved yet and all have id 0. Each gets its own
# ID, shared by its fields, so the server counts it as one note toward daily
# and trial note limits.
_unsaved_note_ids: "WeakKeyDictionary[Note, str]" = WeakKeyDictionary()


def _server_note_id(note: Note) -> str:
    if note.id:
        return str(note.id)
    return _unsaved_note_ids.setdefault(note, str(uuid4()))


field_resolver = FieldResolver(
    openai_provider=openai_provider,
    chat_provider=chat_provider,
    tts_provider=tts_provider,
    image_provider=image_provider,
)
