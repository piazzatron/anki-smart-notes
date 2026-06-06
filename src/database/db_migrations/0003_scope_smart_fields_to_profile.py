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

from yoyo import step


def _scope_smart_fields_to_profile(conn: sqlite3.Connection) -> None:
    columns = _smart_field_columns(conn)
    if "profile_name" in columns:
        return

    conn.execute(
        """
        CREATE TABLE smart_fields_new (
            id TEXT PRIMARY KEY,
            profile_name TEXT,
            note_type_id INTEGER NOT NULL,
            deck_id INTEGER NOT NULL,
            target_field_name TEXT NOT NULL,
            field_type TEXT NOT NULL CHECK (field_type IN ('chat', 'tts', 'image')),
            enabled INTEGER NOT NULL DEFAULT 1 CHECK (enabled IN (0, 1)),
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(profile_name, note_type_id, deck_id, target_field_name)
        );
        """
    )
    conn.execute(
        """
        INSERT INTO smart_fields_new (
            id, profile_name, note_type_id, deck_id, target_field_name, field_type,
            enabled, created_at, updated_at
        )
        SELECT
            id, NULL, note_type_id, deck_id, target_field_name, field_type,
            enabled, created_at, updated_at
        FROM smart_fields;
        """
    )
    conn.execute("DROP TABLE smart_fields;")
    conn.execute("ALTER TABLE smart_fields_new RENAME TO smart_fields;")


def _undo_scope_smart_fields_to_profile(conn: sqlite3.Connection) -> None:
    columns = _smart_field_columns(conn)
    if "profile_name" not in columns:
        return

    conn.execute(
        """
        CREATE TABLE smart_fields_old (
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
        INSERT INTO smart_fields_old (
            id, note_type_id, deck_id, target_field_name, field_type,
            enabled, created_at, updated_at
        )
        SELECT
            id, note_type_id, deck_id, target_field_name, field_type,
            enabled, created_at, updated_at
        FROM smart_fields
        WHERE profile_name IS NULL
            OR profile_name = (
                SELECT profile_name
                FROM smart_fields
                ORDER BY profile_name IS NULL, profile_name
                LIMIT 1
            );
        """
    )
    conn.execute("DROP TABLE smart_fields;")
    conn.execute("ALTER TABLE smart_fields_old RENAME TO smart_fields;")


def _smart_field_columns(conn: sqlite3.Connection) -> set[str]:
    return {row[1] for row in conn.execute("PRAGMA table_info(smart_fields)")}


steps = [
    step(_scope_smart_fields_to_profile, _undo_scope_smart_fields_to_profile),
]
