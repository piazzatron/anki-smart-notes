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
from pathlib import Path
from types import SimpleNamespace

import pytest
from fixtures import DECK_ID, NOTE_TYPE_ID, install_fake_anki, use_temp_sqlite
from yoyo import read_migrations

from src.database import get_sqlite_backend
from src.database.migrations import (
    apply_database_bootstrap_migrations,
    run_migrations,
)
from src.models.smart_fields import ChatSmartFieldSettings
from src.services.smart_field_service import SmartFieldService


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
        "src.database.migrations.migrate_legacy_config_to_database",
        lambda: calls.append("legacy_config"),
    )
    monkeypatch.setattr(
        "src.database.migrations.config",
        SimpleNamespace(did_migrate_smart_fields_to_sqlite=True),
    )

    run_migrations()

    assert calls == [
        "bootstrap",
        "legacy_config",
        "database",
    ]


def test_run_migrations_evolves_imported_legacy_config_to_current_schema(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
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
    fake_mw = install_fake_anki(
        monkeypatch,
        addon_config,
        tmp_path,
        show_message_box=lambda *args: None,
    )
    use_temp_sqlite(monkeypatch, tmp_path)

    run_migrations()

    smart_fields = SmartFieldService().get_smart_fields_for_note(NOTE_TYPE_ID, DECK_ID)

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
    install_fake_anki(
        monkeypatch,
        addon_config,
        tmp_path,
        show_message_box=lambda *args: None,
    )
    use_temp_sqlite(monkeypatch, tmp_path)

    run_migrations()

    smart_fields = SmartFieldService().get_smart_fields_for_note(NOTE_TYPE_ID, DECK_ID)

    assert len(smart_fields) == 1
    assert isinstance(smart_fields[0].settings, ChatSmartFieldSettings)
    assert smart_fields[0].settings.uses_default_generation_settings is True
    assert smart_fields[0].settings.provider == "auto"
    assert smart_fields[0].settings.model == "auto"


def test_run_migrations_fails_for_old_bootstrap_only_schema_before_legacy_import(
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
    messages: list[tuple[object, ...]] = []
    monkeypatch.setattr(
        "src.database.migrations.show_message_box",
        lambda *args: messages.append(args),
    )
    apply_database_bootstrap_migrations(str(database_path))
    replace_smart_fields_with_old_unprofiled_bootstrap_schema(database_path)

    with pytest.raises(
        RuntimeError,
        match=("legacy config import is pending, but smart_fields lacks profile_name"),
    ):
        run_migrations()

    with sqlite3.connect(database_path) as conn:
        applied_migrations = {
            row[0] for row in conn.execute("SELECT migration_id FROM _yoyo_migration")
        }

    assert messages == [
        (
            "Smart Notes could not finish upgrading your Smart Fields.",
            "Please email support@smart-notes.xyz and include your smart-notes.log file.",
        )
    ]
    assert applied_migrations == {"0001_initial_smart_fields_schema"}


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
