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

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Optional, cast

import pytest
from anki.decks import DeckId

from src.models import DEFAULT_EXTRAS, FieldExtras
from src.models.smart_fields import ChatSmartFieldSettings
from src.services.smart_field_service import SmartFieldService
from src.smart_field_migration import (
    migrate_deprecated_chat_config_to_auto,
    migrate_legacy_smart_field_config,
)

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


@pytest.fixture(autouse=True)
def sqlite_database(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import src.database

    monkeypatch.setattr(
        src.database,
        "get_database_path",
        lambda: str(tmp_path / "smart_notes.sqlite3"),
    )
    src.database.apply_database_migrations()


def test_migrate_legacy_smart_field_config_imports_prompts_and_cleans_config(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    addon_config = {
        "prompts_map": {
            "note_types": {
                "Basic": {
                    "1": {
                        "fields": {"Back": "{{Front}}"},
                        "extras": {"Back": chat_extras()},
                    }
                }
            }
        },
        "did_deck_filter_migration": True,
        "did_cleanup_config_defaults": True,
        "did_migrate_smart_fields_to_sqlite": False,
    }
    expected_backup = deepcopy(addon_config)
    fake_mw = install_fake_anki(monkeypatch, addon_config, tmp_path)
    messages: list[tuple[object, ...]] = []
    install_migration_alert(monkeypatch, messages)

    migrate_legacy_smart_field_config()

    smart_fields = SmartFieldService().get_smart_fields_for_note(NOTE_TYPE_ID, DECK_ID)
    backup_files = list(
        (tmp_path / "user_files").glob("config_backup_before_sqlite_*.json")
    )

    assert len(smart_fields) == 1
    assert smart_fields[0].target_field_name == "Back"
    assert isinstance(smart_fields[0].settings, ChatSmartFieldSettings)
    assert smart_fields[0].settings.prompt_text == "{{Front}}"
    assert smart_fields[0].settings.provider == "auto"
    assert smart_fields[0].settings.model == "auto"
    assert len(backup_files) == 1
    assert json.loads(backup_files[0].read_text(encoding="utf-8")) == expected_backup
    assert fake_mw.addonManager.written_config is not None
    assert "prompts_map" not in fake_mw.addonManager.written_config
    assert "did_deck_filter_migration" not in fake_mw.addonManager.written_config
    assert "did_cleanup_config_defaults" not in fake_mw.addonManager.written_config
    assert (
        fake_mw.addonManager.written_config["did_migrate_smart_fields_to_sqlite"]
        is True
    )
    assert messages == []


def test_migrate_legacy_smart_field_config_reports_failure_and_keeps_config(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    addon_config = {
        "prompts_map": {
            "note_types": {
                "Basic": {
                    "1": {
                        "fields": {"Audio": "{{Front}} {{Back}}"},
                        "extras": {"Audio": tts_extras()},
                    }
                }
            }
        },
        "did_migrate_smart_fields_to_sqlite": False,
    }
    fake_mw = install_fake_anki(monkeypatch, addon_config, tmp_path)
    messages: list[tuple[object, ...]] = []
    install_migration_alert(monkeypatch, messages)
    fake_sentry = install_fake_sentry(monkeypatch)

    with pytest.raises(ValueError):
        migrate_legacy_smart_field_config()

    backup_files = list(
        (tmp_path / "user_files").glob("config_backup_before_sqlite_*.json")
    )

    assert len(backup_files) == 1
    assert fake_mw.addonManager.written_config is None
    assert addon_config["did_migrate_smart_fields_to_sqlite"] is False
    assert "prompts_map" in addon_config
    assert len(fake_sentry.captured) == 1
    assert messages == [
        (
            "Smart Notes could not finish upgrading your Smart Fields.",
            "Please email support@smart-notes.xyz and include your smart-notes.log file.",
        )
    ]


def test_migrate_legacy_smart_field_config_does_nothing_after_successful_migration(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    addon_config = {"did_migrate_smart_fields_to_sqlite": True}
    fake_mw = install_fake_anki(monkeypatch, addon_config, tmp_path)

    migrate_legacy_smart_field_config()

    assert fake_mw.addonManager.written_config is None
    assert not (tmp_path / "user_files").exists()


def test_migrate_deprecated_chat_config_to_auto(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    addon_config = {
        "chat_provider": "openai",
        "chat_model": "gpt-5-nano",
    }
    fake_mw = install_fake_anki(monkeypatch, addon_config, tmp_path)

    migrate_deprecated_chat_config_to_auto()

    assert fake_mw.addonManager.written_config is not None
    assert fake_mw.addonManager.written_config["chat_provider"] == "auto"
    assert fake_mw.addonManager.written_config["chat_model"] == "auto"


def install_fake_anki(
    monkeypatch: pytest.MonkeyPatch,
    addon_config: dict[str, Any],
    tmp_path: Path,
) -> Any:
    import src.smart_field_migration
    import src.smart_field_prompt_map

    class FakeModels:
        def by_name(self, note_type: str) -> Optional[dict[str, Any]]:
            if note_type != "Basic":
                return None
            return {"id": NOTE_TYPE_ID}

    class FakeCollection:
        models = FakeModels()

    class FakeMw:
        def __init__(self) -> None:
            self.addonManager = FakeAddonManager(addon_config)
            self.col = FakeCollection()

    fake_mw = FakeMw()
    monkeypatch.setattr(src.smart_field_migration, "mw", fake_mw)
    monkeypatch.setattr(src.smart_field_prompt_map, "mw", fake_mw)
    monkeypatch.setattr(src.smart_field_migration, "config", FakeConfig(addon_config))
    monkeypatch.setattr(
        src.smart_field_migration,
        "get_user_files_path",
        lambda filename: str(tmp_path / "user_files" / filename),
    )
    return fake_mw


def install_migration_alert(
    monkeypatch: pytest.MonkeyPatch, messages: list[tuple[object, ...]]
) -> None:
    import src.smart_field_migration

    monkeypatch.setattr(
        src.smart_field_migration,
        "show_message_box",
        lambda *args: messages.append(args),
    )


def install_fake_sentry(monkeypatch: pytest.MonkeyPatch) -> FakeSentry:
    import src.sentry

    fake_sentry = FakeSentry()
    monkeypatch.setattr(src.sentry, "sentry", fake_sentry)
    return fake_sentry


def chat_extras() -> FieldExtras:
    extras = deepcopy(DEFAULT_EXTRAS)
    extras["chat_provider"] = "openai"
    extras["chat_model"] = "gpt-4o-mini"
    extras["chat_web_search"] = False
    return extras


def tts_extras() -> FieldExtras:
    extras = deepcopy(DEFAULT_EXTRAS)
    extras["type"] = "tts"
    extras["tts_provider"] = "openai"
    extras["tts_model"] = "tts-1"
    extras["tts_voice"] = "alloy"
    return extras
