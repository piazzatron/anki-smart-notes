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

import re
from copy import deepcopy
from typing import Optional, cast

from anki.decks import DeckId
from aqt import mw

from .constants import GLOBAL_DECK_ID
from .logger import logger
from .models import (
    DEFAULT_EXTRAS,
    FieldExtras,
    PromptMap,
)
from .models.smart_fields import (
    ChatSmartFieldSettings,
    ImageSmartFieldSettings,
    SmartField,
    SmartFieldCreate,
    SmartFieldSettings,
    TTSSmartFieldSettings,
)
from .services.smart_field_service import smart_field_service

FIELD_PATTERN = r"\{\{(?!c\d+::)(.+?)\}\}"

# Temporary compatibility layer for the existing smart field UI. The major UI
# refactor should remove this prompt-map shape and talk to smart fields directly.


def list_prompt_map() -> PromptMap:
    if not mw or not mw.col:
        return {"note_types": {}}

    note_type_names = {
        int(note_type["id"]): str(note_type["name"])
        for note_type in mw.col.models.all()
    }
    return prompt_map_from_smart_fields(
        smart_field_service.get_all_smart_fields(), note_type_names
    )


def list_for_note_type(
    note_type: str,
    deck_id: DeckId,
    fallback_to_global_deck: bool = True,
) -> dict[str, tuple[str, FieldExtras]]:
    prompt_map = list_prompt_map()
    note_type_map = prompt_map["note_types"].get(note_type, {})
    deck_map = deepcopy(note_type_map.get(str(deck_id), {}))
    global_map = deepcopy(note_type_map.get(str(GLOBAL_DECK_ID), {}))

    if fallback_to_global_deck:
        deck_map.setdefault("fields", {})
        deck_map.setdefault("extras", {})
        for field, prompt in global_map.get("fields", {}).items():
            if field not in deck_map["fields"]:
                deck_map["fields"][field] = prompt
                deck_map["extras"][field] = global_map["extras"][field]

    return {
        field: (prompt, deck_map.get("extras", {}).get(field) or DEFAULT_EXTRAS)
        for field, prompt in deck_map.get("fields", {}).items()
    }


def replace_from_prompt_map(prompt_map: PromptMap) -> None:
    logger.debug("Smart fields DB: replacing all smart fields from prompt map")
    smart_field_service.replace_all_smart_fields(
        smart_field_creates_from_prompt_map(prompt_map)
    )


def prompt_map_from_smart_fields(
    smart_fields: list[SmartField],
    note_type_names: dict[int, str],
) -> PromptMap:
    prompt_map: PromptMap = {"note_types": {}}
    for smart_field in smart_fields:
        note_type = note_type_names.get(smart_field.note_type_id)
        if not note_type:
            logger.warning(
                f"Smart fields DB: skipping row for deleted note type id {smart_field.note_type_id}"
            )
            continue

        deck_key = str(smart_field.deck_id)
        target_field = smart_field.target_field_name
        note_type_map = prompt_map["note_types"].setdefault(note_type, {})
        deck_map = note_type_map.setdefault(deck_key, {"fields": {}, "extras": {}})
        deck_map["fields"][target_field] = prompt_from_smart_field(smart_field)
        deck_map["extras"][target_field] = extras_from_smart_field(smart_field)

    return prompt_map


def smart_field_creates_from_prompt_map(
    prompt_map: PromptMap,
) -> list[SmartFieldCreate]:
    smart_fields: list[SmartFieldCreate] = []
    for note_type, decks in prompt_map["note_types"].items():
        note_type_id = note_type_id_from_name(note_type)
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
                        settings=settings_from_prompt_parts(prompt, extras),
                    )
                )
    return smart_fields


def note_type_id_from_name(note_type: str) -> Optional[int]:
    if not mw or not mw.col:
        return None
    model = mw.col.models.by_name(note_type)
    if not model:
        logger.warning(f"Smart fields DB: note type missing: {note_type}")
        return None
    return int(model["id"])


def prompt_from_smart_field(smart_field: SmartField) -> str:
    settings = smart_field.settings
    if isinstance(settings, TTSSmartFieldSettings):
        return "{{" + settings.source_field_name + "}}"
    if isinstance(settings, ImageSmartFieldSettings):
        return settings.prompt_text
    return settings.prompt_text


def extras_from_smart_field(smart_field: SmartField) -> FieldExtras:
    extras = deepcopy(DEFAULT_EXTRAS)
    extras["type"] = smart_field.field_type
    extras["automatic"] = smart_field.enabled

    settings = smart_field.settings
    extras["use_custom_model"] = not settings.uses_default_generation_settings
    if settings.uses_default_generation_settings:
        return extras

    if isinstance(settings, ChatSmartFieldSettings):
        extras["chat_provider"] = settings.provider
        extras["chat_model"] = settings.model
        extras["chat_reasoning_level"] = settings.reasoning_level
        extras["chat_web_search"] = settings.web_search_enabled
    elif isinstance(settings, TTSSmartFieldSettings):
        extras["tts_provider"] = settings.provider
        extras["tts_model"] = settings.model
        extras["tts_voice"] = settings.voice_id
    else:
        extras["image_provider"] = settings.provider
        extras["image_model"] = settings.model

    return extras


def settings_from_prompt_parts(prompt: str, extras: FieldExtras) -> SmartFieldSettings:
    field_type = extras["type"]
    if field_type == "chat":
        defaults = smart_field_service.get_chat_defaults()
        uses_defaults = not extras.get("use_custom_model")
        return ChatSmartFieldSettings(
            prompt_text=prompt,
            provider=extras.get("chat_provider") or defaults.provider,
            model=extras.get("chat_model") or defaults.model,
            reasoning_level=extras.get("chat_reasoning_level")
            or defaults.reasoning_level,
            web_search_enabled=_bool_option(
                extras.get("chat_web_search"), defaults.web_search_enabled
            ),
            uses_default_generation_settings=uses_defaults,
        )
    if field_type == "tts":
        defaults = smart_field_service.get_tts_defaults()
        return TTSSmartFieldSettings(
            source_field_name=source_field_from_tts_prompt(prompt),
            provider=extras.get("tts_provider") or defaults.provider,
            model=extras.get("tts_model") or defaults.model,
            voice_id=extras.get("tts_voice") or defaults.voice_id,
            uses_default_generation_settings=not extras.get("use_custom_model"),
        )
    defaults = smart_field_service.get_image_defaults()
    return ImageSmartFieldSettings(
        prompt_text=prompt,
        provider=extras.get("image_provider") or defaults.provider,
        model=extras.get("image_model") or defaults.model,
        uses_default_generation_settings=not extras.get("use_custom_model"),
    )


def source_field_from_tts_prompt(prompt: str) -> str:
    fields = re.findall(FIELD_PATTERN, prompt)
    if len(fields) != 1:
        raise ValueError(
            f"TTS smart fields must have exactly one source field, got: {prompt}"
        )
    return fields[0]


def _bool_option(value: object, default: bool) -> bool:
    return bool(value if value is not None else default)
