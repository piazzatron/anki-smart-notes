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

from typing import cast

from anki.decks import DeckId

from . import utils
from .logger import logger
from .models import (
    DEFAULT_EXTRAS,
    FieldExtras,
    GenerationDefaults,
    PromptMap,
)
from .models.smart_fields import (
    ChatSmartFieldSettings,
    ImageSmartFieldSettings,
    SmartFieldCreate,
    SmartFieldSettings,
    TTSSmartFieldSettings,
)
from .prompt_fields import get_prompt_fields


def smart_field_creates_from_prompt_map(
    prompt_map: PromptMap,
    generation_defaults: GenerationDefaults,
) -> list[SmartFieldCreate]:
    smart_fields: list[SmartFieldCreate] = []
    for note_type, decks in prompt_map["note_types"].items():
        note_type_id = utils.get_note_type_id_from_name(note_type)
        if note_type_id is None:
            logger.warning(
                f"Smart fields DB: skipping smart fields for missing note type: {note_type}"
            )
            continue

        for deck_id, note_type_map in decks.items():
            for field, prompt in note_type_map.get("fields", {}).items():
                extras = note_type_map.get("extras", {}).get(field) or DEFAULT_EXTRAS
                smart_fields.append(
                    SmartFieldCreate(
                        note_type_id=note_type_id,
                        deck_id=cast(DeckId, int(deck_id)),
                        target_field_name=field,
                        enabled=extras["automatic"],
                        settings=smart_field_settings_from_prompt_parts(
                            prompt, extras, generation_defaults
                        ),
                    )
                )
    return smart_fields


def smart_field_settings_from_prompt_parts(
    prompt: str,
    extras: FieldExtras,
    generation_defaults: GenerationDefaults,
) -> SmartFieldSettings:
    if extras["type"] == "tts":
        return TTSSmartFieldSettings(
            source_field_name=source_field_from_tts_prompt(prompt),
            provider=extras.get("tts_provider") or generation_defaults.tts.provider,
            model=extras.get("tts_model") or generation_defaults.tts.model,
            voice_id=extras.get("tts_voice") or generation_defaults.tts.voice_id,
            uses_default_generation_settings=not extras.get("use_custom_model"),
        )
    if extras["type"] == "image":
        return ImageSmartFieldSettings(
            prompt_text=prompt,
            provider=extras.get("image_provider") or generation_defaults.image.provider,
            model=extras.get("image_model") or generation_defaults.image.model,
            uses_default_generation_settings=not extras.get("use_custom_model"),
        )
    return ChatSmartFieldSettings(
        prompt_text=prompt,
        provider=extras.get("chat_provider") or generation_defaults.chat.provider,
        model=extras.get("chat_model") or generation_defaults.chat.model,
        reasoning_level=extras.get("chat_reasoning_level")
        or generation_defaults.chat.reasoning_level,
        web_search_enabled=_bool_option(
            extras.get("chat_web_search"), generation_defaults.chat.web_search_enabled
        ),
        uses_default_generation_settings=not extras.get("use_custom_model"),
    )


def source_field_from_tts_prompt(prompt: str) -> str:
    fields = get_prompt_fields(prompt, lower=False)
    if len(fields) != 1:
        raise ValueError(
            f"TTS smart fields must have exactly one source field, got: {prompt}"
        )
    return fields[0]


def _bool_option(value: object, default: bool) -> bool:
    return bool(value if value is not None else default)
