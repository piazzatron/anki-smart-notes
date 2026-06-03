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

from src.database.migrations import run_migrations
from src.models.smart_fields import ChatSmartFieldSettings
from src.services.smart_field_service import SmartFieldService, smart_field_service

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


def test_run_migrations_applies_schema_before_legacy_config_import(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    monkeypatch.setattr(
        "src.database.migrations.apply_database_bootstrap_migrations",
        lambda: calls.append("bootstrap"),
    )
    monkeypatch.setattr(
        "src.database.migrations.apply_database_migrations",
        lambda: calls.append("database"),
    )
    monkeypatch.setattr(
        "src.database.migrations.migrate_legacy_config_to_database",
        lambda: calls.append("legacy_config"),
    )

    run_migrations()

    assert calls == ["bootstrap", "legacy_config", "database"]


def test_run_migrations_imports_legacy_config_before_chat_model_data_migration(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import src.database.connection

    addon_config = {
        "chat_provider": "openai",
        "chat_model": "gpt-5-nano",
        "chat_reasoning_level": "off",
        "chat_web_search": False,
        "prompts_map": {
            "note_types": {
                "Basic": {
                    str(DECK_ID): {
                        "fields": {"Back": "{{Front}}"},
                        "extras": {
                            "Back": {
                                "automatic": True,
                                "type": "chat",
                                "use_custom_model": True,
                                "chat_provider": "openai",
                                "chat_model": "gpt-4o-mini",
                                "chat_reasoning_level": None,
                                "chat_web_search": False,
                                "tts_model": None,
                                "tts_provider": None,
                                "tts_voice": None,
                                "image_provider": None,
                                "image_model": None,
                            }
                        },
                    }
                }
            }
        },
        "did_migrate_smart_fields_to_sqlite": False,
    }
    fake_mw = install_fake_anki(monkeypatch, addon_config, tmp_path)
    monkeypatch.setattr(
        src.database.connection,
        "get_database_path",
        lambda: str(tmp_path / "smart_notes.sqlite3"),
    )

    run_migrations()

    smart_fields = SmartFieldService().get_smart_fields_for_note(NOTE_TYPE_ID, DECK_ID)

    assert len(smart_fields) == 1
    assert isinstance(smart_fields[0].settings, ChatSmartFieldSettings)
    assert smart_fields[0].settings.provider == "auto"
    assert smart_fields[0].settings.model == "auto"
    assert smart_fields[0].settings.uses_default_generation_settings is False
    assert smart_field_service.get_chat_defaults().provider == "auto"
    assert smart_field_service.get_chat_defaults().model == "auto"
    assert fake_mw.addonManager.written_config is not None
    assert "chat_provider" not in fake_mw.addonManager.written_config
    assert "chat_model" not in fake_mw.addonManager.written_config


def test_run_migrations_updates_inherited_fields_through_sql_default_row(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import src.database.connection

    addon_config = {
        "chat_provider": "openai",
        "chat_model": "gpt-5-nano",
        "chat_reasoning_level": "off",
        "chat_web_search": False,
        "prompts_map": {
            "note_types": {
                "Basic": {
                    str(DECK_ID): {
                        "fields": {"Back": "{{Front}}"},
                        "extras": {
                            "Back": {
                                "automatic": True,
                                "type": "chat",
                                "use_custom_model": False,
                                "chat_provider": None,
                                "chat_model": None,
                                "chat_reasoning_level": None,
                                "chat_web_search": None,
                                "tts_model": None,
                                "tts_provider": None,
                                "tts_voice": None,
                                "image_provider": None,
                                "image_model": None,
                            }
                        },
                    }
                }
            }
        },
        "did_migrate_smart_fields_to_sqlite": False,
    }
    install_fake_anki(monkeypatch, addon_config, tmp_path)
    monkeypatch.setattr(
        src.database.connection,
        "get_database_path",
        lambda: str(tmp_path / "smart_notes.sqlite3"),
    )

    run_migrations()

    smart_fields = SmartFieldService().get_smart_fields_for_note(NOTE_TYPE_ID, DECK_ID)

    assert len(smart_fields) == 1
    assert isinstance(smart_fields[0].settings, ChatSmartFieldSettings)
    assert smart_fields[0].settings.uses_default_generation_settings is True
    assert smart_fields[0].settings.provider == "auto"
    assert smart_fields[0].settings.model == "auto"


def install_fake_anki(
    monkeypatch: pytest.MonkeyPatch,
    addon_config: dict[str, Any],
    tmp_path: Path,
) -> Any:
    import src.database.legacy_config_migration
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
    monkeypatch.setattr(
        src.database.legacy_config_migration,
        "show_message_box",
        lambda *args: None,
    )
    return fake_mw
