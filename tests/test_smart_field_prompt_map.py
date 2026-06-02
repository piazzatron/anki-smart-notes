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

from copy import deepcopy
from pathlib import Path
from typing import Any, Optional, cast

import pytest
from anki.decks import DeckId

from src.models import DEFAULT_EXTRAS, FieldExtras
from src.models.smart_fields import ChatSmartFieldSettings, SmartFieldCreate
from src.services.smart_field_service import SmartFieldService
from src.smart_field_prompt_map import replace_from_prompt_map

NOTE_TYPE_ID = 123
DECK_ID = cast(DeckId, 1)


@pytest.fixture(autouse=True)
def sqlite_database(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import src.database

    monkeypatch.setattr(
        src.database,
        "get_database_path",
        lambda: str(tmp_path / "smart_notes.sqlite3"),
    )
    src.database.apply_database_migrations()


@pytest.fixture(autouse=True)
def anki_collection(monkeypatch: pytest.MonkeyPatch) -> None:
    import src.smart_field_prompt_map

    class FakeModels:
        def by_name(self, note_type: str) -> Optional[dict[str, Any]]:
            if note_type != "Basic":
                return None
            return {"id": NOTE_TYPE_ID}

    class FakeCollection:
        models = FakeModels()

    class FakeMw:
        col = FakeCollection()

    monkeypatch.setattr(src.smart_field_prompt_map, "mw", FakeMw())


def test_replace_from_prompt_map_does_not_delete_existing_fields_if_conversion_fails() -> (
    None
):
    service = SmartFieldService()
    service.save_smart_field(
        SmartFieldCreate(
            note_type_id=NOTE_TYPE_ID,
            deck_id=DECK_ID,
            target_field_name="Back",
            enabled=True,
            settings=ChatSmartFieldSettings(
                prompt_text="existing",
                provider="auto",
                model="auto",
                web_search_enabled=False,
            ),
        )
    )

    with pytest.raises(ValueError):
        replace_from_prompt_map(
            {
                "note_types": {
                    "Basic": {
                        "1": {
                            "fields": {"Audio": "{{Front}} {{Back}}"},
                            "extras": {"Audio": tts_extras()},
                        }
                    }
                }
            }
        )

    smart_fields = service.get_smart_fields_for_note(NOTE_TYPE_ID, DECK_ID)

    assert len(smart_fields) == 1
    assert smart_fields[0].target_field_name == "Back"
    assert isinstance(smart_fields[0].settings, ChatSmartFieldSettings)
    assert smart_fields[0].settings.prompt_text == "existing"


def test_replace_from_prompt_map_replaces_fields_after_successful_conversion() -> None:
    service = SmartFieldService()
    service.save_smart_field(
        SmartFieldCreate(
            note_type_id=NOTE_TYPE_ID,
            deck_id=DECK_ID,
            target_field_name="Back",
            enabled=True,
            settings=ChatSmartFieldSettings(
                prompt_text="old",
                provider="auto",
                model="auto",
                web_search_enabled=False,
            ),
        )
    )

    replace_from_prompt_map(
        {
            "note_types": {
                "Basic": {
                    "1": {
                        "fields": {"FrontExtra": "new {{Front}}"},
                        "extras": {"FrontExtra": chat_extras(automatic=False)},
                    }
                }
            }
        }
    )

    smart_fields = service.get_smart_fields_for_note(NOTE_TYPE_ID, DECK_ID)

    assert len(smart_fields) == 1
    assert smart_fields[0].target_field_name == "FrontExtra"
    assert smart_fields[0].enabled is False
    assert isinstance(smart_fields[0].settings, ChatSmartFieldSettings)
    assert smart_fields[0].settings.prompt_text == "new {{Front}}"


def chat_extras(automatic: bool = True) -> FieldExtras:
    extras = deepcopy(DEFAULT_EXTRAS)
    extras["automatic"] = automatic
    extras["chat_provider"] = "auto"
    extras["chat_model"] = "auto"
    extras["chat_reasoning_level"] = "off"
    extras["chat_web_search"] = False
    return extras


def tts_extras() -> FieldExtras:
    extras = deepcopy(DEFAULT_EXTRAS)
    extras["type"] = "tts"
    extras["tts_provider"] = "openai"
    extras["tts_model"] = "tts-1"
    extras["tts_voice"] = "alloy"
    return extras
