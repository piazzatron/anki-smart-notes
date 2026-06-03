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

import pytest

from src.constants import GLOBAL_DECK_ID
from src.database import open_database
from src.models.smart_fields import (
    ChatSmartFieldSettings,
    ImageSmartFieldSettings,
    SmartFieldCreate,
    TTSSmartFieldSettings,
)
from src.services.smart_field_service import SmartFieldService

NOTE_TYPE_ID = 123


@pytest.fixture(autouse=True)
def sqlite_database(tmp_path, monkeypatch):
    import src.database

    monkeypatch.setattr(
        src.database,
        "get_database_path",
        lambda: str(tmp_path / "smart_notes.sqlite3"),
    )
    src.database.apply_database_migrations()


def test_round_trips_typed_smart_fields() -> None:
    service = SmartFieldService()

    service.save_smart_field(
        SmartFieldCreate(
            note_type_id=NOTE_TYPE_ID,
            deck_id=1,
            target_field_name="Back",
            enabled=True,
            settings=ChatSmartFieldSettings(
                prompt_text="{{Front}}",
                provider="openai",
                model="gpt-4o-mini",
                web_search_enabled=True,
            ),
        )
    )
    service.save_smart_field(
        SmartFieldCreate(
            note_type_id=NOTE_TYPE_ID,
            deck_id=1,
            target_field_name="Audio",
            enabled=True,
            settings=TTSSmartFieldSettings(
                source_field_name="Back",
                provider="openai",
                model="tts-1",
                voice_id="alloy",
            ),
        )
    )
    service.save_smart_field(
        SmartFieldCreate(
            note_type_id=NOTE_TYPE_ID,
            deck_id=1,
            target_field_name="Image",
            enabled=False,
            settings=ImageSmartFieldSettings(
                prompt_text="Draw {{Front}}",
                provider="openai",
                model="gpt-image-1.5-low",
            ),
        )
    )

    smart_fields = {
        smart_field.target_field_name: smart_field
        for smart_field in service.get_smart_fields_for_note(
            NOTE_TYPE_ID, 1, include_global=True
        )
    }

    assert isinstance(smart_fields["Back"].settings, ChatSmartFieldSettings)
    assert smart_fields["Back"].settings.prompt_text == "{{Front}}"
    assert smart_fields["Back"].settings.web_search_enabled is True

    assert isinstance(smart_fields["Audio"].settings, TTSSmartFieldSettings)
    assert smart_fields["Audio"].settings.source_field_name == "Back"

    assert isinstance(smart_fields["Image"].settings, ImageSmartFieldSettings)
    assert smart_fields["Image"].enabled is False


def test_get_smart_fields_for_note_applies_global_fallback_with_deck_override() -> None:
    service = SmartFieldService()

    service.save_smart_field(
        SmartFieldCreate(
            note_type_id=NOTE_TYPE_ID,
            deck_id=GLOBAL_DECK_ID,
            target_field_name="Back",
            enabled=True,
            settings=ChatSmartFieldSettings(
                prompt_text="global",
                provider="openai",
                model="gpt-4o-mini",
                web_search_enabled=False,
            ),
        )
    )
    service.save_smart_field(
        SmartFieldCreate(
            note_type_id=NOTE_TYPE_ID,
            deck_id=GLOBAL_DECK_ID,
            target_field_name="Extra",
            enabled=True,
            settings=ChatSmartFieldSettings(
                prompt_text="global extra",
                provider="openai",
                model="gpt-4o-mini",
                web_search_enabled=False,
            ),
        )
    )
    service.save_smart_field(
        SmartFieldCreate(
            note_type_id=NOTE_TYPE_ID,
            deck_id=1,
            target_field_name="Back",
            enabled=True,
            settings=ChatSmartFieldSettings(
                prompt_text="deck override",
                provider="openai",
                model="gpt-4o-mini",
                web_search_enabled=False,
            ),
        )
    )

    smart_fields = {
        smart_field.target_field_name: smart_field
        for smart_field in service.get_smart_fields_for_note(
            NOTE_TYPE_ID, 1, include_global=True
        )
    }

    assert smart_fields.keys() == {"Back", "Extra"}
    assert isinstance(smart_fields["Back"].settings, ChatSmartFieldSettings)
    assert smart_fields["Back"].settings.prompt_text == "deck override"
    assert isinstance(smart_fields["Extra"].settings, ChatSmartFieldSettings)
    assert smart_fields["Extra"].settings.prompt_text == "global extra"


def test_save_and_delete_match_target_fields_case_insensitively() -> None:
    service = SmartFieldService()

    service.save_smart_field(
        SmartFieldCreate(
            note_type_id=NOTE_TYPE_ID,
            deck_id=1,
            target_field_name="Back",
            enabled=True,
            settings=ChatSmartFieldSettings(
                prompt_text="original",
                provider="openai",
                model="gpt-4o-mini",
                web_search_enabled=False,
            ),
        )
    )
    service.save_smart_field(
        SmartFieldCreate(
            note_type_id=NOTE_TYPE_ID,
            deck_id=1,
            target_field_name="back",
            enabled=False,
            settings=ChatSmartFieldSettings(
                prompt_text="updated",
                provider="openai",
                model="gpt-4o-mini",
                web_search_enabled=True,
            ),
        )
    )

    smart_fields = service.get_smart_fields_for_note(NOTE_TYPE_ID, 1)

    assert len(smart_fields) == 1
    assert smart_fields[0].target_field_name == "back"
    assert smart_fields[0].enabled is False
    assert isinstance(smart_fields[0].settings, ChatSmartFieldSettings)
    assert smart_fields[0].settings.prompt_text == "updated"

    service.delete_smart_field(NOTE_TYPE_ID, 1, "BACK")

    assert service.get_smart_fields_for_note(NOTE_TYPE_ID, 1) == []


def test_get_chat_defaults_fails_when_seed_row_is_missing() -> None:
    with open_database() as conn:
        conn.execute("DELETE FROM default_text_generation_settings WHERE id = 1")
        conn.commit()

    with pytest.raises(
        RuntimeError, match="Missing default text generation settings row"
    ):
        SmartFieldService().get_chat_defaults()


def test_get_all_smart_fields_fails_when_default_seed_row_is_missing() -> None:
    service = SmartFieldService()
    service.save_smart_field(
        SmartFieldCreate(
            note_type_id=NOTE_TYPE_ID,
            deck_id=1,
            target_field_name="Back",
            enabled=True,
            settings=ChatSmartFieldSettings(
                prompt_text="{{Front}}",
                provider="auto",
                model="auto",
                web_search_enabled=False,
                uses_default_generation_settings=True,
            ),
        )
    )
    with open_database() as conn:
        conn.execute("DELETE FROM default_text_generation_settings WHERE id = 1")
        conn.commit()

    with pytest.raises(
        RuntimeError, match="Missing default text generation settings row"
    ):
        service.get_all_smart_fields()


def test_get_tts_defaults_fails_when_seed_row_is_missing() -> None:
    with open_database() as conn:
        conn.execute("DELETE FROM default_tts_generation_settings WHERE id = 1")
        conn.commit()

    with pytest.raises(
        RuntimeError, match="Missing default TTS generation settings row"
    ):
        SmartFieldService().get_tts_defaults()


def test_get_image_defaults_fails_when_seed_row_is_missing() -> None:
    with open_database() as conn:
        conn.execute("DELETE FROM default_image_generation_settings WHERE id = 1")
        conn.commit()

    with pytest.raises(
        RuntimeError, match="Missing default image generation settings row"
    ):
        SmartFieldService().get_image_defaults()
