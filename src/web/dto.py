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

# The web UI wire format, defined in one place (see specs/web-ui-architecture.md
# in the top-level repo). Pure functions mapping domain objects to JSON-ready
# dicts and command payloads back to domain objects. Anything that reads
# Anki/domain state must be called on the main thread.
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal, TypedDict, Union, cast

from anki.cards import CardId
from anki.decks import DeckId

from ..constants import GLOBAL_DECK_ID
from ..models import (
    ChatModels,
    ChatProviders,
    ChatReasoningLevel,
    ImageModels,
    ImageProviders,
    TTSModels,
    TTSProviders,
    image_provider_model_map,
    provider_model_map,
)
from ..models.smart_fields import (
    ChatGenerationSettings,
    ChatSmartFieldSettings,
    GenerationDefaults,
    ImageGenerationSettings,
    ImageSmartFieldSettings,
    SmartField,
    SmartFieldCreate,
    SmartFieldSettings,
    TextPromptTestRequest,
    TTSGenerationSettings,
    TTSSmartFieldSettings,
)

if TYPE_CHECKING:
    from anki.notes import Note

    from ..app_state import AppState

SCHEMA_VERSION: Literal[1] = 1
CHAT_REASONING_LEVELS: list[ChatReasoningLevel] = ["off", "low", "high"]


def build_state(
    *,
    defaults: GenerationDefaults,
    note_types: list[tuple[int, str, list[str]]],
    decks: dict[DeckId, str],
    smart_fields: list[SmartField],
    account: AppState,
) -> StateDto:
    """The full `state` event payload. Whole-state push: every state event
    carries everything, so consumers replace their model wholesale."""
    note_type_ids = {note_type_id for note_type_id, _, _ in note_types}
    deck_ids = set(decks)

    return StateDto(
        schemaVersion=SCHEMA_VERSION,
        smartFields=[
            _smart_field_dto(field)
            for field in smart_fields
            if field.note_type_id in note_type_ids and field.deck_id in deck_ids
        ],
        # Note types and decks let the UI render names for the IDs that smart
        # fields and selection events carry (and feed authoring pickers).
        noteTypes=[
            NoteTypeDto(id=note_type_id, name=name, fields=fields)
            for note_type_id, name, fields in note_types
        ],
        decks=[
            DeckDto(id=deck_id, name=name)
            for deck_id, name in sorted(decks.items(), key=lambda item: item[1])
        ],
        # The pseudo-deck meaning "applies to all decks" — present in `decks`
        # with a friendly name, but scoping UI needs to special-case it.
        globalDeckId=GLOBAL_DECK_ID,
        account=account,
        defaults=GenerationDefaultsDto(
            chat=ChatGenerationSettingsDto(
                provider=defaults.chat.provider,
                model=defaults.chat.model,
                reasoningLevel=defaults.chat.reasoning_level,
                webSearchEnabled=defaults.chat.web_search_enabled,
            ),
            tts=TTSGenerationSettingsDto(
                provider=defaults.tts.provider,
                model=defaults.tts.model,
                voiceId=defaults.tts.voice_id,
            ),
            image=ImageGenerationSettingsDto(
                provider=defaults.image.provider,
                model=defaults.image.model,
            ),
        ),
    )


def build_catalog() -> dict[str, Any]:
    """Static model facts sent once when an SSE connection is established."""
    return {
        "schemaVersion": SCHEMA_VERSION,
        "chat": {
            "providers": list(provider_model_map),
            "models": [
                {"id": model, "provider": provider}
                for provider, models in provider_model_map.items()
                for model in models
            ],
            "reasoningLevels": CHAT_REASONING_LEVELS,
        },
        "image": {
            "providers": list(image_provider_model_map),
            "models": [
                {"id": model, "provider": provider}
                for provider, models in image_provider_model_map.items()
                for model in models
            ],
        },
    }


def build_selection_changed(
    note: Note, card_id: CardId, deck_id: int | None
) -> dict[str, Any]:
    """`anki.browserSelectionChanged` payload for a single selected note."""
    return {
        "note": {
            "cardId": card_id,
            "id": note.id,
            "noteTypeId": note.mid,
            "deckId": deck_id,
            "fields": {name: note[name] for name in note.keys()},  # noqa: SIM118
        }
    }


def build_selection_cleared(count: int) -> dict[str, Any]:
    """Selection payload when the Browser does not have exactly one row selected."""
    return {"note": None, "count": count}


# -- Command payload parsing (wire → domain). Raise ValueError on bad shapes;
# the server maps that to a 400 with the message. --


def parse_smart_field_create(payload: dict[str, Any]) -> SmartFieldCreate:
    field_type = _require(payload, "fieldType")
    settings_raw = _require(payload, "settings")

    settings: SmartFieldSettings
    if field_type == "chat":
        settings = ChatSmartFieldSettings(
            prompt_text=_require(settings_raw, "promptText"),
            provider=cast(ChatProviders, _require(settings_raw, "provider")),
            model=cast(ChatModels, _require(settings_raw, "model")),
            reasoning_level=cast(
                ChatReasoningLevel,
                _require(settings_raw, "reasoningLevel"),
            ),
            web_search_enabled=_require(settings_raw, "webSearchEnabled"),
            uses_default_generation_settings=_require(
                settings_raw, "usesDefaultGenerationSettings"
            ),
        )
    elif field_type == "tts":
        settings = TTSSmartFieldSettings(
            source_field_name=_require(settings_raw, "sourceFieldName"),
            provider=cast(TTSProviders, _require(settings_raw, "provider")),
            model=cast(TTSModels, _require(settings_raw, "model")),
            voice_id=_require(settings_raw, "voiceId"),
            uses_default_generation_settings=_require(
                settings_raw, "usesDefaultGenerationSettings"
            ),
        )
    elif field_type == "image":
        settings = ImageSmartFieldSettings(
            prompt_text=_require(settings_raw, "promptText"),
            provider=cast(ImageProviders, _require(settings_raw, "provider")),
            model=cast(ImageModels, _require(settings_raw, "model")),
            uses_default_generation_settings=_require(
                settings_raw, "usesDefaultGenerationSettings"
            ),
        )
    else:
        raise ValueError(f"Unknown fieldType: {field_type}")

    return SmartFieldCreate(
        note_type_id=int(_require(payload, "noteTypeId")),
        deck_id=cast(DeckId, int(_require(payload, "deckId"))),
        target_field_name=_require(payload, "targetFieldName"),
        enabled=_require(payload, "enabled"),
        settings=settings,
    )


def parse_smart_field_ref(payload: dict[str, Any]) -> SmartFieldRef:
    return SmartFieldRef(
        note_type_id=int(_require(payload, "noteTypeId")),
        deck_id=cast(DeckId, int(_require(payload, "deckId"))),
        target_field_name=_require(payload, "targetFieldName"),
    )


def parse_generation_defaults(payload: dict[str, Any]) -> GenerationDefaults:
    chat = _require(payload, "chat")
    tts = _require(payload, "tts")
    image = _require(payload, "image")
    return GenerationDefaults(
        chat=parse_chat_generation_settings(chat),
        tts=TTSGenerationSettings(
            provider=cast(TTSProviders, _require(tts, "provider")),
            model=cast(TTSModels, _require(tts, "model")),
            voice_id=_require(tts, "voiceId"),
        ),
        image=ImageGenerationSettings(
            provider=cast(ImageProviders, _require(image, "provider")),
            model=cast(ImageModels, _require(image, "model")),
        ),
    )


def parse_text_prompt_test(payload: dict[str, Any]) -> TextPromptTestRequest:
    card_id = _require(payload, "cardId")
    prompt = _require(payload, "prompt")
    settings = _require(payload, "settings")

    if isinstance(card_id, bool) or not isinstance(card_id, int):
        raise ValueError("cardId must be an integer")
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("prompt must be a non-empty string")
    if not isinstance(settings, dict):
        raise ValueError("settings must be an object")

    return TextPromptTestRequest(
        card_id=cast(CardId, card_id),
        prompt=prompt,
        settings=parse_chat_generation_settings(settings),
    )


@dataclass(frozen=True)
class SmartFieldRef:
    """Wire identity of a smart field, used by the delete command."""

    note_type_id: int
    deck_id: DeckId
    target_field_name: str


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


class StateDto(TypedDict):
    schemaVersion: Literal[1]
    smartFields: list[SmartFieldDto]
    noteTypes: list[NoteTypeDto]
    decks: list[DeckDto]
    globalDeckId: DeckId
    account: AppState
    defaults: GenerationDefaultsDto


def _require(payload: dict[str, Any], key: str) -> Any:
    if key not in payload:
        raise ValueError(f"Missing required field: {key}")
    return payload[key]


def parse_chat_generation_settings(payload: dict[str, Any]) -> ChatGenerationSettings:
    provider = _require(payload, "provider")
    model = _require(payload, "model")
    reasoning_level = _require(payload, "reasoningLevel")
    web_search_enabled = _require(payload, "webSearchEnabled")

    if not isinstance(provider, str) or provider not in provider_model_map:
        raise ValueError(f"Unknown chat provider: {provider}")
    if not isinstance(model, str) or model not in provider_model_map[provider]:
        raise ValueError(f"Model {model} is not available for provider {provider}")
    if reasoning_level not in CHAT_REASONING_LEVELS:
        raise ValueError(f"Unknown reasoning level: {reasoning_level}")
    if not isinstance(web_search_enabled, bool):
        raise ValueError("webSearchEnabled must be a boolean")

    return ChatGenerationSettings(
        provider=provider,
        model=model,
        reasoning_level=reasoning_level,
        web_search_enabled=web_search_enabled,
    )


def _smart_field_dto(field: SmartField) -> SmartFieldDto:
    settings = field.settings
    if isinstance(settings, ChatSmartFieldSettings):
        return ChatSmartFieldDto(
            id=field.id,
            noteTypeId=field.note_type_id,
            deckId=field.deck_id,
            targetFieldName=field.target_field_name,
            fieldType="chat",
            enabled=field.enabled,
            settings=ChatSmartFieldSettingsDto(
                promptText=settings.prompt_text,
                provider=settings.provider,
                model=settings.model,
                reasoningLevel=settings.reasoning_level,
                webSearchEnabled=settings.web_search_enabled,
                usesDefaultGenerationSettings=settings.uses_default_generation_settings,
            ),
        )
    if isinstance(settings, TTSSmartFieldSettings):
        return TTSSmartFieldDto(
            id=field.id,
            noteTypeId=field.note_type_id,
            deckId=field.deck_id,
            targetFieldName=field.target_field_name,
            fieldType="tts",
            enabled=field.enabled,
            settings=TTSSmartFieldSettingsDto(
                sourceFieldName=settings.source_field_name,
                provider=settings.provider,
                model=settings.model,
                voiceId=settings.voice_id,
                usesDefaultGenerationSettings=settings.uses_default_generation_settings,
            ),
        )
    return ImageSmartFieldDto(
        id=field.id,
        noteTypeId=field.note_type_id,
        deckId=field.deck_id,
        targetFieldName=field.target_field_name,
        fieldType="image",
        enabled=field.enabled,
        settings=ImageSmartFieldSettingsDto(
            promptText=settings.prompt_text,
            provider=settings.provider,
            model=settings.model,
            usesDefaultGenerationSettings=settings.uses_default_generation_settings,
        ),
    )
