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
from datetime import datetime, timezone
from typing import Optional, cast
from uuid import uuid4

from anki.decks import DeckId

from ..constants import GLOBAL_DECK_ID
from ..database import open_database
from ..logger import logger
from ..models import (
    ChatModels,
    ChatProviders,
    ImageModels,
    ImageProviders,
    SmartFieldType,
    TTSModels,
    TTSProviders,
)
from ..models.smart_fields import (
    ChatSmartFieldSettings,
    ImageSmartFieldSettings,
    SmartField,
    SmartFieldCreate,
    SmartFieldSettings,
    TTSSmartFieldSettings,
)


class SmartFieldService:
    """Persists smart field rules and maps database rows to domain models."""

    def get_smart_fields_for_note(
        self,
        note_type_id: int,
        deck_id: DeckId,
        include_global: bool = True,
    ) -> list[SmartField]:
        logger.debug(
            f"Smart fields DB: loading fields for note_type_id={note_type_id}, deck_id={deck_id}"
        )
        global_fields: dict[str, SmartField] = {}
        deck_fields: dict[str, SmartField] = {}

        for smart_field in self.get_all_smart_fields():
            if smart_field.note_type_id != note_type_id:
                continue

            field_key = smart_field.target_field_name.lower()
            if smart_field.deck_id == deck_id:
                deck_fields[field_key] = smart_field
            elif include_global and smart_field.deck_id == GLOBAL_DECK_ID:
                global_fields[field_key] = smart_field

        global_fields.update(deck_fields)
        return list(global_fields.values())

    def get_all_smart_fields(self) -> list[SmartField]:
        logger.debug("Smart fields DB: loading all fields")
        with open_database() as conn:
            rows = conn.execute(
                """
                SELECT
                    sf.id,
                    sf.note_type_id,
                    sf.deck_id,
                    sf.target_field_name,
                    sf.field_type,
                    sf.enabled,
                    chat.prompt_text AS chat_prompt,
                    chat.provider AS chat_provider,
                    chat.model AS chat_model,
                    chat.web_search_enabled AS chat_web_search,
                    tts.source_field_name AS tts_source_field,
                    tts.provider AS tts_provider,
                    tts.model AS tts_model,
                    tts.voice_id AS tts_voice,
                    image.prompt_text AS image_prompt,
                    image.provider AS image_provider,
                    image.model AS image_model
                FROM smart_fields sf
                LEFT JOIN text_smart_field_settings chat ON chat.smart_field_id = sf.id
                LEFT JOIN tts_smart_field_settings tts ON tts.smart_field_id = sf.id
                LEFT JOIN image_smart_field_settings image ON image.smart_field_id = sf.id
                ORDER BY sf.note_type_id, sf.deck_id, sf.target_field_name
                """
            ).fetchall()
        return [self._smart_field_from_row(row) for row in rows]

    def save_smart_field(self, smart_field: SmartFieldCreate) -> None:
        logger.debug(
            f"Smart fields DB: saving {smart_field.field_type} field "
            f"{smart_field.note_type_id}/{smart_field.deck_id}/{smart_field.target_field_name}"
        )
        with open_database() as conn:
            smart_field_id = self._save_smart_field(conn, smart_field)
            conn.commit()
        logger.debug(f"Smart fields DB: saved smart_field_id={smart_field_id}")

    def replace_all_smart_fields(self, smart_fields: list[SmartFieldCreate]) -> None:
        logger.debug(
            f"Smart fields DB: replacing all fields with {len(smart_fields)} field(s)"
        )
        with open_database() as conn:
            conn.execute("DELETE FROM smart_fields")
            for smart_field in smart_fields:
                self._save_smart_field(conn, smart_field)
            conn.commit()

    def delete_smart_field(
        self, note_type_id: int, deck_id: DeckId, target_field: str
    ) -> None:
        logger.debug(
            f"Smart fields DB: removing {note_type_id}/{deck_id}/{target_field}"
        )
        with open_database() as conn:
            conn.execute(
                """
                DELETE FROM smart_fields
                WHERE note_type_id = ?
                    AND deck_id = ?
                    AND lower(target_field_name) = lower(?)
                """,
                (note_type_id, int(deck_id), target_field),
            )
            conn.commit()

    def _save_smart_field(
        self, conn: sqlite3.Connection, smart_field: SmartFieldCreate
    ) -> str:
        existing_id = self._get_existing_id(
            conn,
            smart_field.note_type_id,
            smart_field.deck_id,
            smart_field.target_field_name,
        )
        smart_field_id = existing_id or str(uuid4())
        now = self._now()

        if existing_id:
            conn.execute(
                """
                UPDATE smart_fields
                SET target_field_name = ?, field_type = ?, enabled = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    smart_field.target_field_name,
                    smart_field.field_type,
                    int(smart_field.enabled),
                    now,
                    smart_field_id,
                ),
            )
            self._delete_settings(conn, smart_field_id)
        else:
            conn.execute(
                """
                INSERT INTO smart_fields (
                    id, note_type_id, deck_id, target_field_name, field_type,
                    enabled, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    smart_field_id,
                    smart_field.note_type_id,
                    int(smart_field.deck_id),
                    smart_field.target_field_name,
                    smart_field.field_type,
                    int(smart_field.enabled),
                    now,
                    now,
                ),
            )

        self._insert_settings(conn, smart_field_id, smart_field.settings)
        return smart_field_id

    def _insert_settings(
        self,
        conn: sqlite3.Connection,
        smart_field_id: str,
        settings: SmartFieldSettings,
    ) -> None:
        if isinstance(settings, ChatSmartFieldSettings):
            conn.execute(
                """
                INSERT INTO text_smart_field_settings (
                    smart_field_id, prompt_text, provider, model, web_search_enabled
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    smart_field_id,
                    settings.prompt_text,
                    settings.provider,
                    settings.model,
                    int(settings.web_search_enabled),
                ),
            )
            return

        if isinstance(settings, TTSSmartFieldSettings):
            conn.execute(
                """
                INSERT INTO tts_smart_field_settings (
                    smart_field_id, source_field_name, provider, model, voice_id
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    smart_field_id,
                    settings.source_field_name,
                    settings.provider,
                    settings.model,
                    settings.voice_id,
                ),
            )
            return

        conn.execute(
            """
            INSERT INTO image_smart_field_settings (
                smart_field_id, prompt_text, provider, model
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                smart_field_id,
                settings.prompt_text,
                settings.provider,
                settings.model,
            ),
        )

    def _smart_field_from_row(self, row: sqlite3.Row) -> SmartField:
        field_type = cast(SmartFieldType, row["field_type"])
        if field_type == "chat":
            settings: SmartFieldSettings = ChatSmartFieldSettings(
                prompt_text=cast(str, row["chat_prompt"]),
                provider=cast(ChatProviders, row["chat_provider"]),
                model=cast(ChatModels, row["chat_model"]),
                web_search_enabled=bool(row["chat_web_search"]),
            )
        elif field_type == "tts":
            settings = TTSSmartFieldSettings(
                source_field_name=cast(str, row["tts_source_field"]),
                provider=cast(TTSProviders, row["tts_provider"]),
                model=cast(TTSModels, row["tts_model"]),
                voice_id=cast(str, row["tts_voice"]),
            )
        else:
            settings = ImageSmartFieldSettings(
                prompt_text=cast(str, row["image_prompt"]),
                provider=cast(ImageProviders, row["image_provider"]),
                model=cast(ImageModels, row["image_model"]),
            )

        return SmartField(
            id=cast(str, row["id"]),
            note_type_id=int(row["note_type_id"]),
            deck_id=cast(DeckId, int(row["deck_id"])),
            target_field_name=cast(str, row["target_field_name"]),
            enabled=bool(row["enabled"]),
            settings=settings,
        )

    def _get_existing_id(
        self,
        conn: sqlite3.Connection,
        note_type_id: int,
        deck_id: DeckId,
        target_field: str,
    ) -> Optional[str]:
        row = conn.execute(
            """
            SELECT id FROM smart_fields
            WHERE note_type_id = ?
                AND deck_id = ?
                AND lower(target_field_name) = lower(?)
            """,
            (note_type_id, int(deck_id), target_field),
        ).fetchone()
        return cast(str, row["id"]) if row else None

    def _delete_settings(self, conn: sqlite3.Connection, smart_field_id: str) -> None:
        conn.execute(
            "DELETE FROM text_smart_field_settings WHERE smart_field_id = ?",
            (smart_field_id,),
        )
        conn.execute(
            "DELETE FROM tts_smart_field_settings WHERE smart_field_id = ?",
            (smart_field_id,),
        )
        conn.execute(
            "DELETE FROM image_smart_field_settings WHERE smart_field_id = ?",
            (smart_field_id,),
        )

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()


smart_field_service = SmartFieldService()
