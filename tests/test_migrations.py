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

import sqlite3
from copy import deepcopy
from pathlib import Path
from typing import Any, Optional, cast

import pytest
from anki.decks import DeckId
from yoyo import read_migrations

from src.database import get_sqlite_backend
from src.database.migrations import (
    apply_database_bootstrap_migrations,
    apply_database_migrations,
    run_migrations,
)
from src.models.smart_fields import ChatSmartFieldSettings
from src.services.smart_field_service import SmartFieldService

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


def test_run_migrations_imports_legacy_config_after_bootstrap(
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
        "src.database.migrations.apply_database_profile_scope_migration_if_needed",
        lambda **kwargs: calls.append("profile_scope"),
    )
    monkeypatch.setattr(
        "src.database.migrations.migrate_legacy_config_to_database",
        lambda: calls.append("legacy_config"),
    )
    monkeypatch.setattr(
        "src.database.migrations.legacy_config_migration_is_complete",
        lambda: False,
    )

    run_migrations()

    assert calls == [
        "bootstrap",
        "profile_scope",
        "legacy_config",
        "database",
    ]


def test_run_migrations_evolves_imported_legacy_config_to_current_schema(
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

    smart_fields = SmartFieldService().get_smart_fields_for_note(
        NOTE_TYPE_ID, DECK_ID, profile_name="__test__"
    )

    assert len(smart_fields) == 1
    assert isinstance(smart_fields[0].settings, ChatSmartFieldSettings)
    assert smart_fields[0].settings.provider == "auto"
    assert smart_fields[0].settings.model == "auto"
    assert smart_fields[0].settings.uses_default_generation_settings is False
    assert SmartFieldService().get_chat_defaults().provider == "auto"
    assert SmartFieldService().get_chat_defaults().model == "auto"
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

    smart_fields = SmartFieldService().get_smart_fields_for_note(
        NOTE_TYPE_ID, DECK_ID, profile_name="__test__"
    )

    assert len(smart_fields) == 1
    assert isinstance(smart_fields[0].settings, ChatSmartFieldSettings)
    assert smart_fields[0].settings.uses_default_generation_settings is True
    assert smart_fields[0].settings.provider == "auto"
    assert smart_fields[0].settings.model == "auto"


def test_run_migrations_repairs_old_bootstrap_only_schema_before_legacy_import(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import src.database.connection

    database_path = tmp_path / "smart_notes.sqlite3"
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
    install_fake_anki(monkeypatch, addon_config, tmp_path)
    monkeypatch.setattr(
        src.database.connection,
        "get_database_path",
        lambda: str(database_path),
    )
    apply_database_bootstrap_migrations(str(database_path))
    replace_smart_fields_with_old_unprofiled_bootstrap_schema(database_path)

    run_migrations()

    smart_fields = SmartFieldService().get_smart_fields_for_note(
        NOTE_TYPE_ID, DECK_ID, profile_name="__test__"
    )
    with sqlite3.connect(database_path) as conn:
        applied_migrations = {
            row[0] for row in conn.execute("SELECT migration_id FROM _yoyo_migration")
        }

    assert len(smart_fields) == 1
    assert isinstance(smart_fields[0].settings, ChatSmartFieldSettings)
    assert smart_fields[0].settings.provider == "auto"
    assert smart_fields[0].settings.model == "auto"
    assert applied_migrations == {
        "0001_initial_smart_fields_schema",
        "0002_migrate_deprecated_chat_models_to_auto",
        "0003_scope_smart_fields_to_profile",
    }


def test_run_migrations_does_not_apply_profile_repair_after_data_migration_ran(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import src.database.connection

    database_path = tmp_path / "smart_notes.sqlite3"
    addon_config = {
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
    install_fake_anki(monkeypatch, addon_config, tmp_path)
    monkeypatch.setattr(
        src.database.connection,
        "get_database_path",
        lambda: str(database_path),
    )
    apply_first_two_database_migrations(database_path)
    replace_smart_fields_with_old_unprofiled_bootstrap_schema(database_path)

    with pytest.raises(
        RuntimeError,
        match=(
            "SQL data migrations have already run before legacy config import: "
            "0002_migrate_deprecated_chat_models_to_auto"
        ),
    ):
        run_migrations()

    with sqlite3.connect(database_path) as conn:
        columns = {row[1] for row in conn.execute("PRAGMA table_info(smart_fields)")}
        applied_migrations = {
            row[0] for row in conn.execute("SELECT migration_id FROM _yoyo_migration")
        }

    assert "profile_name" not in columns
    assert "0003_scope_smart_fields_to_profile" not in applied_migrations


def test_run_migrations_profiles_old_sql_rows_after_legacy_import_completed(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import src.database.connection

    database_path = tmp_path / "smart_notes.sqlite3"
    addon_config = {"did_migrate_smart_fields_to_sqlite": True}
    install_fake_anki(monkeypatch, addon_config, tmp_path)
    monkeypatch.setattr(
        src.database.connection,
        "get_database_path",
        lambda: str(database_path),
    )
    apply_first_two_database_migrations(database_path)
    replace_smart_fields_with_old_unprofiled_bootstrap_schema(database_path)
    insert_old_text_smart_field_for_run_migrations(database_path)

    run_migrations()

    with sqlite3.connect(database_path) as conn:
        smart_field_row = conn.execute(
            """
            SELECT profile_name, note_type_id, deck_id, target_field_name
            FROM smart_fields
            """
        ).fetchone()
        applied_migrations = {
            row[0] for row in conn.execute("SELECT migration_id FROM _yoyo_migration")
        }

    assert smart_field_row == ("__test__", NOTE_TYPE_ID, int(DECK_ID), "Back")
    assert "0003_scope_smart_fields_to_profile" in applied_migrations


def test_run_migrations_fails_if_legacy_import_would_skip_sql_data_migrations(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import src.database.connection

    database_path = tmp_path / "smart_notes.sqlite3"
    addon_config = {
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
    install_fake_anki(monkeypatch, addon_config, tmp_path)
    monkeypatch.setattr(
        src.database.connection,
        "get_database_path",
        lambda: str(database_path),
    )
    apply_database_migrations(str(database_path))

    with pytest.raises(
        RuntimeError,
        match="SQL data migrations have already run before legacy config import",
    ):
        run_migrations()


def install_fake_anki(
    monkeypatch: pytest.MonkeyPatch,
    addon_config: dict[str, Any],
    tmp_path: Path,
) -> Any:
    import src.database.legacy_config_migration
    import src.smart_field_prompt_map
    import src.utils

    class FakeModels:
        def all(self) -> list[dict[str, Any]]:
            return [{"name": "Basic", "id": NOTE_TYPE_ID}]

        def by_name(self, note_type: str) -> Optional[dict[str, Any]]:
            if note_type != "Basic":
                return None
            return {"id": NOTE_TYPE_ID}

    class FakeDecks:
        def all(self) -> list[dict[str, Any]]:
            return [{"id": int(DECK_ID), "name": "Deck 1"}]

    class FakeCollection:
        models = FakeModels()
        decks = FakeDecks()

    class FakeProfileManager:
        name = "__test__"
        base = str(tmp_path / "profiles")

        def profiles(self) -> list[str]:
            return ["__test__"]

    class FakeMw:
        def __init__(self) -> None:
            self.addonManager = FakeAddonManager(addon_config)
            self.pm = FakeProfileManager()
            self.col = FakeCollection()

    fake_mw = FakeMw()
    import aqt

    monkeypatch.setattr(aqt, "mw", fake_mw)
    monkeypatch.setattr(src.database.legacy_config_migration, "mw", fake_mw)
    monkeypatch.setattr(src.smart_field_prompt_map, "mw", fake_mw)
    monkeypatch.setattr(src.utils, "mw", fake_mw)
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


def apply_first_two_database_migrations(database_path: Path) -> None:
    migrations_path = Path(__file__).parents[1] / "src" / "database" / "db_migrations"
    migrations = read_migrations(str(migrations_path))
    backend = get_sqlite_backend(str(database_path))
    with backend.lock():
        backend.apply_migrations(migrations[:2])


def insert_old_text_smart_field_for_run_migrations(database_path: Path) -> None:
    with sqlite3.connect(database_path) as conn:
        conn.execute(
            """
            INSERT INTO smart_fields (
                id, note_type_id, deck_id, target_field_name, field_type,
                enabled, created_at, updated_at
            )
            VALUES ('legacy', ?, ?, 'Back', 'chat', 1, 'now', 'now')
            """,
            (NOTE_TYPE_ID, int(DECK_ID)),
        )
        conn.execute(
            """
            INSERT INTO text_smart_field_settings (
                smart_field_id, prompt_text, uses_default_generation_settings,
                provider, model, reasoning_level, web_search_enabled
            )
            VALUES ('legacy', '{{Front}}', 0, 'openai', 'gpt-5-mini', 'off', 0)
            """
        )


def replace_smart_fields_with_old_unprofiled_bootstrap_schema(
    database_path: Path,
) -> None:
    with sqlite3.connect(database_path) as conn:
        conn.execute("PRAGMA foreign_keys = OFF")
        conn.execute("DROP TABLE smart_fields")
        conn.execute(
            """
            CREATE TABLE smart_fields (
                id TEXT PRIMARY KEY,
                note_type_id INTEGER NOT NULL,
                deck_id INTEGER NOT NULL,
                target_field_name TEXT NOT NULL,
                field_type TEXT NOT NULL CHECK (field_type IN ('chat', 'tts', 'image')),
                enabled INTEGER NOT NULL DEFAULT 1 CHECK (enabled IN (0, 1)),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(note_type_id, deck_id, target_field_name)
            );
            """
        )
