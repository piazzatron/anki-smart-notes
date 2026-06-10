# type: ignore

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

import asyncio
import threading
from unittest.mock import MagicMock

import pytest

from src.event_bus import EventBus, StateInvalidated, event_bus, republish_state
from src.models.smart_fields import (
    ChatGenerationSettings,
    ChatSmartFieldSettings,
    GenerationDefaults,
    ImageGenerationSettings,
    SmartField,
    TTSGenerationSettings,
    TTSSmartFieldSettings,
)
from src.web import dto
from tests.fixtures import DECK_ID, NOTE_TYPE_ID, MockNote

GENERATION_DEFAULTS = GenerationDefaults(
    chat=ChatGenerationSettings(
        provider="openai",
        model="gpt-5",
        reasoning_level="off",
        web_search_enabled=False,
    ),
    tts=TTSGenerationSettings(provider="openai", model="tts-1", voice_id="alloy"),
    image=ImageGenerationSettings(provider="replicate", model="flux-schnell"),
)


def _patch_state_sources(monkeypatch) -> None:
    monkeypatch.setattr(
        dto,
        "get_note_types_with_fields",
        lambda: [(NOTE_TYPE_ID, "Basic", ["Front", "Back"])],
    )
    monkeypatch.setattr(dto, "deck_id_to_name_map", lambda: {DECK_ID: "Spanish::Verbs"})


def _patch_service_defaults(monkeypatch) -> None:
    monkeypatch.setattr(
        dto.smart_field_service,
        "get_generation_defaults",
        lambda: GENERATION_DEFAULTS,
    )
    monkeypatch.setattr(
        dto.smart_field_service, "get_chat_defaults", lambda: GENERATION_DEFAULTS.chat
    )
    monkeypatch.setattr(
        dto.smart_field_service, "get_tts_defaults", lambda: GENERATION_DEFAULTS.tts
    )
    monkeypatch.setattr(
        dto.smart_field_service,
        "get_image_defaults",
        lambda: GENERATION_DEFAULTS.image,
    )


# -- EventBus --


@pytest.mark.asyncio
async def test_event_bus_delivers_across_threads():
    bus = EventBus()
    loop = asyncio.get_running_loop()
    queue: asyncio.Queue = asyncio.Queue()
    bus.subscribe(loop, queue)

    thread = threading.Thread(target=lambda: bus.publish(StateInvalidated()))
    thread.start()
    thread.join()

    event = await asyncio.wait_for(queue.get(), timeout=2)
    assert isinstance(event, StateInvalidated)


@pytest.mark.asyncio
async def test_event_bus_unsubscribe_stops_delivery():
    bus = EventBus()
    loop = asyncio.get_running_loop()
    queue: asyncio.Queue = asyncio.Queue()
    bus.subscribe(loop, queue)
    bus.unsubscribe(queue)

    bus.publish(StateInvalidated())
    await asyncio.sleep(0)
    assert queue.empty()


# -- DTOs --


def _chat_smart_field() -> SmartField:
    return SmartField(
        id="sf-1",
        note_type_id=NOTE_TYPE_ID,
        deck_id=DECK_ID,
        target_field_name="Back",
        enabled=True,
        settings=ChatSmartFieldSettings(
            prompt_text="Define {{Front}}",
            provider="openai",
            model="gpt-5",
            web_search_enabled=False,
            reasoning_level="off",
            uses_default_generation_settings=True,
        ),
    )


def test_build_state_shape(monkeypatch):
    _patch_service_defaults(monkeypatch)
    _patch_state_sources(monkeypatch)
    monkeypatch.setattr(
        dto.smart_field_service, "get_all_smart_fields", lambda: [_chat_smart_field()]
    )

    state = dto.build_state()

    assert state["schemaVersion"] == dto.SCHEMA_VERSION
    assert state["noteTypes"] == [
        {"id": NOTE_TYPE_ID, "name": "Basic", "fields": ["Front", "Back"]}
    ]
    assert state["decks"] == [{"id": DECK_ID, "name": "Spanish::Verbs"}]
    assert state["globalDeckId"] == dto.GLOBAL_DECK_ID
    assert state["defaults"] == {
        "chat": {
            "provider": "openai",
            "model": "gpt-5",
            "reasoningLevel": "off",
            "webSearchEnabled": False,
        },
        "tts": {"provider": "openai", "model": "tts-1", "voiceId": "alloy"},
        "image": {"provider": "replicate", "model": "flux-schnell"},
    }
    assert state["smartFields"] == [
        {
            "id": "sf-1",
            "noteTypeId": NOTE_TYPE_ID,
            "deckId": DECK_ID,
            "targetFieldName": "Back",
            "fieldType": "chat",
            "enabled": True,
            "settings": {
                "promptText": "Define {{Front}}",
                "provider": "openai",
                "model": "gpt-5",
                "webSearchEnabled": False,
                "reasoningLevel": "off",
                "usesDefaultGenerationSettings": True,
            },
        }
    ]


def test_build_selection_changed():
    note = MockNote({"Front": "dog", "Back": ""}, note_id=42)

    payload = dto.build_selection_changed(note, deck_id=7)

    assert payload == {
        "note": {
            "id": 42,
            "noteTypeId": NOTE_TYPE_ID,
            "deckId": 7,
            "fields": {"Front": "dog", "Back": ""},
        }
    }


def test_build_selection_cleared():
    assert dto.build_selection_cleared(3) == {"note": None, "count": 3}


# -- Command payload parsing --


def test_parse_smart_field_create_chat_fills_defaults(monkeypatch):
    _patch_service_defaults(monkeypatch)

    create = dto.parse_smart_field_create(
        {
            "noteTypeId": NOTE_TYPE_ID,
            "deckId": int(DECK_ID),
            "targetFieldName": "Back",
            "fieldType": "chat",
            "settings": {"promptText": "Define {{Front}}"},
        }
    )

    assert create.note_type_id == NOTE_TYPE_ID
    assert create.deck_id == DECK_ID
    assert create.target_field_name == "Back"
    assert create.enabled is True
    assert create.settings == ChatSmartFieldSettings(
        prompt_text="Define {{Front}}",
        provider="openai",
        model="gpt-5",
        reasoning_level="off",
        web_search_enabled=False,
        uses_default_generation_settings=True,
    )


def test_parse_smart_field_create_tts(monkeypatch):
    _patch_service_defaults(monkeypatch)

    create = dto.parse_smart_field_create(
        {
            "noteTypeId": NOTE_TYPE_ID,
            "deckId": int(DECK_ID),
            "targetFieldName": "Audio",
            "fieldType": "tts",
            "enabled": False,
            "settings": {"sourceFieldName": "Front", "voiceId": "echo"},
        }
    )

    assert create.enabled is False
    assert create.settings == TTSSmartFieldSettings(
        source_field_name="Front",
        provider="openai",
        model="tts-1",
        voice_id="echo",
        uses_default_generation_settings=True,
    )


def test_parse_smart_field_create_rejects_missing_prompt(monkeypatch):
    _patch_service_defaults(monkeypatch)

    with pytest.raises(ValueError, match="promptText"):
        dto.parse_smart_field_create(
            {
                "noteTypeId": NOTE_TYPE_ID,
                "deckId": int(DECK_ID),
                "targetFieldName": "Back",
                "fieldType": "chat",
                "settings": {},
            }
        )


def test_parse_smart_field_create_rejects_unknown_type(monkeypatch):
    _patch_service_defaults(monkeypatch)

    with pytest.raises(ValueError, match="Unknown fieldType"):
        dto.parse_smart_field_create(
            {
                "noteTypeId": NOTE_TYPE_ID,
                "deckId": int(DECK_ID),
                "targetFieldName": "Back",
                "fieldType": "video",
                "settings": {},
            }
        )


def test_parse_smart_field_ref_requires_keys():
    with pytest.raises(ValueError, match="targetFieldName"):
        dto.parse_smart_field_ref({"noteTypeId": 1, "deckId": 2})


def test_parse_generation_defaults_round_trips():
    parsed = dto.parse_generation_defaults(
        {
            "chat": {
                "provider": "openai",
                "model": "gpt-5",
                "reasoningLevel": "off",
                "webSearchEnabled": False,
            },
            "tts": {"provider": "openai", "model": "tts-1", "voiceId": "alloy"},
            "image": {"provider": "replicate", "model": "flux-schnell"},
        }
    )
    assert parsed == GENERATION_DEFAULTS


# -- republish_state --


def test_republish_state_publishes_after_call(monkeypatch):
    published = []
    monkeypatch.setattr(event_bus, "publish", published.append)

    @republish_state
    def mutate(value: int) -> int:
        # Publish must happen after the mutation, not before.
        assert published == []
        return value * 2

    assert mutate(21) == 42
    assert len(published) == 1
    assert isinstance(published[0], StateInvalidated)
    assert mutate.__name__ == "mutate"


def test_republish_state_does_not_publish_on_exception(monkeypatch):
    published = []
    monkeypatch.setattr(event_bus, "publish", published.append)

    @republish_state
    def explode() -> None:
        raise ValueError("boom")

    with pytest.raises(ValueError):
        explode()
    assert published == []


# -- Hook adapters --


def test_operation_did_execute_publishes_on_notetype_or_deck_change(monkeypatch):
    from types import SimpleNamespace

    from src.web import hook_adapters

    bus = MagicMock()
    monkeypatch.setattr(hook_adapters, "event_bus", bus)
    monkeypatch.setattr(hook_adapters, "rebuild_deck_cache", lambda: None)

    hook_adapters.on_operation_did_execute(
        SimpleNamespace(notetype=False, deck=False), None
    )
    bus.publish.assert_not_called()

    hook_adapters.on_operation_did_execute(
        SimpleNamespace(notetype=False, deck=True), None
    )
    bus.publish.assert_called_once()
    assert isinstance(bus.publish.call_args.args[0], StateInvalidated)
