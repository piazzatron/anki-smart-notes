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

from src.database import apply_database_migrations, get_database_path


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
        assert "chat_smart_field_settings" in tables
        assert "tts_smart_field_settings" in tables
        assert "image_smart_field_settings" in tables

        smart_field_columns = {
            row[1] for row in conn.execute("PRAGMA table_info(smart_fields)")
        }
        assert smart_field_columns == {
            "id",
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


def test_get_database_path_uses_anki_preserved_user_files() -> None:
    assert get_database_path().endswith("/user_files/smart_notes.sqlite3")
    assert "/src/user_files/" not in get_database_path()
