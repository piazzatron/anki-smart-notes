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


def apply_step(conn: sqlite3.Connection) -> None:
    columns = {
        row[1] for row in conn.execute("PRAGMA table_info(text_smart_field_settings)")
    }
    if "reasoning_level" in columns:
        return

    conn.execute(
        """
        ALTER TABLE text_smart_field_settings
        ADD COLUMN reasoning_level TEXT NOT NULL DEFAULT 'off'
        CHECK (reasoning_level IN ('off', 'low', 'high'));
        """
    )


def rollback_step(conn: sqlite3.Connection) -> None:
    columns = {
        row[1] for row in conn.execute("PRAGMA table_info(text_smart_field_settings)")
    }
    if "reasoning_level" not in columns:
        return

    conn.execute(
        """
        ALTER TABLE text_smart_field_settings
        DROP COLUMN reasoning_level;
        """
    )


steps = [step(apply_step, rollback_step)]
