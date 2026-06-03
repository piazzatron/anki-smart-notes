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

from typing import Any, Optional, TypedDict

from .providers import (
    ChatModels,
    ChatProviders,
    ChatReasoningLevel,
    ImageModels,
    ImageProviders,
    SmartFieldType,
    TTSModels,
    TTSProviders,
)


class FieldExtras(TypedDict):
    automatic: bool
    type: SmartFieldType
    use_custom_model: bool

    chat_model: Optional[ChatModels]
    chat_provider: Optional[ChatProviders]
    chat_reasoning_level: Optional[ChatReasoningLevel]
    chat_web_search: Optional[bool]

    tts_provider: Optional[TTSProviders]
    tts_model: Optional[TTSModels]
    tts_voice: Optional[str]

    image_provider: Optional[ImageProviders]
    image_model: Optional[ImageModels]


DEFAULT_EXTRAS: FieldExtras = {
    "automatic": True,
    "type": "chat",
    "use_custom_model": False,
    "chat_model": None,
    "chat_provider": None,
    "chat_reasoning_level": None,
    "chat_web_search": None,
    "tts_model": None,
    "tts_provider": None,
    "tts_voice": None,
    "image_provider": None,
    "image_model": None,
}


class NoteTypeMap(TypedDict):
    fields: dict[str, str]
    extras: dict[str, FieldExtras]


class PromptMap(TypedDict):
    note_types: dict[str, dict[str, NoteTypeMap]]


# The UI derives option key lists from these TypedDicts, so a new option only
# needs one type entry here plus its FieldExtras/DEFAULT_EXTRAS entry.
def typed_dict_keys(td: Any) -> list[str]:
    return list(td.__annotations__.keys())


class OverridableChatOptionsDict(TypedDict):
    chat_provider: Optional[ChatProviders]
    chat_model: Optional[ChatModels]
    chat_reasoning_level: Optional[ChatReasoningLevel]
    chat_web_search: Optional[bool]


overridable_chat_options: list[str] = typed_dict_keys(OverridableChatOptionsDict)


class OverrideableTTSOptionsDict(TypedDict):
    tts_model: Optional[TTSModels]
    tts_provider: Optional[TTSProviders]
    tts_voice: Optional[str]


overridable_tts_options: list[str] = typed_dict_keys(OverrideableTTSOptionsDict)


class OverridableImageOptionsDict(TypedDict):
    image_model: Optional[ImageModels]
    image_provider: Optional[ImageProviders]


overridable_image_options: list[str] = typed_dict_keys(OverridableImageOptionsDict)
