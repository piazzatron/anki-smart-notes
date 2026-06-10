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

from src.models.smart_fields import (
    ChatGenerationSettings,
    ChatSmartFieldSettings,
    GenerationDefaults,
    ImageGenerationSettings,
    SmartField,
    TTSGenerationSettings,
    TTSSmartFieldSettings,
)
from src.web import commands, dto
from src.web.event_bus import EventBus, StateInvalidated
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
    monkeypatch.setattr(
        dto.smart_field_service, "get_all_smart_fields", lambda: [_chat_smart_field()]
    )

    state = dto.build_state()

    assert state["schemaVersion"] == dto.SCHEMA_VERSION
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


# -- Commands --


def _patch_command_deps(monkeypatch):
    service = MagicMock()
    bus = MagicMock()
    monkeypatch.setattr(commands, "smart_field_service", service)
    monkeypatch.setattr(commands, "event_bus", bus)
    return service, bus


def _assert_published_invalidation(bus: MagicMock) -> None:
    bus.publish.assert_called_once()
    assert isinstance(bus.publish.call_args.args[0], StateInvalidated)


def test_save_smart_field_command(monkeypatch):
    service, bus = _patch_command_deps(monkeypatch)
    create = MagicMock()

    commands.save_smart_field(create)

    service.save_smart_field.assert_called_once_with(create)
    _assert_published_invalidation(bus)


def test_replace_all_smart_fields_command(monkeypatch):
    service, bus = _patch_command_deps(monkeypatch)

    commands.replace_all_smart_fields([])

    service.replace_all_smart_fields.assert_called_once_with([])
    _assert_published_invalidation(bus)


def test_delete_smart_field_command(monkeypatch):
    service, bus = _patch_command_deps(monkeypatch)

    commands.delete_smart_field(NOTE_TYPE_ID, DECK_ID, "Back")

    service.delete_smart_field.assert_called_once_with(NOTE_TYPE_ID, DECK_ID, "Back")
    _assert_published_invalidation(bus)


def test_save_generation_defaults_command(monkeypatch):
    service, bus = _patch_command_deps(monkeypatch)

    commands.save_generation_defaults(GENERATION_DEFAULTS)

    service.save_chat_defaults.assert_called_once_with(GENERATION_DEFAULTS.chat)
    service.save_tts_defaults.assert_called_once_with(GENERATION_DEFAULTS.tts)
    service.save_image_defaults.assert_called_once_with(GENERATION_DEFAULTS.image)
    _assert_published_invalidation(bus)


def test_restore_generation_defaults_command(monkeypatch):
    service, bus = _patch_command_deps(monkeypatch)

    commands.restore_generation_defaults()

    service.restore_generation_defaults.assert_called_once_with()
    _assert_published_invalidation(bus)
