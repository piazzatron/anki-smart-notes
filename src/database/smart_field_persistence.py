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

from ..models import (
    ChatGenerationSettings,
    ImageGenerationSettings,
    TTSGenerationSettings,
)
from ..models.smart_fields import (
    ChatSmartFieldSettings,
    SmartFieldSettings,
    TTSSmartFieldSettings,
)


def upsert_chat_generation_defaults(
    conn: sqlite3.Connection, settings: ChatGenerationSettings
) -> None:
    conn.execute(
        """
        INSERT INTO default_text_generation_settings (
            id, provider, model, reasoning_level, web_search_enabled
        )
        VALUES (1, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            provider = excluded.provider,
            model = excluded.model,
            reasoning_level = excluded.reasoning_level,
            web_search_enabled = excluded.web_search_enabled
        """,
        (
            settings.provider,
            settings.model,
            settings.reasoning_level,
            int(settings.web_search_enabled),
        ),
    )


def upsert_tts_generation_defaults(
    conn: sqlite3.Connection, settings: TTSGenerationSettings
) -> None:
    conn.execute(
        """
        INSERT INTO default_tts_generation_settings (
            id, provider, model, voice_id
        )
        VALUES (1, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            provider = excluded.provider,
            model = excluded.model,
            voice_id = excluded.voice_id
        """,
        (settings.provider, settings.model, settings.voice_id),
    )


def upsert_image_generation_defaults(
    conn: sqlite3.Connection, settings: ImageGenerationSettings
) -> None:
    conn.execute(
        """
        INSERT INTO default_image_generation_settings (
            id, provider, model
        )
        VALUES (1, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            provider = excluded.provider,
            model = excluded.model
        """,
        (settings.provider, settings.model),
    )


def insert_smart_field_settings(
    conn: sqlite3.Connection,
    smart_field_id: str,
    settings: SmartFieldSettings,
) -> None:
    # Legacy config import also uses these inserts before later migrations run.
    # Keep them compatible with the bootstrap settings schema.
    if isinstance(settings, ChatSmartFieldSettings):
        conn.execute(
            """
            INSERT INTO text_smart_field_settings (
                smart_field_id, prompt_text, uses_default_generation_settings,
                provider, model, reasoning_level, web_search_enabled
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                smart_field_id,
                settings.prompt_text,
                int(settings.uses_default_generation_settings),
                None
                if settings.uses_default_generation_settings
                else settings.provider,
                None if settings.uses_default_generation_settings else settings.model,
                None
                if settings.uses_default_generation_settings
                else settings.reasoning_level,
                None
                if settings.uses_default_generation_settings
                else int(settings.web_search_enabled),
            ),
        )
        return

    if isinstance(settings, TTSSmartFieldSettings):
        conn.execute(
            """
            INSERT INTO tts_smart_field_settings (
                smart_field_id, source_field_name, uses_default_generation_settings,
                provider, model, voice_id
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                smart_field_id,
                settings.source_field_name,
                int(settings.uses_default_generation_settings),
                None
                if settings.uses_default_generation_settings
                else settings.provider,
                None if settings.uses_default_generation_settings else settings.model,
                None
                if settings.uses_default_generation_settings
                else settings.voice_id,
            ),
        )
        return

    conn.execute(
        """
        INSERT INTO image_smart_field_settings (
            smart_field_id, prompt_text, uses_default_generation_settings,
            provider, model
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            smart_field_id,
            settings.prompt_text,
            int(settings.uses_default_generation_settings),
            None if settings.uses_default_generation_settings else settings.provider,
            None if settings.uses_default_generation_settings else settings.model,
        ),
    )
