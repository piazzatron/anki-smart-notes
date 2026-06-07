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

from dataclasses import dataclass
from typing import Union

from anki.decks import DeckId

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


@dataclass(frozen=True)
class ChatGenerationSettings:
    provider: ChatProviders
    model: ChatModels
    reasoning_level: ChatReasoningLevel
    web_search_enabled: bool


@dataclass(frozen=True)
class TTSGenerationSettings:
    provider: TTSProviders
    model: TTSModels
    voice_id: str


@dataclass(frozen=True)
class ImageGenerationSettings:
    provider: ImageProviders
    model: ImageModels


@dataclass(frozen=True)
class GenerationDefaults:
    chat: ChatGenerationSettings
    tts: TTSGenerationSettings
    image: ImageGenerationSettings


DEFAULT_TEXT_GENERATION_SETTINGS = ChatGenerationSettings(
    provider="auto",
    model="auto",
    reasoning_level="off",
    web_search_enabled=False,
)
DEFAULT_TTS_GENERATION_SETTINGS = TTSGenerationSettings(
    provider="google",
    model="standard",
    voice_id="en-US-Casual-K",
)
DEFAULT_IMAGE_GENERATION_SETTINGS = ImageGenerationSettings(
    provider="openai",
    model="gpt-image-1.5-low",
)


@dataclass(frozen=True)
class ChatSmartFieldSettings:
    prompt_text: str
    provider: ChatProviders
    model: ChatModels
    web_search_enabled: bool
    reasoning_level: ChatReasoningLevel = "off"
    uses_default_generation_settings: bool = False


@dataclass(frozen=True)
class TTSSmartFieldSettings:
    source_field_name: str
    provider: TTSProviders
    model: TTSModels
    voice_id: str
    uses_default_generation_settings: bool = False


@dataclass(frozen=True)
class ImageSmartFieldSettings:
    prompt_text: str
    provider: ImageProviders
    model: ImageModels
    uses_default_generation_settings: bool = False


SmartFieldSettings = Union[
    ChatSmartFieldSettings, TTSSmartFieldSettings, ImageSmartFieldSettings
]


@dataclass(frozen=True)
class SmartField:
    id: str
    profile_name: str
    note_type_id: int
    deck_id: DeckId
    target_field_name: str
    enabled: bool
    settings: SmartFieldSettings

    @property
    def field_type(self) -> SmartFieldType:
        return smart_field_type(self.settings)


@dataclass(frozen=True)
class SmartFieldCreate:
    note_type_id: int
    deck_id: DeckId
    target_field_name: str
    enabled: bool
    settings: SmartFieldSettings

    @property
    def field_type(self) -> SmartFieldType:
        return smart_field_type(self.settings)


def smart_field_type(settings: SmartFieldSettings) -> SmartFieldType:
    if isinstance(settings, ChatSmartFieldSettings):
        return "chat"
    if isinstance(settings, TTSSmartFieldSettings):
        return "tts"
    return "image"
