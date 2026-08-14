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
from typing import Callable, Optional, Union, cast
from uuid import uuid4

from anki.decks import DeckId

from .. import utils
from ..constants import GLOBAL_DECK_ID
from ..database.connection import open_database
from ..event_bus import republish_state
from ..logger import logger
from ..models import (
    ChatGenerationSettings,
    ChatModels,
    ChatProviders,
    ChatReasoningLevel,
    GenerationDefaults,
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
from ..prompt_fields import get_prompt_fields

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
SMART_FIELD_TARGET_COLLISION_ERROR = (
    "A Smart Field already exists for that note type, deck, and field"
)
SMART_FIELD_CYCLE_ERROR = (
    "Smart fields referencing other smart fields cannot make a cycle! 🔁"
)


class SmartFieldService:
    """Persists runtime Smart Field rules and global generation defaults.

    Legacy prompt-map import owns separate SQL in the migration layer because it
    ports old config data into the bootstrap schema; this service only owns
    normal reads and writes after the full migration pipeline has completed.
    """

    def __init__(self, get_profile_name: Optional[Callable[[], str]] = None) -> None:
        self._get_profile_name = get_profile_name or utils.get_current_profile_name

    def get_chat_defaults(self) -> ChatGenerationSettings:
        with open_database() as conn:
            row = conn.execute(
                """
                SELECT provider, model, reasoning_level, web_search_enabled
                FROM default_text_generation_settings
                WHERE id = 1
                """
            ).fetchone()
        if row is None:
            raise RuntimeError("Missing default text generation settings row")
        return _chat_generation_settings_from_row(row)

    @republish_state
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

    def get_tts_defaults(self) -> TTSGenerationSettings:
        with open_database() as conn:
            row = conn.execute(
                """
                SELECT provider, model, voice_id
                FROM default_tts_generation_settings
                WHERE id = 1
                """
            ).fetchone()
        if row is None:
            raise RuntimeError("Missing default TTS generation settings row")
        return _tts_generation_settings_from_row(row)

    @republish_state
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

    def get_image_defaults(self) -> ImageGenerationSettings:
        with open_database() as conn:
            row = conn.execute(
                """
                SELECT provider, model
                FROM default_image_generation_settings
                WHERE id = 1
                """
            ).fetchone()
        if row is None:
            raise RuntimeError("Missing default image generation settings row")
        return _image_generation_settings_from_row(row)

    @republish_state
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

    @republish_state
    def restore_generation_defaults(self) -> None:
        self.save_chat_defaults(DEFAULT_TEXT_GENERATION_SETTINGS)
        self.save_tts_defaults(DEFAULT_TTS_GENERATION_SETTINGS)
        self.save_image_defaults(DEFAULT_IMAGE_GENERATION_SETTINGS)

    def get_generation_defaults(self) -> GenerationDefaults:
        with open_database() as conn:
            chat_row = conn.execute(
                """
                SELECT provider, model, reasoning_level, web_search_enabled
                FROM default_text_generation_settings
                WHERE id = 1
                """
            ).fetchone()
            tts_row = conn.execute(
                """
                SELECT provider, model, voice_id
                FROM default_tts_generation_settings
                WHERE id = 1
                """
            ).fetchone()
            image_row = conn.execute(
                """
                SELECT provider, model
                FROM default_image_generation_settings
                WHERE id = 1
                """
            ).fetchone()

        if chat_row is None:
            raise RuntimeError("Missing default text generation settings row")
        if tts_row is None:
            raise RuntimeError("Missing default TTS generation settings row")
        if image_row is None:
            raise RuntimeError("Missing default image generation settings row")

        return GenerationDefaults(
            chat=_chat_generation_settings_from_row(chat_row),
            tts=_tts_generation_settings_from_row(tts_row),
            image=_image_generation_settings_from_row(image_row),
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
        profile_name = self._get_profile_name()
        logger.debug(f"Smart fields DB: loading all fields for profile={profile_name}")

        with open_database() as conn:
            _ensure_generation_defaults_exist(conn)
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
                WHERE sf.profile_name = ?
                ORDER BY sf.note_type_id, sf.deck_id, sf.target_field_name
                """,
                (profile_name,),
            ).fetchall()
        return [self._smart_field_from_row(row) for row in rows]

    @republish_state
    def create_smart_field(self, smart_field: SmartFieldCreate) -> None:
        """Creates a Smart Field with a new UUID."""
        profile_name = self._get_profile_name()
        logger.debug(
            f"Smart fields DB: creating {smart_field.field_type} field "
            f"{profile_name}/{smart_field.note_type_id}/{smart_field.deck_id}/"
            f"{smart_field.target_field_name}"
        )
        with open_database() as conn:
            collision = conn.execute(
                """
                SELECT id FROM smart_fields
                WHERE profile_name = ?
                    AND note_type_id = ?
                    AND deck_id = ?
                    AND lower(target_field_name) = lower(?)
                """,
                (
                    profile_name,
                    smart_field.note_type_id,
                    int(smart_field.deck_id),
                    smart_field.target_field_name,
                ),
            ).fetchone()
            if collision is not None:
                raise ValueError(SMART_FIELD_TARGET_COLLISION_ERROR)

            self._validate_no_cycle(smart_field)

            try:
                smart_field_id = self._insert_smart_field(
                    conn, smart_field, profile_name
                )
            except sqlite3.IntegrityError as e:
                raise ValueError(SMART_FIELD_TARGET_COLLISION_ERROR) from e
        logger.debug(f"Smart fields DB: created smart_field_id={smart_field_id}")

    @republish_state
    def update_smart_field(self, smart_field: SmartField) -> None:
        """Updates the profile-scoped Smart Field identified by its UUID."""
        profile_name = self._get_profile_name()
        logger.debug(
            f"Smart fields DB: updating smart_field_id={smart_field.id} "
            f"for profile={profile_name}"
        )
        with open_database() as conn:
            self._validate_no_cycle(smart_field, replaced_smart_field_id=smart_field.id)
            self._update_smart_field(conn, smart_field, profile_name)

    @republish_state
    def replace_all_smart_fields(
        self,
        smart_fields: list[SmartFieldCreate],
    ) -> None:
        profile_name = self._get_profile_name()
        logger.debug(
            f"Smart fields DB: replacing all fields for profile={profile_name} "
            f"with {len(smart_fields)} field(s)"
        )
        deduped_fields: dict[tuple[int, int, str], SmartFieldCreate] = {}
        for smart_field in smart_fields:
            deduped_fields[
                (
                    smart_field.note_type_id,
                    int(smart_field.deck_id),
                    smart_field.target_field_name.lower(),
                )
            ] = smart_field

        with open_database() as conn:
            conn.execute(
                "DELETE FROM smart_fields WHERE profile_name = ?", (profile_name,)
            )
            for smart_field in deduped_fields.values():
                self._insert_smart_field(conn, smart_field, profile_name)

    @republish_state
    def delete_smart_field(self, smart_field_id: str) -> None:
        profile_name = self._get_profile_name()
        logger.debug(
            f"Smart fields DB: removing smart_field_id={smart_field_id} "
            f"for profile={profile_name}"
        )
        with open_database() as conn:
            cursor = conn.execute(
                """
                DELETE FROM smart_fields
                WHERE id = ? AND profile_name = ?
                """,
                (smart_field_id, profile_name),
            )
            if cursor.rowcount != 1:
                raise ValueError(f"Smart Field not found: {smart_field_id}")

    def _update_smart_field(
        self,
        conn: sqlite3.Connection,
        smart_field: SmartField,
        profile_name: str,
    ) -> None:
        collision = conn.execute(
            """
            SELECT id FROM smart_fields
            WHERE profile_name = ?
                AND note_type_id = ?
                AND deck_id = ?
                AND lower(target_field_name) = lower(?)
                AND id != ?
            """,
            (
                profile_name,
                smart_field.note_type_id,
                int(smart_field.deck_id),
                smart_field.target_field_name,
                smart_field.id,
            ),
        ).fetchone()
        if collision is not None:
            raise ValueError(SMART_FIELD_TARGET_COLLISION_ERROR)

        try:
            cursor = conn.execute(
                """
                UPDATE smart_fields
                SET note_type_id = ?, deck_id = ?, target_field_name = ?,
                    field_type = ?, enabled = ?, updated_at = ?
                WHERE id = ? AND profile_name = ?
                """,
                (
                    smart_field.note_type_id,
                    int(smart_field.deck_id),
                    smart_field.target_field_name,
                    smart_field.field_type,
                    int(smart_field.enabled),
                    _utc_now_iso(),
                    smart_field.id,
                    profile_name,
                ),
            )
        except sqlite3.IntegrityError as e:
            raise ValueError(SMART_FIELD_TARGET_COLLISION_ERROR) from e
        if cursor.rowcount != 1:
            raise ValueError(f"Smart Field not found: {smart_field.id}")

        self._delete_settings(conn, smart_field.id)
        self._insert_settings(conn, smart_field.id, smart_field.settings)

    def _validate_no_cycle(
        self,
        smart_field: Union[SmartField, SmartFieldCreate],
        replaced_smart_field_id: Optional[str] = None,
    ) -> None:
        existing_fields = self.get_all_smart_fields()
        replaced_smart_field = next(
            (field for field in existing_fields if field.id == replaced_smart_field_id),
            None,
        )

        if replaced_smart_field_id and replaced_smart_field is None:
            return

        new_effective_fields = self._get_prospective_effective_fields(
            existing_fields,
            smart_field.note_type_id,
            smart_field.deck_id,
            replaced_smart_field_id,
            smart_field,
        )
        self._raise_for_cycle(new_effective_fields)

        if (
            replaced_smart_field is None
            or replaced_smart_field.deck_id == GLOBAL_DECK_ID
            or (
                replaced_smart_field.note_type_id == smart_field.note_type_id
                and replaced_smart_field.deck_id == smart_field.deck_id
            )
        ):
            return

        old_effective_fields = self._get_prospective_effective_fields(
            existing_fields,
            replaced_smart_field.note_type_id,
            replaced_smart_field.deck_id,
            replaced_smart_field_id,
        )
        self._raise_for_cycle(old_effective_fields)

    def _get_prospective_effective_fields(
        self,
        existing_fields: list[SmartField],
        note_type_id: int,
        deck_id: DeckId,
        replaced_smart_field_id: Optional[str],
        mutation: Optional[Union[SmartField, SmartFieldCreate]] = None,
    ) -> dict[str, Union[SmartField, SmartFieldCreate]]:
        global_fields: dict[str, Union[SmartField, SmartFieldCreate]] = {}
        deck_fields: dict[str, Union[SmartField, SmartFieldCreate]] = {}
        for existing_field in existing_fields:
            if existing_field.id == replaced_smart_field_id:
                continue
            if existing_field.note_type_id != note_type_id:
                continue

            field_key = existing_field.target_field_name.lower()
            if existing_field.deck_id == GLOBAL_DECK_ID:
                global_fields[field_key] = existing_field
            elif existing_field.deck_id == deck_id:
                deck_fields[field_key] = existing_field

        effective_fields = dict(global_fields)
        if deck_id != GLOBAL_DECK_ID:
            effective_fields.update(deck_fields)
        if mutation is not None:
            effective_fields[mutation.target_field_name.lower()] = mutation
        return effective_fields

    def _raise_for_cycle(
        self,
        effective_fields: dict[str, Union[SmartField, SmartFieldCreate]],
    ) -> None:
        dependencies: dict[str, list[str]] = {}
        for target_field, effective_field in effective_fields.items():
            settings = effective_field.settings
            if isinstance(settings, TTSSmartFieldSettings):
                input_fields = [settings.source_field_name.lower()]
            else:
                input_fields = get_prompt_fields(settings.prompt_text)
            dependencies[target_field] = [
                input_field
                for input_field in input_fields
                if input_field in effective_fields
            ]

        if _has_cycle(dependencies):
            raise ValueError(SMART_FIELD_CYCLE_ERROR)

    def _insert_smart_field(
        self,
        conn: sqlite3.Connection,
        smart_field: SmartFieldCreate,
        profile_name: str,
    ) -> str:
        smart_field_id = str(uuid4())
        now = _utc_now_iso()
        conn.execute(
            """
            INSERT INTO smart_fields (
                id, profile_name, note_type_id, deck_id, target_field_name, field_type,
                enabled, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                smart_field_id,
                profile_name,
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


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _has_cycle(dependencies: dict[str, list[str]]) -> bool:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(field: str) -> bool:
        if field in visiting:
            return True
        if field in visited:
            return False

        visiting.add(field)
        if any(visit(dependency) for dependency in dependencies[field]):
            return True
        visiting.remove(field)
        visited.add(field)
        return False

    return any(visit(field) for field in dependencies)


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


def _ensure_generation_defaults_exist(conn: sqlite3.Connection) -> None:
    row = conn.execute(
        """
        SELECT
            EXISTS(SELECT 1 FROM default_text_generation_settings WHERE id = 1)
                AS text_defaults_exist,
            EXISTS(SELECT 1 FROM default_tts_generation_settings WHERE id = 1)
                AS tts_defaults_exist,
            EXISTS(SELECT 1 FROM default_image_generation_settings WHERE id = 1)
                AS image_defaults_exist
        """
    ).fetchone()

    if not row["text_defaults_exist"]:
        raise RuntimeError("Missing default text generation settings row")
    if not row["tts_defaults_exist"]:
        raise RuntimeError("Missing default TTS generation settings row")
    if not row["image_defaults_exist"]:
        raise RuntimeError("Missing default image generation settings row")


smart_field_service = SmartFieldService()
