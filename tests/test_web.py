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
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from src.app_state import AppStateManager
from src.event_bus import (
    BrowserSelectionChanged,
    EventBus,
    StateInvalidated,
    event_bus,
    republish_state,
)
from src.models.smart_fields import (
    ChatGenerationSettings,
    ChatSmartFieldSettings,
    GenerationDefaults,
    ImageGenerationSettings,
    ImageSmartFieldSettings,
    SmartField,
    TTSGenerationSettings,
    TTSSmartFieldSettings,
)
from src.web import dto
from tests.fixtures import DECK_ID, NOTE_TYPE_ID, MockCard, MockNote

GENERATION_DEFAULTS = GenerationDefaults(
    chat=ChatGenerationSettings(
        provider="openai",
        model="gpt-5",
        reasoning_level="off",
        web_search_enabled=False,
    ),
    tts=TTSGenerationSettings(provider="openai", model="tts-1", voice_id="alloy"),
    image=ImageGenerationSettings(provider="replicate", model="flux-dev"),
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


@pytest.mark.asyncio
async def test_event_bus_replays_latest_browser_selection_to_new_subscribers():
    bus = EventBus()
    selection = BrowserSelectionChanged({"note": {"cardId": 42}})
    bus.publish(selection)
    queue: asyncio.Queue = asyncio.Queue()

    bus.subscribe(asyncio.get_running_loop(), queue)

    assert await asyncio.wait_for(queue.get(), timeout=2) == selection


@pytest.mark.asyncio
async def test_event_bus_can_clear_replayed_browser_selection():
    bus = EventBus()
    bus.publish(BrowserSelectionChanged({"note": {"cardId": 42}}))
    bus.clear_browser_selection()
    queue: asyncio.Queue = asyncio.Queue()

    bus.subscribe(asyncio.get_running_loop(), queue)
    await asyncio.sleep(0)

    assert queue.empty()


def test_subscription_state_change_invalidates_web_state(monkeypatch):
    publish = MagicMock()
    monkeypatch.setattr("src.app_state.event_bus.publish", publish)
    monkeypatch.setattr("src.app_state.config", SimpleNamespace(auth_token=None))

    manager = AppStateManager()
    manager.update_subscription_state()

    assert isinstance(publish.call_args.args[0], StateInvalidated)


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


def test_build_state_shape():
    account = {
        "subscription": "FREE_TRIAL_ACTIVE",
        "plan": {
            "planId": "free",
            "planName": "Free Trial",
            "notesUsed": 12,
            "notesLimit": 50,
            "daysLeft": 5,
            "textCreditsUsed": 20,
            "textCreditsCapacity": 100,
            "voiceCreditsUsed": 10,
            "voiceCreditsCapacity": 100,
            "imageCreditsUsed": 0,
            "imageCreditsCapacity": 100,
            "totalCreditsUsed": 30,
            "totalCreditsCapacity": 300,
        },
    }

    state = dto.build_state(
        defaults=GENERATION_DEFAULTS,
        note_types=[(NOTE_TYPE_ID, "Basic", ["Front", "Back"])],
        decks={DECK_ID: "Spanish::Verbs"},
        smart_fields=[_chat_smart_field()],
        account=account,
    )

    assert state["schemaVersion"] == dto.SCHEMA_VERSION
    assert state["noteTypes"] == [
        {"id": NOTE_TYPE_ID, "name": "Basic", "fields": ["Front", "Back"]}
    ]
    assert state["decks"] == [{"id": DECK_ID, "name": "Spanish::Verbs"}]
    assert state["globalDeckId"] == dto.GLOBAL_DECK_ID
    assert state["account"] == account
    assert state["defaults"] == {
        "chat": {
            "provider": "openai",
            "model": "gpt-5",
            "reasoningLevel": "off",
            "webSearchEnabled": False,
        },
        "tts": {"provider": "openai", "model": "tts-1", "voiceId": "alloy"},
        "image": {"provider": "replicate", "model": "flux-dev"},
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


def test_build_state_excludes_smart_fields_with_missing_anki_references():
    valid_field = _chat_smart_field()
    state = dto.build_state(
        defaults=GENERATION_DEFAULTS,
        note_types=[(NOTE_TYPE_ID, "Basic", ["Front", "Back"])],
        decks={DECK_ID: "Spanish::Verbs"},
        smart_fields=[
            valid_field,
            replace(valid_field, id="missing-note-type", note_type_id=999),
            replace(valid_field, id="missing-deck", deck_id=999),
        ],
        account={"subscription": "UNAUTHENTICATED", "plan": None},
    )

    assert [field["id"] for field in state["smartFields"]] == ["sf-1"]


def test_build_catalog_shape():
    assert dto.build_catalog() == {
        "schemaVersion": dto.SCHEMA_VERSION,
        "chat": {
            "providers": ["auto", "openai", "anthropic", "google"],
            "models": [
                {"id": "auto", "provider": "auto"},
                {"id": "auto-max", "provider": "auto"},
                {"id": "gpt-5-mini", "provider": "openai"},
                {"id": "gpt-5-chat-latest", "provider": "openai"},
                {"id": "gpt-5", "provider": "openai"},
                {"id": "claude-haiku-4-5", "provider": "anthropic"},
                {"id": "claude-sonnet-4-6", "provider": "anthropic"},
                {"id": "claude-opus-4-6", "provider": "anthropic"},
                {"id": "gemini-3.1-flash-lite", "provider": "google"},
                {"id": "gemini-3-flash", "provider": "google"},
                {"id": "gemini-3.1-pro", "provider": "google"},
            ],
            "reasoningLevels": ["off", "low", "high"],
        },
        "image": {
            "providers": ["openai", "google", "replicate"],
            "models": [
                {"id": "gpt-image-1.5-low", "provider": "openai"},
                {"id": "gpt-image-2-low", "provider": "openai"},
                {"id": "gpt-image-1.5-medium", "provider": "openai"},
                {"id": "gpt-image-2-medium", "provider": "openai"},
                {"id": "nano-banana-2", "provider": "google"},
                {"id": "z-image-turbo", "provider": "replicate"},
                {"id": "flux-dev", "provider": "replicate"},
            ],
        },
    }


def test_build_selection_changed():
    note = MockNote({"Front": "dog", "Back": ""}, note_id=42)

    payload = dto.build_selection_changed(note, card_id=99, deck_id=7)

    assert payload == {
        "note": {
            "cardId": 99,
            "id": 42,
            "noteTypeId": NOTE_TYPE_ID,
            "deckId": 7,
            "fields": {"Front": "dog", "Back": ""},
        }
    }


def test_build_selection_cleared():
    assert dto.build_selection_cleared(3) == {"note": None, "count": 3}


# -- Command payload parsing --


def test_parse_smart_field_create_chat():
    create = dto.parse_smart_field_create(
        {
            "noteTypeId": NOTE_TYPE_ID,
            "deckId": int(DECK_ID),
            "targetFieldName": "Back",
            "fieldType": "chat",
            "enabled": True,
            "settings": {
                "promptText": "Define {{Front}}",
                "provider": "openai",
                "model": "gpt-5",
                "reasoningLevel": "off",
                "webSearchEnabled": False,
                "usesDefaultGenerationSettings": True,
            },
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


def test_parse_smart_field_create_tts():
    create = dto.parse_smart_field_create(
        {
            "noteTypeId": NOTE_TYPE_ID,
            "deckId": int(DECK_ID),
            "targetFieldName": "Audio",
            "fieldType": "tts",
            "enabled": False,
            "settings": {
                "sourceFieldName": "Front",
                "provider": "openai",
                "model": "tts-1",
                "voiceId": "echo",
                "usesDefaultGenerationSettings": True,
            },
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


def test_parse_smart_field_create_image():
    create = dto.parse_smart_field_create(
        {
            "noteTypeId": NOTE_TYPE_ID,
            "deckId": int(DECK_ID),
            "targetFieldName": "Image",
            "fieldType": "image",
            "enabled": True,
            "settings": {
                "promptText": "Illustrate {{Front}}",
                "provider": "replicate",
                "model": "flux-dev",
                "usesDefaultGenerationSettings": False,
            },
        }
    )

    assert create.settings == ImageSmartFieldSettings(
        prompt_text="Illustrate {{Front}}",
        provider="replicate",
        model="flux-dev",
        uses_default_generation_settings=False,
    )


def test_parse_smart_field_create_rejects_missing_setting():
    with pytest.raises(ValueError, match="provider"):
        dto.parse_smart_field_create(
            {
                "noteTypeId": NOTE_TYPE_ID,
                "deckId": int(DECK_ID),
                "targetFieldName": "Back",
                "fieldType": "chat",
                "enabled": True,
                "settings": {
                    "promptText": "Define {{Front}}",
                    "model": "gpt-5",
                    "reasoningLevel": "off",
                    "webSearchEnabled": False,
                    "usesDefaultGenerationSettings": True,
                },
            }
        )


def test_parse_smart_field_create_rejects_missing_enabled():
    with pytest.raises(ValueError, match="enabled"):
        dto.parse_smart_field_create(
            {
                "noteTypeId": NOTE_TYPE_ID,
                "deckId": int(DECK_ID),
                "targetFieldName": "Back",
                "fieldType": "chat",
                "settings": {
                    "promptText": "Define {{Front}}",
                    "provider": "openai",
                    "model": "gpt-5",
                    "reasoningLevel": "off",
                    "webSearchEnabled": False,
                    "usesDefaultGenerationSettings": True,
                },
            }
        )


def test_parse_smart_field_create_rejects_missing_prompt():
    with pytest.raises(ValueError, match="promptText"):
        dto.parse_smart_field_create(
            {
                "noteTypeId": NOTE_TYPE_ID,
                "deckId": int(DECK_ID),
                "targetFieldName": "Back",
                "fieldType": "chat",
                "enabled": True,
                "settings": {
                    "provider": "openai",
                    "model": "gpt-5",
                    "reasoningLevel": "off",
                    "webSearchEnabled": False,
                    "usesDefaultGenerationSettings": True,
                },
            }
        )


def test_parse_smart_field_create_rejects_unknown_type():
    with pytest.raises(ValueError, match="Unknown fieldType"):
        dto.parse_smart_field_create(
            {
                "noteTypeId": NOTE_TYPE_ID,
                "deckId": int(DECK_ID),
                "targetFieldName": "Back",
                "fieldType": "video",
                "enabled": True,
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
            "image": {"provider": "replicate", "model": "flux-dev"},
        }
    )
    assert parsed == GENERATION_DEFAULTS


def test_parse_text_prompt_test_validates_card_and_settings():
    parsed = dto.parse_text_prompt_test(
        {
            "cardId": 99,
            "prompt": "Define {{Front}}",
            "settings": {
                "provider": "openai",
                "model": "gpt-5",
                "reasoningLevel": "high",
                "webSearchEnabled": True,
            },
        }
    )

    assert parsed.card_id == 99
    assert parsed.prompt == "Define {{Front}}"
    assert parsed.settings == ChatGenerationSettings(
        provider="openai",
        model="gpt-5",
        reasoning_level="high",
        web_search_enabled=True,
    )


def test_parse_text_prompt_test_rejects_model_provider_mismatch():
    with pytest.raises(ValueError, match="not available for provider"):
        dto.parse_text_prompt_test(
            {
                "cardId": 99,
                "prompt": "Define {{Front}}",
                "settings": {
                    "provider": "anthropic",
                    "model": "gpt-5",
                    "reasoningLevel": "off",
                    "webSearchEnabled": False,
                },
            }
        )


def test_parse_image_prompt_test_validates_settings():
    parsed = dto.parse_image_prompt_test(
        {
            "cardId": 99,
            "prompt": "Illustrate {{Front}}",
            "settings": {"provider": "openai", "model": "gpt-image-1.5-low"},
        }
    )

    assert parsed.card_id == 99
    assert parsed.prompt == "Illustrate {{Front}}"
    assert parsed.settings == ImageGenerationSettings(
        provider="openai", model="gpt-image-1.5-low"
    )


def test_parse_tts_prompt_test_requires_known_voice_combination():
    parsed = dto.parse_tts_prompt_test(
        {
            "cardId": 99,
            "text": "{{Front}}",
            "settings": {
                "provider": "openai",
                "model": "tts-1",
                "voiceId": "alloy",
            },
        }
    )

    assert parsed.card_id == 99
    assert parsed.settings == TTSGenerationSettings(
        provider="openai", model="tts-1", voice_id="alloy"
    )

    with pytest.raises(ValueError, match="Unknown provider, model, and voice"):
        dto.parse_tts_preview(
            {
                "text": "Hello",
                "settings": {
                    "provider": "openai",
                    "model": "tts-1",
                    "voiceId": "missing",
                },
            }
        )


def test_build_voice_catalog_uses_wire_names():
    catalog = dto.build_voice_catalog()

    assert catalog["schemaVersion"] == dto.SCHEMA_VERSION
    assert catalog["voices"]
    assert set(catalog["voices"][0]) == {
        "provider",
        "voiceId",
        "model",
        "name",
        "gender",
        "language",
        "priceTier",
    }


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


def test_browser_selection_uses_representative_card_for_one_selected_row(monkeypatch):
    from src.web import hook_adapters

    note = MockNote({"Front": "dog"}, note_id=42)
    card = MockCard(id=99, did=7, note=note)
    browser = MagicMock()
    browser.table.len_selection.return_value = 1
    browser.table.get_single_selected_card.return_value = card
    monkeypatch.setattr(
        hook_adapters,
        "mw",
        SimpleNamespace(col=MagicMock()),
    )

    payload = hook_adapters._build_selection_payload(browser)

    assert payload["note"]["cardId"] == 99
    assert payload["note"]["deckId"] == 7
    browser.selected_cards.assert_not_called()


def test_browser_selection_counts_selected_rows(monkeypatch):
    from src.web import hook_adapters

    browser = MagicMock()
    browser.table.len_selection.return_value = 2
    browser.table.get_single_selected_card.return_value = None
    monkeypatch.setattr(hook_adapters, "mw", SimpleNamespace(col=MagicMock()))

    assert hook_adapters._build_selection_payload(browser) == {
        "note": None,
        "count": 2,
    }


@pytest.mark.asyncio
async def test_text_prompt_service_refetches_card_and_runs_without_writing(monkeypatch):
    from src.services import prompt_test_service

    monkeypatch.setattr(prompt_test_service, "is_capacity_remaining", lambda: True)
    note = MockNote({"Front": "dog"}, note_id=42)
    card = MockCard(id=99, did=7, note=note)
    request = dto.parse_text_prompt_test(
        {
            "cardId": 99,
            "prompt": "Define {{Front}}",
            "settings": {
                "provider": "openai",
                "model": "gpt-5",
                "reasoningLevel": "off",
                "webSearchEnabled": False,
            },
        }
    )
    monkeypatch.setattr(
        prompt_test_service,
        "mw",
        SimpleNamespace(col=SimpleNamespace(get_card=lambda card_id: card)),
    )
    get_chat_response = MagicMock(return_value="A domesticated canine")

    async def fake_get_chat_response(**kwargs):
        get_chat_response(**kwargs)
        return "A domesticated canine"

    monkeypatch.setattr(
        prompt_test_service.field_resolver,
        "get_chat_response",
        fake_get_chat_response,
    )

    context = prompt_test_service.prepare_text_prompt_test(request)
    result = await prompt_test_service.run_text_prompt_test(context)

    assert result == {"text": "A domesticated canine"}
    assert get_chat_response.call_args.kwargs["note"] is note
    assert get_chat_response.call_args.kwargs["deck_id"] == 7
    assert get_chat_response.call_args.kwargs["generation_source"] == "prompt_test"
    assert get_chat_response.call_args.kwargs["should_convert_to_html"] is False
    assert get_chat_response.call_args.kwargs["should_embed_images"] is False


@pytest.mark.asyncio
async def test_image_prompt_service_returns_data_url_without_writing(monkeypatch):
    from src.services import prompt_test_service

    monkeypatch.setattr(prompt_test_service, "is_capacity_remaining", lambda: True)
    note = MockNote({"Front": "dog"}, note_id=42)
    card = MockCard(id=99, did=7, note=note)
    request = dto.parse_image_prompt_test(
        {
            "cardId": 99,
            "prompt": "Illustrate {{Front}}",
            "settings": {"provider": "openai", "model": "gpt-image-1.5-low"},
        }
    )
    monkeypatch.setattr(
        prompt_test_service,
        "mw",
        SimpleNamespace(col=SimpleNamespace(get_card=lambda card_id: card)),
    )

    async def fake_get_image_response(**kwargs):
        assert kwargs["note"] is note
        assert kwargs["show_error_box"] is False
        return {"data": b"image", "content_type": "image/png"}

    monkeypatch.setattr(
        prompt_test_service.field_resolver,
        "get_image_response",
        fake_get_image_response,
    )

    result = await prompt_test_service.run_image_prompt_test(
        prompt_test_service.prepare_image_prompt_test(request)
    )

    assert result == {"dataUrl": "data:image/png;base64,aW1hZ2U="}


@pytest.mark.asyncio
async def test_tts_prompt_service_returns_audio_data_url_without_writing(monkeypatch):
    from src.services import prompt_test_service

    monkeypatch.setattr(prompt_test_service, "is_capacity_remaining", lambda: True)
    note = MockNote({"Front": "dog"}, note_id=42)
    card = MockCard(id=99, did=7, note=note)
    request = dto.parse_tts_prompt_test(
        {
            "cardId": 99,
            "text": "{{Front}}",
            "settings": {
                "provider": "openai",
                "model": "tts-1",
                "voiceId": "alloy",
            },
        }
    )
    monkeypatch.setattr(
        prompt_test_service,
        "mw",
        SimpleNamespace(col=SimpleNamespace(get_card=lambda card_id: card)),
    )

    async def fake_get_tts_response(**kwargs):
        assert kwargs["note"] is note
        assert kwargs["show_error_box"] is False
        return b"audio"

    monkeypatch.setattr(
        prompt_test_service.field_resolver,
        "get_tts_response",
        fake_get_tts_response,
    )

    result = await prompt_test_service.run_tts_prompt_test(
        prompt_test_service.prepare_tts_prompt_test(request)
    )

    assert result == {"dataUrl": "data:audio/mpeg;base64,YXVkaW8="}
