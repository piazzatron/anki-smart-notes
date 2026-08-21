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

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal, TypedDict, Union

if TYPE_CHECKING:
    from anki.decks import DeckId

    from ...models import (
        ChatModels,
        ChatProviders,
        ChatReasoningLevel,
        ImageModels,
        ImageProviders,
        TTSModels,
        TTSProviders,
    )
    from ...subscription_provider import PlanInfo
    from ...voice_catalog import VoiceGender, VoicePriceTier

CHAT_REASONING_LEVELS: list[ChatReasoningLevel] = ["off", "low", "high"]


# -- Outbound wire types (domain -> JSON). The client consumes these as
# camelCase and posts the same shapes back, so the parsers reuse them as the
# declared inbound types too. --


class NoteTypeDto(TypedDict):
    id: int
    name: str
    fields: list[str]


class DeckDto(TypedDict):
    id: DeckId
    name: str


class ChatGenerationSettingsDto(TypedDict):
    provider: ChatProviders
    model: ChatModels
    reasoningLevel: ChatReasoningLevel
    webSearchEnabled: bool


class TTSGenerationSettingsDto(TypedDict):
    provider: TTSProviders
    model: TTSModels
    voiceId: str


class ImageGenerationSettingsDto(TypedDict):
    provider: ImageProviders
    model: ImageModels


class GenerationDefaultsDto(TypedDict):
    chat: ChatGenerationSettingsDto
    tts: TTSGenerationSettingsDto
    image: ImageGenerationSettingsDto


class SettingsDto(TypedDict):
    generateAtReview: bool
    regenerateWhenBatching: bool
    debug: bool
    legacyOpenAiEnabled: bool
    legacyOpenAiKey: str | None
    legacyOpenAiModel: str
    legacyOpenAiHost: str | None
    showWizardCompletion: bool
    didDismissReviewPrompt: bool
    didDismissDiscordPrompt: bool


class ChatSmartFieldSettingsDto(TypedDict):
    promptText: str
    provider: ChatProviders
    model: ChatModels
    reasoningLevel: ChatReasoningLevel
    webSearchEnabled: bool
    usesDefaultGenerationSettings: bool


class TTSSmartFieldSettingsDto(TypedDict):
    sourceFieldName: str
    provider: TTSProviders
    model: TTSModels
    voiceId: str
    usesDefaultGenerationSettings: bool


class ImageSmartFieldSettingsDto(TypedDict):
    promptText: str
    provider: ImageProviders
    model: ImageModels
    usesDefaultGenerationSettings: bool


class SmartFieldBaseDto(TypedDict):
    id: str
    noteTypeId: int
    deckId: DeckId
    targetFieldName: str
    enabled: bool


class ChatSmartFieldDto(SmartFieldBaseDto):
    fieldType: Literal["chat"]
    settings: ChatSmartFieldSettingsDto


class TTSSmartFieldDto(SmartFieldBaseDto):
    fieldType: Literal["tts"]
    settings: TTSSmartFieldSettingsDto


class ImageSmartFieldDto(SmartFieldBaseDto):
    fieldType: Literal["image"]
    settings: ImageSmartFieldSettingsDto


SmartFieldDto = Union[ChatSmartFieldDto, TTSSmartFieldDto, ImageSmartFieldDto]


class FeatureFlagsDto(TypedDict):
    reviewFreeMonth: bool


class AccountDto(TypedDict):
    """Account state exposed to the web UI, including the backend JWT needed
    for direct authenticated API requests."""

    status: Literal["LOADING", "UNAUTHENTICATED", "AUTHENTICATED"]
    plan: PlanInfo | None
    email: str | None
    authToken: str | None


class StateDto(TypedDict):
    smartFields: list[SmartFieldDto]
    noteTypes: list[NoteTypeDto]
    decks: list[DeckDto]
    globalDeckId: DeckId
    account: AccountDto
    featureFlags: FeatureFlagsDto
    settings: SettingsDto
    appVersion: str
    defaults: GenerationDefaultsDto


class VoiceCatalogDto(TypedDict):
    voices: list[VoiceCatalogItemDto]


class VoiceCatalogItemDto(TypedDict):
    provider: TTSProviders
    voiceId: str
    model: str
    name: str
    gender: VoiceGender
    language: str
    priceTier: VoicePriceTier


# -- Inbound command payloads (JSON -> domain). Each parser casts a raw dict to
# the matching type below, so the wire keys and their types are declared once
# and every field access is statically checked. --


class SmartFieldCreatePayload(TypedDict):
    noteTypeId: int
    deckId: int
    targetFieldName: str
    enabled: bool
    fieldType: str
    settings: dict[str, Any]


class SmartFieldUpdatePayload(SmartFieldCreatePayload):
    id: str


class SmartFieldIdPayload(TypedDict):
    id: str


class PromptGeneratePayload(TypedDict):
    noteTypeId: int
    deckId: int
    targetFieldName: str
    fieldType: str
    generationPrompt: str


class TextPromptTestPayload(TypedDict):
    prompt: str
    settings: ChatGenerationSettingsDto


class ImagePromptTestPayload(TypedDict):
    prompt: str
    settings: ImageGenerationSettingsDto


class TTSPromptTestPayload(TypedDict):
    text: str
    settings: TTSGenerationSettingsDto


class SaveTestResultPayload(TypedDict):
    token: str
    cardId: int
    fieldName: str


class FeedbackPayload(TypedDict):
    message: str


class AuthExchangeCodePayload(TypedDict):
    code: str


@dataclass(frozen=True)
class PromptGenerateRequest:
    note_type_id: int
    deck_id: DeckId
    target_field_name: str
    field_type: Literal["chat", "image"]
    generation_prompt: str
