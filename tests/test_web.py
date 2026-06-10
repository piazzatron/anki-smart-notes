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

import pytest

from src.models.smart_fields import ChatSmartFieldSettings, SmartField
from src.web import dto
from src.web.event_bus import EventBus, StateInvalidated
from tests.fixtures import DECK_ID, NOTE_TYPE_ID, MockNote

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
    monkeypatch.setattr(
        dto.smart_field_service, "get_all_smart_fields", lambda: [_chat_smart_field()]
    )

    state = dto.build_state()

    assert state["schemaVersion"] == dto.SCHEMA_VERSION
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
