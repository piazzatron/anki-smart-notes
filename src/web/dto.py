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

from ..config import config
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
    ImagePromptTestRequest,
    ImageSmartFieldSettings,
    SaveTestResultRequest,
    SmartField,
    SmartFieldCreate,
    SmartFieldSettings,
    TextPromptTestRequest,
    TTSGenerationSettings,
    TTSPromptTestRequest,
    TTSSmartFieldSettings,
)
from ..services.settings_service import Settings
from ..voice_catalog import VoiceGender, VoicePriceTier, get_voice_catalog

if TYPE_CHECKING:
    from anki.notes import Note

    from ..app_state import AppState
    from ..feature_flags import FeatureFlags

SCHEMA_VERSION: Literal[1] = 1
CHAT_REASONING_LEVELS: list[ChatReasoningLevel] = ["off", "low", "high"]


def build_state(
    *,
    defaults: GenerationDefaults,
    note_types: list[tuple[int, str, list[str]]],
    decks: dict[DeckId, str],
    smart_fields: list[SmartField],
    account: AppState,
    feature_flags: FeatureFlags,
    settings: SettingsDto,
    app_version: str,
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
        featureFlags=FeatureFlagsDto(
            reviewFreeMonth=feature_flags.review_free_month,
        ),
        settings=settings,
        appVersion=app_version,
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


def build_settings() -> SettingsDto:
    """Build the web settings projection from the persisted Anki config."""
    return SettingsDto(
        generateAtReview=config.generate_at_review,
        regenerateWhenBatching=config.regenerate_notes_when_batching,
        debug=config.debug,
        legacyOpenAiEnabled=config.legacy_support is True,
        legacyOpenAiKey=config.openai_api_key,
        legacyOpenAiModel=config.legacy_openai_model,
        legacyOpenAiHost=config.openai_endpoint,
        showWizardCompletion=config.show_wizard_completion,
        didDismissDiscordPrompt=config.did_dismiss_discord_prompt,
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


def build_voice_catalog() -> VoiceCatalogDto:
    """Large, static voice reference loaded lazily by the voice screen."""
    return VoiceCatalogDto(
        schemaVersion=SCHEMA_VERSION,
        voices=[
            VoiceCatalogItemDto(
                provider=voice["provider"],
                voiceId=voice["voice_id"],
                model=voice["model"],
                name=voice["name"],
                gender=voice["gender"],
                language=voice["language"],
                priceTier=voice["price_tier"],
            )
            for voice in get_voice_catalog()
        ],
    )


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


def parse_smart_field_update(payload: dict[str, Any]) -> SmartField:
    smart_field = parse_smart_field_create(payload)
    return SmartField(
        id=_require_string(payload, "id"),
        note_type_id=smart_field.note_type_id,
        deck_id=smart_field.deck_id,
        target_field_name=smart_field.target_field_name,
        enabled=smart_field.enabled,
        settings=smart_field.settings,
    )


def parse_smart_field_id(payload: dict[str, Any]) -> str:
    return _require_string(payload, "id")


def parse_generation_defaults(payload: dict[str, Any]) -> GenerationDefaults:
    chat = _require(payload, "chat")
    tts = _require(payload, "tts")
    image = _require(payload, "image")
    return GenerationDefaults(
        chat=parse_chat_generation_settings(chat),
        tts=parse_tts_generation_settings(tts),
        image=parse_image_generation_settings(image),
    )


def parse_text_prompt_test(payload: dict[str, Any]) -> TextPromptTestRequest:
    return TextPromptTestRequest(
        card_id=_parse_optional_card_id(payload),
        prompt=_parse_non_empty_string(payload, "prompt"),
        settings=parse_chat_generation_settings(_require_object(payload, "settings")),
    )


def parse_image_prompt_test(payload: dict[str, Any]) -> ImagePromptTestRequest:
    return ImagePromptTestRequest(
        card_id=_parse_optional_card_id(payload),
        prompt=_parse_non_empty_string(payload, "prompt"),
        settings=parse_image_generation_settings(_require_object(payload, "settings")),
    )


def parse_tts_prompt_test(payload: dict[str, Any]) -> TTSPromptTestRequest:
    return TTSPromptTestRequest(
        card_id=_parse_optional_card_id(payload),
        text=_parse_non_empty_string(payload, "text"),
        settings=parse_tts_generation_settings(_require_object(payload, "settings")),
    )


def parse_save_test_result(payload: dict[str, Any]) -> SaveTestResultRequest:
    return SaveTestResultRequest(
        token=_parse_non_empty_string(payload, "token"),
        card_id=_parse_card_id(payload),
        field_name=_parse_non_empty_string(payload, "fieldName"),
    )


def parse_settings(payload: dict[str, Any]) -> Settings:
    generate_at_review = _require_boolean(payload, "generateAtReview")
    regenerate_when_batching = _require_boolean(payload, "regenerateWhenBatching")
    debug = _require_boolean(payload, "debug")
    legacy_openai_key = _require_optional_string(payload, "legacyOpenAiKey")
    legacy_openai_model = _require_string(payload, "legacyOpenAiModel")
    legacy_openai_host = _require_optional_string(payload, "legacyOpenAiHost")
    show_wizard_completion = _require_boolean(payload, "showWizardCompletion")
    did_dismiss_discord_prompt = _require_boolean(payload, "didDismissDiscordPrompt")

    return Settings(
        generate_at_review=generate_at_review,
        regenerate_when_batching=regenerate_when_batching,
        debug=debug,
        legacy_openai_key=legacy_openai_key,
        legacy_openai_model=legacy_openai_model,
        legacy_openai_host=legacy_openai_host,
        show_wizard_completion=show_wizard_completion,
        did_dismiss_discord_prompt=did_dismiss_discord_prompt,
    )


def parse_prompt_generate(payload: dict[str, Any]) -> PromptGenerateRequest:
    note_type_id = _require_integer(payload, "noteTypeId")
    deck_id = _require_integer(payload, "deckId")
    target_field_name = _require_string(payload, "targetFieldName")
    field_type = _require_string(payload, "fieldType")
    generation_prompt = _require_string(payload, "generationPrompt")

    if field_type not in ("chat", "image"):
        raise ValueError("fieldType must be chat or image")

    return PromptGenerateRequest(
        note_type_id=note_type_id,
        deck_id=cast(DeckId, deck_id),
        target_field_name=target_field_name,
        field_type=field_type,
        generation_prompt=generation_prompt,
    )


def parse_feedback_message(payload: dict[str, Any]) -> str:
    message = _require_string(payload, "message").strip()
    if not message:
        raise ValueError("message must be a non-empty string")
    return message


def parse_auth_logout(payload: object) -> None:
    if not isinstance(payload, dict) or payload:
        raise ValueError("auth.logout payload must be an empty object")


def parse_auth_exchange_code(payload: dict[str, Any]) -> str:
    code = _require_string(payload, "code").strip().upper()
    if not code:
        raise ValueError("Please enter a code.")
    return code


def parse_account_refresh(payload: object) -> None:
    if not isinstance(payload, dict) or payload:
        raise ValueError("account.refresh payload must be an empty object")


def parse_ui_open_browser(payload: object) -> None:
    if not isinstance(payload, dict) or payload:
        raise ValueError("ui.openBrowser payload must be an empty object")


@dataclass(frozen=True)
class PromptGenerateRequest:
    note_type_id: int
    deck_id: DeckId
    target_field_name: str
    field_type: Literal["chat", "image"]
    generation_prompt: str


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


class StateDto(TypedDict):
    schemaVersion: Literal[1]
    smartFields: list[SmartFieldDto]
    noteTypes: list[NoteTypeDto]
    decks: list[DeckDto]
    globalDeckId: DeckId
    account: AppState
    featureFlags: FeatureFlagsDto
    settings: SettingsDto
    appVersion: str
    defaults: GenerationDefaultsDto


class VoiceCatalogDto(TypedDict):
    schemaVersion: Literal[1]
    voices: list[VoiceCatalogItemDto]


class VoiceCatalogItemDto(TypedDict):
    provider: TTSProviders
    voiceId: str
    model: str
    name: str
    gender: VoiceGender
    language: str
    priceTier: VoicePriceTier


def _require(payload: dict[str, Any], key: str) -> Any:
    if key not in payload:
        raise ValueError(f"Missing required field: {key}")
    return payload[key]


def _require_boolean(payload: dict[str, Any], key: str) -> bool:
    value = _require(payload, key)
    if not isinstance(value, bool):
        raise ValueError(f"{key} must be a boolean")
    return value


def _require_integer(payload: dict[str, Any], key: str) -> int:
    value = _require(payload, key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{key} must be an integer")
    return value


def _require_string(payload: dict[str, Any], key: str) -> str:
    value = _require(payload, key)
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string")
    return value


def _require_optional_string(payload: dict[str, Any], key: str) -> str | None:
    value = _require(payload, key)
    if value is not None and not isinstance(value, str):
        raise ValueError(f"{key} must be a string or null")
    return value


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


def parse_image_generation_settings(payload: dict[str, Any]) -> ImageGenerationSettings:
    provider = _require(payload, "provider")
    model = _require(payload, "model")
    if not isinstance(provider, str) or provider not in image_provider_model_map:
        raise ValueError(f"Unknown image provider: {provider}")
    if not isinstance(model, str) or model not in image_provider_model_map[provider]:
        raise ValueError(f"Model {model} is not available for provider {provider}")
    return ImageGenerationSettings(provider=provider, model=model)


def parse_tts_generation_settings(payload: dict[str, Any]) -> TTSGenerationSettings:
    provider = _require(payload, "provider")
    model = _require(payload, "model")
    voice_id = _require(payload, "voiceId")
    if not isinstance(provider, str) or not isinstance(model, str):
        raise ValueError("Voice provider and model must be strings")
    if not isinstance(voice_id, str) or not voice_id:
        raise ValueError("voiceId must be a non-empty string")
    if not any(
        voice["provider"] == provider
        and voice["model"] == model
        and voice["voice_id"] == voice_id
        for voice in get_voice_catalog()
    ):
        raise ValueError("Unknown provider, model, and voice combination")
    return TTSGenerationSettings(
        provider=cast(TTSProviders, provider),
        model=cast(TTSModels, model),
        voice_id=voice_id,
    )


def _parse_card_id(payload: dict[str, Any]) -> CardId:
    card_id = _require(payload, "cardId")
    if isinstance(card_id, bool) or not isinstance(card_id, int):
        raise ValueError("cardId must be an integer")
    return cast(CardId, card_id)


def _parse_optional_card_id(payload: dict[str, Any]) -> CardId | None:
    card_id = payload.get("cardId")
    if card_id is None:
        return None
    if isinstance(card_id, bool) or not isinstance(card_id, int):
        raise ValueError("cardId must be an integer")
    return cast(CardId, card_id)


def _parse_non_empty_string(payload: dict[str, Any], key: str) -> str:
    value = _require(payload, key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty string")
    return value


def _require_object(payload: dict[str, Any], key: str) -> dict[str, Any]:
    value = _require(payload, key)
    if not isinstance(value, dict):
        raise ValueError(f"{key} must be an object")
    return value


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
