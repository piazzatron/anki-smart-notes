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
from typing import Any, Callable, Optional, cast

import pytest
from anki.decks import DeckId

import src.database.connection
import src.database.legacy_config_migration
import src.sentry
import src.smart_field_prompt_map

NOTE_TYPE_NAME = "note_type_1"
BASIC_NOTE_TYPE_NAME = "Basic"
NOTE_TYPE_ID = 123
DECK_ID = cast(DeckId, 1)


class MockNote:
    def __init__(
        self,
        data: dict[str, Any],
        *,
        note_type: str = NOTE_TYPE_NAME,
        note_id: int = 1,
    ) -> None:
        self._data = data
        self._note_type = note_type
        self.id = note_id

    def note_type(self) -> dict[str, object]:
        return {"name": self._note_type, "id": NOTE_TYPE_ID}

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self._data[key] = value

    def __contains__(self, key: str) -> bool:
        return key in self._data

    def items(self) -> object:
        return self._data.items()

    def fields(self) -> object:
        return self._data.keys()


class MockConfig:
    def __init__(
        self,
        *,
        allow_empty_fields: bool = False,
        prompts_map: Any = None,
    ) -> None:
        self.allow_empty_fields = allow_empty_fields
        self.prompts_map = prompts_map

    chat_provider = "auto"
    chat_model = "auto"
    chat_reasoning_level = "off"
    chat_web_search = False
    tts_provider = "openai"
    tts_voice = "alloy"
    tts_model = "tts-1"
    openai_api_key = ""
    auth_token = ""
    debug = True
    generate_at_review = True


class MockCard:
    def __init__(
        self,
        *,
        id: int = 1,
        did: int = 1,
        processed: bool = False,
        note: Optional[MockNote] = None,
    ) -> None:
        self.id = id
        self.did = did
        self.processed = processed
        self._note = note or MockNote({"f1": "1"})

    def note(self) -> MockNote:
        return self._note


class MockProcessor:
    def __init__(self) -> None:
        self.processed_cards: list[int] = []

    async def process_note(
        self,
        note: Any,
        deck_id: int,
        overwrite_fields: bool = False,
    ) -> bool:
        self.processed_cards.append(deck_id)
        return True


class FakeAddonManager:
    def __init__(self, addon_config: Optional[dict[str, Any]] = None) -> None:
        self.addon_config = addon_config or {}
        self.written_config: Optional[dict[str, Any]] = None

    def getConfig(self, addon_name: str) -> dict[str, Any]:
        return self.addon_config

    def writeConfig(self, addon_name: str, addon_config: dict[str, Any]) -> None:
        self.written_config = deepcopy(addon_config)


class FakeConfig:
    def __init__(self, addon_config: dict[str, Any]) -> None:
        self.addon_config = addon_config

    @property
    def did_migrate_smart_fields_to_sqlite(self) -> bool:
        return bool(self.addon_config.get("did_migrate_smart_fields_to_sqlite"))

    def __getattr__(self, key: str) -> object:
        return self.addon_config.get(key)


class FakeSentry:
    def __init__(self) -> None:
        self.captured: list[Exception] = []

    def capture_exception(self, error: Exception) -> None:
        self.captured.append(error)


class FakeModels:
    def __init__(self, note_types: Optional[dict[str, int]] = None) -> None:
        self.note_types = note_types or {BASIC_NOTE_TYPE_NAME: NOTE_TYPE_ID}

    def by_name(self, note_type: str) -> Optional[dict[str, Any]]:
        if note_type not in self.note_types:
            return None
        return {"id": self.note_types[note_type]}


class FakeCollection:
    def __init__(self, note_types: Optional[dict[str, int]] = None) -> None:
        self.models = FakeModels(note_types)


class FakeMw:
    def __init__(
        self,
        addon_config: Optional[dict[str, Any]] = None,
        *,
        note_types: Optional[dict[str, int]] = None,
    ) -> None:
        self.addonManager = FakeAddonManager(addon_config)
        self.col = FakeCollection(note_types)


def use_temp_sqlite(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        src.database.connection,
        "get_database_path",
        lambda: str(tmp_path / "smart_notes.sqlite3"),
    )


def install_fake_anki(
    monkeypatch: pytest.MonkeyPatch,
    addon_config: dict[str, Any],
    tmp_path: Path,
    *,
    show_message_box: Optional[Callable[..., None]] = None,
) -> FakeMw:
    fake_mw = FakeMw(addon_config)
    monkeypatch.setattr(src.database.legacy_config_migration, "mw", fake_mw)
    monkeypatch.setattr(src.smart_field_prompt_map, "mw", fake_mw)
    monkeypatch.setattr(
        src.database.legacy_config_migration, "config", FakeConfig(addon_config)
    )
    monkeypatch.setattr(
        src.database.legacy_config_migration,
        "get_user_files_path",
        lambda filename: str(tmp_path / "user_files" / filename),
    )
    if show_message_box is not None:
        monkeypatch.setattr(
            src.database.legacy_config_migration,
            "show_message_box",
            show_message_box,
        )
    return fake_mw


def install_prompt_map_collection(
    monkeypatch: pytest.MonkeyPatch,
    *,
    note_types: Optional[dict[str, int]] = None,
) -> FakeMw:
    fake_mw = FakeMw(note_types=note_types)
    monkeypatch.setattr(src.smart_field_prompt_map, "mw", fake_mw)
    return fake_mw


def install_migration_alert(
    monkeypatch: pytest.MonkeyPatch, messages: list[tuple[object, ...]]
) -> None:
    monkeypatch.setattr(
        src.database.legacy_config_migration,
        "show_message_box",
        lambda *args: messages.append(args),
    )


def install_fake_sentry(monkeypatch: pytest.MonkeyPatch) -> FakeSentry:
    fake_sentry = FakeSentry()
    monkeypatch.setattr(src.sentry, "sentry", fake_sentry)
    return fake_sentry
