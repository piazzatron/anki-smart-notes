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

NOTE_TYPE_ID = 123
DECK_ID = cast(DeckId, 1)


class FakeAddonManager:
    def __init__(self, addon_config: dict[str, Any]) -> None:
        self.addon_config = addon_config
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
    def by_name(self, note_type: str) -> Optional[dict[str, Any]]:
        if note_type != "Basic":
            return None
        return {"id": NOTE_TYPE_ID}


class FakeCollection:
    models = FakeModels()


class FakeMw:
    def __init__(self, addon_config: dict[str, Any]) -> None:
        self.addonManager = FakeAddonManager(addon_config)
        self.col = FakeCollection()


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
