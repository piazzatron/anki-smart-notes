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

from yoyo import step

steps = [
    step(
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
        """,
        "DROP TABLE smart_fields;",
    ),
    step(
        """
        CREATE TABLE text_smart_field_settings (
            smart_field_id TEXT PRIMARY KEY REFERENCES smart_fields(id) ON DELETE CASCADE,
            prompt_text TEXT NOT NULL,
            provider TEXT NOT NULL,
            model TEXT NOT NULL,
            reasoning_level TEXT NOT NULL DEFAULT 'off' CHECK (reasoning_level IN ('off', 'low', 'high')),
            web_search_enabled INTEGER NOT NULL DEFAULT 0 CHECK (web_search_enabled IN (0, 1))
        );
        """,
        "DROP TABLE text_smart_field_settings;",
    ),
    step(
        """
        CREATE TABLE tts_smart_field_settings (
            smart_field_id TEXT PRIMARY KEY REFERENCES smart_fields(id) ON DELETE CASCADE,
            source_field_name TEXT NOT NULL,
            provider TEXT NOT NULL,
            model TEXT NOT NULL,
            voice_id TEXT NOT NULL
        );
        """,
        "DROP TABLE tts_smart_field_settings;",
    ),
    step(
        """
        CREATE TABLE image_smart_field_settings (
            smart_field_id TEXT PRIMARY KEY REFERENCES smart_fields(id) ON DELETE CASCADE,
            prompt_text TEXT NOT NULL,
            provider TEXT NOT NULL,
            model TEXT NOT NULL
        );
        """,
        "DROP TABLE image_smart_field_settings;",
    ),
]
