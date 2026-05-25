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
    ImageModels,
    ImageProviders,
    SmartFieldType,
    TTSModels,
    TTSProviders,
)


@dataclass(frozen=True)
class ChatSmartFieldSettings:
    prompt_text: str
    provider: ChatProviders
    model: ChatModels
    web_search_enabled: bool


@dataclass(frozen=True)
class TTSSmartFieldSettings:
    source_field_name: str
    provider: TTSProviders
    model: TTSModels
    voice_id: str


@dataclass(frozen=True)
class ImageSmartFieldSettings:
    prompt_text: str
    provider: ImageProviders
    model: ImageModels


SmartFieldSettings = Union[
    ChatSmartFieldSettings, TTSSmartFieldSettings, ImageSmartFieldSettings
]


@dataclass(frozen=True)
class SmartField:
    id: str
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
