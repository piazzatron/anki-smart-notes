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

# Auto Max is `auto` at reasoning level `max`, not its own `auto-max` model. SQLite
# can't alter a CHECK constraint, so both text settings tables are rebuilt to allow
# `max`, and saved `auto-max` rows move to `auto` at `max` on the way through.
REASONING_LEVEL_FROM_MODEL = (
    "CASE WHEN model = 'auto-max' THEN 'max' ELSE reasoning_level END"
)
MODEL_WITHOUT_AUTO_MAX = "CASE WHEN model = 'auto-max' THEN 'auto' ELSE model END"

steps = [
    step(
        """
        CREATE TABLE default_text_generation_settings_new (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            provider TEXT NOT NULL,
            model TEXT NOT NULL,
            reasoning_level TEXT NOT NULL DEFAULT 'off' CHECK (reasoning_level IN ('off', 'low', 'high', 'max')),
            web_search_enabled INTEGER NOT NULL DEFAULT 0 CHECK (web_search_enabled IN (0, 1))
        );
        """,
        "SELECT 1;",
    ),
    step(
        f"""
        INSERT INTO default_text_generation_settings_new (
            id, provider, model, reasoning_level, web_search_enabled
        )
        SELECT
            id, provider, {MODEL_WITHOUT_AUTO_MAX},
            {REASONING_LEVEL_FROM_MODEL}, web_search_enabled
        FROM default_text_generation_settings;
        """,
        "SELECT 1;",
    ),
    step(
        """
        DROP TABLE default_text_generation_settings;
        """,
        "SELECT 1;",
    ),
    step(
        """
        ALTER TABLE default_text_generation_settings_new
            RENAME TO default_text_generation_settings;
        """,
        "SELECT 1;",
    ),
    step(
        """
        CREATE TABLE text_smart_field_settings_new (
            smart_field_id TEXT PRIMARY KEY REFERENCES smart_fields(id) ON DELETE CASCADE,
            prompt_text TEXT NOT NULL,
            uses_default_generation_settings INTEGER NOT NULL DEFAULT 1 CHECK (uses_default_generation_settings IN (0, 1)),
            provider TEXT,
            model TEXT,
            reasoning_level TEXT CHECK (reasoning_level IN ('off', 'low', 'high', 'max')),
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
        "SELECT 1;",
    ),
    step(
        f"""
        INSERT INTO text_smart_field_settings_new (
            smart_field_id, prompt_text, uses_default_generation_settings,
            provider, model, reasoning_level, web_search_enabled
        )
        SELECT
            smart_field_id, prompt_text, uses_default_generation_settings,
            provider, {MODEL_WITHOUT_AUTO_MAX}, {REASONING_LEVEL_FROM_MODEL},
            web_search_enabled
        FROM text_smart_field_settings;
        """,
        "SELECT 1;",
    ),
    step(
        """
        DROP TABLE text_smart_field_settings;
        """,
        "SELECT 1;",
    ),
    step(
        """
        ALTER TABLE text_smart_field_settings_new
            RENAME TO text_smart_field_settings;
        """,
        "SELECT 1;",
    ),
]
