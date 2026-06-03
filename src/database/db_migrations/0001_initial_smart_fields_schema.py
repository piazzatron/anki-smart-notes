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
        CREATE TABLE default_text_generation_settings (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            provider TEXT NOT NULL,
            model TEXT NOT NULL,
            reasoning_level TEXT NOT NULL DEFAULT 'off' CHECK (reasoning_level IN ('off', 'low', 'high')),
            web_search_enabled INTEGER NOT NULL DEFAULT 0 CHECK (web_search_enabled IN (0, 1))
        );
        """,
        "DROP TABLE default_text_generation_settings;",
    ),
    step(
        """
        INSERT INTO default_text_generation_settings (
            id, provider, model, reasoning_level, web_search_enabled
        )
        VALUES (1, 'auto', 'auto', 'off', 0);
        """,
        "DELETE FROM default_text_generation_settings WHERE id = 1;",
    ),
    step(
        """
        CREATE TABLE default_tts_generation_settings (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            provider TEXT NOT NULL,
            model TEXT NOT NULL,
            voice_id TEXT NOT NULL
        );
        """,
        "DROP TABLE default_tts_generation_settings;",
    ),
    step(
        """
        INSERT INTO default_tts_generation_settings (
            id, provider, model, voice_id
        )
        VALUES (1, 'google', 'standard', 'en-US-Casual-K');
        """,
        "DELETE FROM default_tts_generation_settings WHERE id = 1;",
    ),
    step(
        """
        CREATE TABLE default_image_generation_settings (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            provider TEXT NOT NULL,
            model TEXT NOT NULL
        );
        """,
        "DROP TABLE default_image_generation_settings;",
    ),
    step(
        """
        INSERT INTO default_image_generation_settings (
            id, provider, model
        )
        VALUES (1, 'openai', 'gpt-image-1.5-low');
        """,
        "DELETE FROM default_image_generation_settings WHERE id = 1;",
    ),
    step(
        """
        CREATE TABLE text_smart_field_settings (
            smart_field_id TEXT PRIMARY KEY REFERENCES smart_fields(id) ON DELETE CASCADE,
            prompt_text TEXT NOT NULL,
            uses_default_generation_settings INTEGER NOT NULL DEFAULT 1 CHECK (uses_default_generation_settings IN (0, 1)),
            provider TEXT,
            model TEXT,
            reasoning_level TEXT CHECK (reasoning_level IN ('off', 'low', 'high')),
            web_search_enabled INTEGER CHECK (web_search_enabled IN (0, 1)),
            CHECK (
                (
                    uses_default_generation_settings = 1
                    AND provider IS NULL
                    AND model IS NULL
                    AND reasoning_level IS NULL
                    AND web_search_enabled IS NULL
                )
                OR (
                    uses_default_generation_settings = 0
                    AND provider IS NOT NULL
                    AND model IS NOT NULL
                    AND reasoning_level IS NOT NULL
                    AND web_search_enabled IS NOT NULL
                )
            )
        );
        """,
        "DROP TABLE text_smart_field_settings;",
    ),
    step(
        """
        CREATE TABLE tts_smart_field_settings (
            smart_field_id TEXT PRIMARY KEY REFERENCES smart_fields(id) ON DELETE CASCADE,
            source_field_name TEXT NOT NULL,
            uses_default_generation_settings INTEGER NOT NULL DEFAULT 1 CHECK (uses_default_generation_settings IN (0, 1)),
            provider TEXT,
            model TEXT,
            voice_id TEXT,
            CHECK (
                (
                    uses_default_generation_settings = 1
                    AND provider IS NULL
                    AND model IS NULL
                    AND voice_id IS NULL
                )
                OR (
                    uses_default_generation_settings = 0
                    AND provider IS NOT NULL
                    AND model IS NOT NULL
                    AND voice_id IS NOT NULL
                )
            )
        );
        """,
        "DROP TABLE tts_smart_field_settings;",
    ),
    step(
        """
        CREATE TABLE image_smart_field_settings (
            smart_field_id TEXT PRIMARY KEY REFERENCES smart_fields(id) ON DELETE CASCADE,
            prompt_text TEXT NOT NULL,
            uses_default_generation_settings INTEGER NOT NULL DEFAULT 1 CHECK (uses_default_generation_settings IN (0, 1)),
            provider TEXT,
            model TEXT,
            CHECK (
                (
                    uses_default_generation_settings = 1
                    AND provider IS NULL
                    AND model IS NULL
                )
                OR (
                    uses_default_generation_settings = 0
                    AND provider IS NOT NULL
                    AND model IS NOT NULL
                )
            )
        );
        """,
        "DROP TABLE image_smart_field_settings;",
    ),
]
