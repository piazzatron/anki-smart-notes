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

# The web UI wire format, defined in one place (see specs/web-ui-architecture.md
# in the top-level repo). Pure functions mapping domain objects to JSON-ready
# dicts and command payloads back to domain objects. Anything that reads
# Anki/domain state must be called on the main thread.

import dataclasses
from typing import Any, Optional, cast

from anki.decks import DeckId
from anki.notes import Note

from ..app_state import app_state
from ..constants import GLOBAL_DECK_ID
from ..decks import deck_id_to_name_map
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
    TTSGenerationSettings,
    TTSSmartFieldSettings,
)
from ..services.smart_field_service import smart_field_service
from ..utils.notes_utils import get_note_types_with_fields

SCHEMA_VERSION = 1
CHAT_REASONING_LEVELS: list[ChatReasoningLevel] = ["off", "low", "high"]


def build_state() -> dict[str, Any]:
    """The full `state` event payload. Whole-state push: every state event
    carries everything, so consumers replace their model wholesale."""
    defaults = smart_field_service.get_generation_defaults()
    note_types = get_note_types_with_fields()
    decks = deck_id_to_name_map()
    note_type_ids = {note_type_id for note_type_id, _, _ in note_types}
    deck_ids = set(decks)

    return {
        "schemaVersion": SCHEMA_VERSION,
        "smartFields": [
            _smart_field_dto(field)
            for field in smart_field_service.get_all_smart_fields()
            if field.note_type_id in note_type_ids and field.deck_id in deck_ids
        ],
        # Note types and decks let the UI render names for the IDs that smart
        # fields and selection events carry (and feed authoring pickers).
        "noteTypes": [
            {"id": note_type_id, "name": name, "fields": fields}
            for note_type_id, name, fields in note_types
        ],
        "decks": [
            {"id": deck_id, "name": name}
            for deck_id, name in sorted(decks.items(), key=lambda item: item[1])
        ],
        # The pseudo-deck meaning "applies to all decks" — present in `decks`
        # with a friendly name, but scoping UI needs to special-case it.
        "globalDeckId": GLOBAL_DECK_ID,
        "account": app_state.state,
        "defaults": {
            "chat": _camelize_keys(dataclasses.asdict(defaults.chat)),
            "tts": _camelize_keys(dataclasses.asdict(defaults.tts)),
            "image": _camelize_keys(dataclasses.asdict(defaults.image)),
        },
    }


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


def build_selection_changed(note: Note, deck_id: Optional[int]) -> dict[str, Any]:
    """`anki.browserSelectionChanged` payload for a single selected note."""
    return {
        "note": {
            "id": note.id,
            "noteTypeId": note.mid,
            "deckId": deck_id,
            "fields": {name: note[name] for name in note.keys()},  # noqa: SIM118
        }
    }


def build_selection_cleared(count: int) -> dict[str, Any]:
    """`anki.browserSelectionChanged` payload when not exactly one note is
    selected — note contents only ship for single selection."""
    return {"note": None, "count": count}


# -- Command payload parsing (wire → domain). Raise ValueError on bad shapes;
# the server maps that to a 400 with the message. --


def parse_smart_field_create(payload: dict[str, Any]) -> SmartFieldCreate:
    field_type = _require(payload, "fieldType")
    settings_raw = _require(payload, "settings")

    settings: SmartFieldSettings
    if field_type == "chat":
        chat_defaults = smart_field_service.get_chat_defaults()
        settings = ChatSmartFieldSettings(
            prompt_text=_require(settings_raw, "promptText"),
            provider=cast(
                ChatProviders, settings_raw.get("provider", chat_defaults.provider)
            ),
            model=cast(ChatModels, settings_raw.get("model", chat_defaults.model)),
            reasoning_level=cast(
                ChatReasoningLevel,
                settings_raw.get("reasoningLevel", chat_defaults.reasoning_level),
            ),
            web_search_enabled=settings_raw.get(
                "webSearchEnabled", chat_defaults.web_search_enabled
            ),
            uses_default_generation_settings=settings_raw.get(
                "usesDefaultGenerationSettings", True
            ),
        )
    elif field_type == "tts":
        tts_defaults = smart_field_service.get_tts_defaults()
        settings = TTSSmartFieldSettings(
            source_field_name=_require(settings_raw, "sourceFieldName"),
            provider=cast(
                TTSProviders, settings_raw.get("provider", tts_defaults.provider)
            ),
            model=cast(TTSModels, settings_raw.get("model", tts_defaults.model)),
            voice_id=settings_raw.get("voiceId", tts_defaults.voice_id),
            uses_default_generation_settings=settings_raw.get(
                "usesDefaultGenerationSettings", True
            ),
        )
    elif field_type == "image":
        image_defaults = smart_field_service.get_image_defaults()
        settings = ImageSmartFieldSettings(
            prompt_text=_require(settings_raw, "promptText"),
            provider=cast(
                ImageProviders, settings_raw.get("provider", image_defaults.provider)
            ),
            model=cast(ImageModels, settings_raw.get("model", image_defaults.model)),
            uses_default_generation_settings=settings_raw.get(
                "usesDefaultGenerationSettings", True
            ),
        )
    else:
        raise ValueError(f"Unknown fieldType: {field_type}")

    return SmartFieldCreate(
        note_type_id=int(_require(payload, "noteTypeId")),
        deck_id=cast(DeckId, int(_require(payload, "deckId"))),
        target_field_name=_require(payload, "targetFieldName"),
        enabled=payload.get("enabled", True),
        settings=settings,
    )


def parse_smart_field_ref(payload: dict[str, Any]) -> "SmartFieldRef":
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
        chat=ChatGenerationSettings(
            provider=cast(ChatProviders, _require(chat, "provider")),
            model=cast(ChatModels, _require(chat, "model")),
            reasoning_level=cast(ChatReasoningLevel, _require(chat, "reasoningLevel")),
            web_search_enabled=_require(chat, "webSearchEnabled"),
        ),
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


@dataclasses.dataclass(frozen=True)
class SmartFieldRef:
    """Wire identity of a smart field, used by the delete command."""

    note_type_id: int
    deck_id: DeckId
    target_field_name: str


def _require(payload: dict[str, Any], key: str) -> Any:
    if key not in payload:
        raise ValueError(f"Missing required field: {key}")
    return payload[key]


def _smart_field_dto(field: SmartField) -> dict[str, Any]:
    return {
        "id": field.id,
        "noteTypeId": field.note_type_id,
        "deckId": field.deck_id,
        "targetFieldName": field.target_field_name,
        "fieldType": field.field_type,
        "enabled": field.enabled,
        "settings": _camelize_keys(dataclasses.asdict(field.settings)),
    }


def _camelize_keys(data: dict[str, Any]) -> dict[str, Any]:
    return {_camelize(key): value for key, value in data.items()}


def _camelize(snake: str) -> str:
    head, *rest = snake.split("_")
    return head + "".join(part.title() for part in rest)
