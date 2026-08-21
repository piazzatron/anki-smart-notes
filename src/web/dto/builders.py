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

from typing import TYPE_CHECKING, Any

from ...config import config
from ...constants import GLOBAL_DECK_ID
from ...models import image_provider_model_map, provider_model_map
from ...models.smart_fields import (
    ChatSmartFieldSettings,
    GenerationDefaults,
    SmartField,
    TTSSmartFieldSettings,
)
from ...voice_catalog import get_voice_catalog
from .models import (
    CHAT_REASONING_LEVELS,
    AccountDto,
    ChatGenerationSettingsDto,
    ChatSmartFieldDto,
    ChatSmartFieldSettingsDto,
    DeckDto,
    FeatureFlagsDto,
    GenerationDefaultsDto,
    ImageGenerationSettingsDto,
    ImageSmartFieldDto,
    ImageSmartFieldSettingsDto,
    NoteTypeDto,
    SettingsDto,
    SmartFieldDto,
    StateDto,
    TTSGenerationSettingsDto,
    TTSSmartFieldDto,
    TTSSmartFieldSettingsDto,
    VoiceCatalogDto,
    VoiceCatalogItemDto,
)

if TYPE_CHECKING:
    from anki.cards import CardId
    from anki.decks import DeckId
    from anki.notes import Note

    from ...app_state import AppState
    from ...feature_flags import FeatureFlags


def build_state(
    *,
    defaults: GenerationDefaults,
    note_types: list[tuple[int, str, list[str]]],
    decks: dict[DeckId, str],
    smart_fields: list[SmartField],
    account: AppState,
    auth_token: str | None,
    feature_flags: FeatureFlags,
    settings: SettingsDto,
    app_version: str,
) -> StateDto:
    """The full `state` event payload. Whole-state push: every state event
    carries everything, so consumers replace their model wholesale."""
    note_type_ids = {note_type_id for note_type_id, _, _ in note_types}
    deck_ids = set(decks)

    return StateDto(
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
        account=AccountDto(
            status=account["status"],
            plan=account["plan"],
            email=account["email"],
            authToken=auth_token,
        ),
        featureFlags=FeatureFlagsDto(
            reviewFreeMonth=feature_flags.review_free_month,
        ),
        settings=settings,
        appVersion=app_version,
        defaults=build_generation_defaults(defaults),
    )


def build_generation_defaults(defaults: GenerationDefaults) -> GenerationDefaultsDto:
    """The default chat/TTS/image generation settings, in wire form."""
    return GenerationDefaultsDto(
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
        didDismissReviewPrompt=config.did_dismiss_review_prompt,
        didDismissDiscordPrompt=config.did_dismiss_discord_prompt,
    )


def build_catalog() -> dict[str, Any]:
    """Static model facts sent once when an SSE connection is established."""
    return {
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
