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
from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any, Optional, cast
from uuid import uuid4

from anki.decks import DeckId

from ..constants import GLOBAL_DECK_ID
from ..database import open_database
from ..logger import logger
from ..models import (
    ChatGenerationSettings,
    ChatModels,
    ChatProviders,
    ChatReasoningLevel,
    ImageGenerationSettings,
    ImageModels,
    ImageProviders,
    SmartFieldType,
    TTSGenerationSettings,
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

DEFAULT_TEXT_GENERATION_SETTINGS = ChatGenerationSettings(
    provider="auto",
    model="auto",
    reasoning_level="off",
    web_search_enabled=False,
)
DEFAULT_TTS_GENERATION_SETTINGS = TTSGenerationSettings(
    provider="google",
    model="standard",
    voice_id="en-US-Casual-K",
)
DEFAULT_IMAGE_GENERATION_SETTINGS = ImageGenerationSettings(
    provider="openai",
    model="gpt-image-1.5-low",
)


class SmartFieldService:
    """Persists Smart Field rules and global generation defaults."""

    def get_chat_defaults(self) -> ChatGenerationSettings:
        with open_database() as conn:
            row = conn.execute(
                """
                SELECT provider, model, reasoning_level, web_search_enabled
                FROM default_text_generation_settings
                WHERE id = 1
                """
            ).fetchone()
        if not row:
            raise RuntimeError("Missing default text generation settings row")
        return _chat_generation_settings_from_row(row)

    def save_chat_defaults(self, settings: ChatGenerationSettings) -> None:
        with open_database() as conn:
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
            conn.commit()

    def get_tts_defaults(self) -> TTSGenerationSettings:
        with open_database() as conn:
            row = conn.execute(
                """
                SELECT provider, model, voice_id
                FROM default_tts_generation_settings
                WHERE id = 1
                """
            ).fetchone()
        if not row:
            raise RuntimeError("Missing default TTS generation settings row")
        return _tts_generation_settings_from_row(row)

    def save_tts_defaults(self, settings: TTSGenerationSettings) -> None:
        with open_database() as conn:
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
            conn.commit()

    def get_image_defaults(self) -> ImageGenerationSettings:
        with open_database() as conn:
            row = conn.execute(
                """
                SELECT provider, model
                FROM default_image_generation_settings
                WHERE id = 1
                """
            ).fetchone()
        if not row:
            raise RuntimeError("Missing default image generation settings row")
        return _image_generation_settings_from_row(row)

    def save_image_defaults(self, settings: ImageGenerationSettings) -> None:
        with open_database() as conn:
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
            conn.commit()

    def restore_generation_defaults(self) -> None:
        self.save_chat_defaults(DEFAULT_TEXT_GENERATION_SETTINGS)
        self.save_tts_defaults(DEFAULT_TTS_GENERATION_SETTINGS)
        self.save_image_defaults(DEFAULT_IMAGE_GENERATION_SETTINGS)

    def import_generation_defaults_from_legacy_config(
        self, addon_config: Mapping[str, Any]
    ) -> None:
        self.save_chat_defaults(
            ChatGenerationSettings(
                provider=cast(
                    ChatProviders,
                    addon_config.get("chat_provider")
                    or DEFAULT_TEXT_GENERATION_SETTINGS.provider,
                ),
                model=cast(
                    ChatModels,
                    addon_config.get("chat_model")
                    or DEFAULT_TEXT_GENERATION_SETTINGS.model,
                ),
                reasoning_level=_validated_reasoning_level(
                    addon_config.get("chat_reasoning_level")
                ),
                web_search_enabled=bool(
                    addon_config.get("chat_web_search")
                    if addon_config.get("chat_web_search") is not None
                    else DEFAULT_TEXT_GENERATION_SETTINGS.web_search_enabled
                ),
            )
        )
        self.save_tts_defaults(
            TTSGenerationSettings(
                provider=cast(
                    TTSProviders,
                    addon_config.get("tts_provider")
                    or DEFAULT_TTS_GENERATION_SETTINGS.provider,
                ),
                model=cast(
                    TTSModels,
                    addon_config.get("tts_model")
                    or DEFAULT_TTS_GENERATION_SETTINGS.model,
                ),
                voice_id=str(
                    addon_config.get("tts_voice")
                    or DEFAULT_TTS_GENERATION_SETTINGS.voice_id
                ),
            )
        )
        self.save_image_defaults(
            ImageGenerationSettings(
                provider=cast(
                    ImageProviders,
                    addon_config.get("image_provider")
                    or DEFAULT_IMAGE_GENERATION_SETTINGS.provider,
                ),
                model=cast(
                    ImageModels,
                    addon_config.get("image_model")
                    or DEFAULT_IMAGE_GENERATION_SETTINGS.model,
                ),
            )
        )

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
                    chat.uses_default_generation_settings AS chat_uses_default,
                    COALESCE(chat.provider, text_defaults.provider) AS chat_provider,
                    COALESCE(chat.model, text_defaults.model) AS chat_model,
                    COALESCE(chat.reasoning_level, text_defaults.reasoning_level) AS chat_reasoning_level,
                    COALESCE(chat.web_search_enabled, text_defaults.web_search_enabled) AS chat_web_search,
                    tts.source_field_name AS tts_source_field,
                    tts.uses_default_generation_settings AS tts_uses_default,
                    COALESCE(tts.provider, tts_defaults.provider) AS tts_provider,
                    COALESCE(tts.model, tts_defaults.model) AS tts_model,
                    COALESCE(tts.voice_id, tts_defaults.voice_id) AS tts_voice,
                    image.prompt_text AS image_prompt,
                    image.uses_default_generation_settings AS image_uses_default,
                    COALESCE(image.provider, image_defaults.provider) AS image_provider,
                    COALESCE(image.model, image_defaults.model) AS image_model
                FROM smart_fields sf
                LEFT JOIN text_smart_field_settings chat ON chat.smart_field_id = sf.id
                LEFT JOIN tts_smart_field_settings tts ON tts.smart_field_id = sf.id
                LEFT JOIN image_smart_field_settings image ON image.smart_field_id = sf.id
                LEFT JOIN default_text_generation_settings text_defaults ON text_defaults.id = 1
                LEFT JOIN default_tts_generation_settings tts_defaults ON tts_defaults.id = 1
                LEFT JOIN default_image_generation_settings image_defaults ON image_defaults.id = 1
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
                    None
                    if settings.uses_default_generation_settings
                    else settings.model,
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
                    None
                    if settings.uses_default_generation_settings
                    else settings.model,
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
                None
                if settings.uses_default_generation_settings
                else settings.provider,
                None if settings.uses_default_generation_settings else settings.model,
            ),
        )

    def _smart_field_from_row(self, row: sqlite3.Row) -> SmartField:
        field_type = cast(SmartFieldType, row["field_type"])
        if field_type == "chat":
            settings: SmartFieldSettings = ChatSmartFieldSettings(
                prompt_text=cast(str, row["chat_prompt"]),
                provider=cast(ChatProviders, row["chat_provider"]),
                model=cast(ChatModels, row["chat_model"]),
                reasoning_level=cast(ChatReasoningLevel, row["chat_reasoning_level"]),
                web_search_enabled=bool(row["chat_web_search"]),
                uses_default_generation_settings=bool(row["chat_uses_default"]),
            )
        elif field_type == "tts":
            settings = TTSSmartFieldSettings(
                source_field_name=cast(str, row["tts_source_field"]),
                provider=cast(TTSProviders, row["tts_provider"]),
                model=cast(TTSModels, row["tts_model"]),
                voice_id=cast(str, row["tts_voice"]),
                uses_default_generation_settings=bool(row["tts_uses_default"]),
            )
        else:
            settings = ImageSmartFieldSettings(
                prompt_text=cast(str, row["image_prompt"]),
                provider=cast(ImageProviders, row["image_provider"]),
                model=cast(ImageModels, row["image_model"]),
                uses_default_generation_settings=bool(row["image_uses_default"]),
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


def _validated_reasoning_level(value: object) -> ChatReasoningLevel:
    if value in {"off", "low", "high"}:
        return cast(ChatReasoningLevel, value)
    return DEFAULT_TEXT_GENERATION_SETTINGS.reasoning_level


def _chat_generation_settings_from_row(row: sqlite3.Row) -> ChatGenerationSettings:
    return ChatGenerationSettings(
        provider=cast(ChatProviders, row["provider"]),
        model=cast(ChatModels, row["model"]),
        reasoning_level=cast(ChatReasoningLevel, row["reasoning_level"]),
        web_search_enabled=bool(row["web_search_enabled"]),
    )


def _tts_generation_settings_from_row(row: sqlite3.Row) -> TTSGenerationSettings:
    return TTSGenerationSettings(
        provider=cast(TTSProviders, row["provider"]),
        model=cast(TTSModels, row["model"]),
        voice_id=cast(str, row["voice_id"]),
    )


def _image_generation_settings_from_row(row: sqlite3.Row) -> ImageGenerationSettings:
    return ImageGenerationSettings(
        provider=cast(ImageProviders, row["provider"]),
        model=cast(ImageModels, row["model"]),
    )


smart_field_service = SmartFieldService()
