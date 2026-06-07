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

import pytest
import yoyo.backends.base
from yoyo import read_migrations

from src.database import (
    get_database_path,
    get_sqlite_backend,
    open_database,
)
from src.database.migrations import apply_database_migrations


def test_apply_database_migrations_creates_smart_field_tables(tmp_path: Path) -> None:
    database_path = tmp_path / "smart_notes.sqlite3"

    apply_database_migrations(str(database_path))

    conn = sqlite3.connect(database_path)
    try:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }

        assert "smart_fields" in tables
        assert "text_smart_field_settings" in tables
        assert "tts_smart_field_settings" in tables
        assert "image_smart_field_settings" in tables
        assert "default_text_generation_settings" in tables
        assert "default_tts_generation_settings" in tables
        assert "default_image_generation_settings" in tables

        smart_field_columns = {
            row[1] for row in conn.execute("PRAGMA table_info(smart_fields)")
        }
        assert smart_field_columns == {
            "id",
            "profile_name",
            "note_type_id",
            "deck_id",
            "target_field_name",
            "field_type",
            "enabled",
            "created_at",
            "updated_at",
        }
    finally:
        conn.close()


def test_apply_database_migrations_does_not_require_yoyo_entry_points(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(yoyo.backends.base, "entry_points", lambda group: {})

    apply_database_migrations(str(tmp_path / "smart_notes.sqlite3"))


def test_open_database_closes_connection_after_context(tmp_path: Path) -> None:
    database_path = tmp_path / "smart_notes.sqlite3"

    with open_database(str(database_path)) as conn:
        conn.execute("CREATE TABLE example(id INTEGER PRIMARY KEY)")

    with pytest.raises(sqlite3.ProgrammingError, match="closed database"):
        conn.execute("SELECT 1")


def test_deprecated_chat_models_migrate_to_auto(tmp_path: Path) -> None:
    database_path = tmp_path / "smart_notes.sqlite3"
    migrations_path = Path(__file__).parents[1] / "src" / "database" / "db_migrations"
    migrations = read_migrations(str(migrations_path))
    backend = get_sqlite_backend(str(database_path))

    with backend.lock():
        backend.apply_migrations(migrations[:1])

    conn = sqlite3.connect(database_path)
    try:
        for index, model in enumerate(
            ["deepseek-v3", "gpt-4o-mini", "gpt-5-nano", "gpt-5-mini"]
        ):
            smart_field_id = f"field-{index}"
            conn.execute(
                """
                INSERT INTO smart_fields (
                    id, note_type_id, deck_id, target_field_name, field_type,
                    enabled, created_at, updated_at
                )
                VALUES (?, 1, 1, ?, 'chat', 1, 'now', 'now')
                """,
                (smart_field_id, f"Field {index}"),
            )
            conn.execute(
                """
                INSERT INTO text_smart_field_settings (
                    smart_field_id, prompt_text, uses_default_generation_settings,
                    provider, model, reasoning_level, web_search_enabled
                )
                VALUES (?, 'prompt', 0, ?, ?, 'off', 0)
                """,
                (
                    smart_field_id,
                    "deepseek" if model == "deepseek-v3" else "openai",
                    model,
                ),
            )
        conn.commit()
    finally:
        conn.close()

    with backend.lock():
        backend.apply_migrations(migrations[1:])

    conn = sqlite3.connect(database_path)
    try:
        rows = conn.execute(
            """
            SELECT smart_field_id, provider, model
            FROM text_smart_field_settings
            ORDER BY smart_field_id
            """
        ).fetchall()
    finally:
        conn.close()

    assert rows == [
        ("field-0", "auto", "auto"),
        ("field-1", "auto", "auto"),
        ("field-2", "auto", "auto"),
        ("field-3", "openai", "gpt-5-mini"),
    ]


def test_deprecated_default_chat_model_migrates_to_auto(tmp_path: Path) -> None:
    database_path = tmp_path / "smart_notes.sqlite3"
    migrations_path = Path(__file__).parents[1] / "src" / "database" / "db_migrations"
    migrations = read_migrations(str(migrations_path))
    backend = get_sqlite_backend(str(database_path))

    with backend.lock():
        backend.apply_migrations(migrations[:1])

    conn = sqlite3.connect(database_path)
    try:
        conn.execute(
            """
            UPDATE default_text_generation_settings
            SET provider = 'openai', model = 'gpt-5-nano'
            WHERE id = 1
            """
        )
        conn.commit()
    finally:
        conn.close()

    with backend.lock():
        backend.apply_migrations(migrations[1:])

    conn = sqlite3.connect(database_path)
    try:
        row = conn.execute(
            """
            SELECT provider, model
            FROM default_text_generation_settings
            WHERE id = 1
            """
        ).fetchone()
    finally:
        conn.close()

    assert row == ("auto", "auto")


def test_profile_scope_migration_allows_same_field_in_different_profiles(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "smart_notes.sqlite3"
    conn = sqlite3.connect(database_path)
    try:
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
        conn.execute(
            """
            INSERT INTO smart_fields (
                id, note_type_id, deck_id, target_field_name, field_type,
                enabled, created_at, updated_at
            )
            VALUES ('legacy', 1, 1, 'Back', 'chat', 1, 'now', 'now')
            """
        )
        conn.execute(
            """
            CREATE TABLE text_smart_field_settings (
                smart_field_id TEXT PRIMARY KEY REFERENCES smart_fields(id) ON DELETE CASCADE,
                prompt_text TEXT NOT NULL,
                uses_default_generation_settings INTEGER NOT NULL DEFAULT 1 CHECK (uses_default_generation_settings IN (0, 1)),
                provider TEXT,
                model TEXT,
                reasoning_level TEXT CHECK (reasoning_level IN ('off', 'low', 'high')),
                web_search_enabled INTEGER CHECK (web_search_enabled IN (0, 1))
            );
            """
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
        conn.commit()

        conn.close()

        migrations_path = (
            Path(__file__).parents[1] / "src" / "database" / "db_migrations"
        )
        migrations = read_migrations(str(migrations_path))
        backend = get_sqlite_backend(str(database_path))
        with backend.lock():
            backend.apply_migrations(migrations[2:3])

        conn = sqlite3.connect(database_path)
        joined_row = conn.execute(
            """
            SELECT sf.profile_name, text.prompt_text, text.provider, text.model
            FROM smart_fields sf
            JOIN text_smart_field_settings text ON text.smart_field_id = sf.id
            WHERE sf.id = 'legacy'
            """
        ).fetchone()

        assert joined_row == ("__test__", "{{Front}}", "openai", "gpt-5-mini")

        conn.execute(
            """
            INSERT INTO smart_fields (
                id, profile_name, note_type_id, deck_id, target_field_name,
                field_type, enabled, created_at, updated_at
            )
            VALUES ('profile-1', 'Profile 1', 1, 1, 'Back', 'chat', 1, 'now', 'now')
            """
        )
        conn.execute(
            """
            INSERT INTO smart_fields (
                id, profile_name, note_type_id, deck_id, target_field_name,
                field_type, enabled, created_at, updated_at
            )
            VALUES ('profile-2', 'Profile 2', 1, 1, 'Back', 'chat', 1, 'now', 'now')
            """
        )

        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                """
                INSERT INTO smart_fields (
                    id, profile_name, note_type_id, deck_id, target_field_name,
                    field_type, enabled, created_at, updated_at
                )
                VALUES (
                    'profile-1-duplicate', 'Profile 1', 1, 1, 'Back',
                    'chat', 1, 'now', 'now'
                )
                """
            )
    finally:
        conn.close()


def test_get_database_path_uses_anki_preserved_user_files() -> None:
    assert get_database_path().endswith("/user_files/smart_notes.sqlite3")
    assert "/src/user_files/" not in get_database_path()
