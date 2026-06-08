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

import json
import sqlite3
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import cast
from uuid import uuid4

from aqt import mw

from .. import config as config_module
from ..config import config
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
    PromptMap,
    TTSGenerationSettings,
    TTSModels,
    TTSProviders,
)
from ..models.smart_fields import (
    ChatSmartFieldSettings,
    SmartFieldCreate,
    SmartFieldSettings,
    TTSSmartFieldSettings,
)
from ..smart_field_prompt_map_conversion import smart_field_creates_from_prompt_map
from ..ui.ui_utils import show_message_box
from .connection import get_user_files_path, open_database

GENERATION_DEFAULT_CONFIG_KEYS = (
    "chat_provider",
    "chat_model",
    "chat_reasoning_level",
    "chat_web_search",
    "tts_provider",
    "tts_voice",
    "tts_model",
    "image_provider",
    "image_model",
)

CONFIG_KEYS_TO_REMOVE_AFTER_IMPORT = [
    "prompts_map",
    *GENERATION_DEFAULT_CONFIG_KEYS,
    "did_deck_filter_migration",
    "did_cleanup_config_defaults",
]

LEGACY_DEFAULT_TEXT_GENERATION_SETTINGS = ChatGenerationSettings(
    provider="auto",
    model="auto",
    reasoning_level="off",
    web_search_enabled=False,
)
LEGACY_DEFAULT_TTS_GENERATION_SETTINGS = TTSGenerationSettings(
    provider="google",
    model="standard",
    voice_id="en-US-Casual-K",
)
LEGACY_DEFAULT_IMAGE_GENERATION_SETTINGS = ImageGenerationSettings(
    provider="openai",
    model="gpt-image-1.5-low",
)


def migrate_legacy_config_to_database() -> None:
    if config.did_migrate_smart_fields_to_sqlite:
        logger.debug("Legacy config DB migration: already completed")
        return

    try:
        logger.info("Legacy config DB migration: starting legacy config import")
        addon_config = _get_addon_config()
        _assert_database_is_at_bootstrap_for_legacy_import()

        # Preserve the pre-migration config before any import or cleanup mutates it.
        _backup_config_for_sqlite_migration(addon_config)

        # Import generation defaults first so inherited Smart Field rows saved
        # below point at the current SQL default rows.
        generation_defaults = _migrate_legacy_generation_defaults_config(addon_config)

        # Snapshot the legacy prompt map before the final cleanup removes it
        # from config.json.
        legacy_prompt_map = deepcopy(
            cast(
                PromptMap,
                addon_config.get("prompts_map") or {"note_types": {}},
            )
        )
        logger.debug(
            "Legacy config DB migration: importing "
            f"{len(legacy_prompt_map.get('note_types', {}))} note types"
        )

        # The bootstrap schema is present, and later SQL migrations will evolve
        # these imported rows with the rest of the database.
        _migrate_legacy_prompt_map(legacy_prompt_map, generation_defaults)

        # Delete legacy config keys only after both SQL imports have succeeded.
        _finish_legacy_config_migration(addon_config)
        logger.info("Legacy config DB migration: completed")
    except Exception as e:
        logger.error(f"Legacy config DB migration failed: {e}", exc_info=True)
        try:
            from ..sentry import sentry

            if sentry:
                sentry.capture_exception(e)
        except Exception as sentry_error:
            logger.error(
                f"Legacy config DB migration: failed to notify Sentry: {sentry_error}"
            )

        show_message_box(
            "Smart Notes could not finish upgrading your Smart Fields.",
            "Please email support@smart-notes.xyz and include your smart-notes.log file.",
        )
        raise


def _get_addon_config() -> dict[str, object]:
    if not mw:
        raise RuntimeError("Cannot migrate config because mw is unavailable")
    addon_config = mw.addonManager.getConfig(config_module.__name__)
    if addon_config is None:
        raise RuntimeError("Cannot migrate config because addon config is missing")
    return addon_config


def _backup_config_for_sqlite_migration(addon_config: dict[str, object]) -> None:
    if not mw:
        raise RuntimeError("Cannot backup config because mw is unavailable")

    backup_path = Path(
        get_user_files_path(
            "config_backup_before_sqlite_"
            f"{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
        )
    )
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    backup_path.write_text(json.dumps(addon_config, indent=2), encoding="utf-8")
    logger.info(f"Legacy config DB migration: backed up config to {backup_path}")


def _migrate_legacy_generation_defaults_config(
    addon_config: dict[str, object],
) -> GenerationDefaults:
    # Global generation defaults used to live in config.json while Smart Fields
    # lived in prompts_map. Import the defaults into SQL before importing fields
    # so any non-custom field rows can point at these rows immediately.
    logger.info("Legacy config DB migration: importing generation defaults")
    chat_reasoning_level = addon_config.get("chat_reasoning_level")
    if chat_reasoning_level not in {"off", "low", "high"}:
        chat_reasoning_level = LEGACY_DEFAULT_TEXT_GENERATION_SETTINGS.reasoning_level

    generation_defaults = GenerationDefaults(
        chat=ChatGenerationSettings(
            provider=cast(
                ChatProviders,
                addon_config.get("chat_provider")
                or LEGACY_DEFAULT_TEXT_GENERATION_SETTINGS.provider,
            ),
            model=cast(
                ChatModels,
                addon_config.get("chat_model")
                or LEGACY_DEFAULT_TEXT_GENERATION_SETTINGS.model,
            ),
            reasoning_level=cast(ChatReasoningLevel, chat_reasoning_level),
            web_search_enabled=bool(
                addon_config.get("chat_web_search")
                if addon_config.get("chat_web_search") is not None
                else LEGACY_DEFAULT_TEXT_GENERATION_SETTINGS.web_search_enabled
            ),
        ),
        tts=TTSGenerationSettings(
            provider=cast(
                TTSProviders,
                addon_config.get("tts_provider")
                or LEGACY_DEFAULT_TTS_GENERATION_SETTINGS.provider,
            ),
            model=cast(
                TTSModels,
                addon_config.get("tts_model")
                or LEGACY_DEFAULT_TTS_GENERATION_SETTINGS.model,
            ),
            voice_id=str(
                addon_config.get("tts_voice")
                or LEGACY_DEFAULT_TTS_GENERATION_SETTINGS.voice_id
            ),
        ),
        image=ImageGenerationSettings(
            provider=cast(
                ImageProviders,
                addon_config.get("image_provider")
                or LEGACY_DEFAULT_IMAGE_GENERATION_SETTINGS.provider,
            ),
            model=cast(
                ImageModels,
                addon_config.get("image_model")
                or LEGACY_DEFAULT_IMAGE_GENERATION_SETTINGS.model,
            ),
        ),
    )

    with open_database() as conn:
        _upsert_legacy_chat_generation_defaults(conn, generation_defaults.chat)
        _upsert_legacy_tts_generation_defaults(conn, generation_defaults.tts)
        _upsert_legacy_image_generation_defaults(conn, generation_defaults.image)

    return generation_defaults


def _migrate_legacy_prompt_map(
    prompt_map: PromptMap, generation_defaults: GenerationDefaults
) -> None:
    smart_fields = smart_field_creates_from_prompt_map(prompt_map, generation_defaults)

    with open_database() as conn:
        # Re-run safety: a failed prior attempt may have inserted rows before
        # config cleanup marked the legacy migration complete.
        _upsert_bootstrap_smart_fields(conn, smart_fields)


def _finish_legacy_config_migration(addon_config: dict[str, object]) -> None:
    if not mw:
        raise RuntimeError("Cannot cleanup config because mw is unavailable")

    for key in CONFIG_KEYS_TO_REMOVE_AFTER_IMPORT:
        if key in addon_config:
            logger.debug(f"Legacy config DB migration: removing config key {key}")
            addon_config.pop(key)
    addon_config["did_migrate_smart_fields_to_sqlite"] = True
    mw.addonManager.writeConfig(config_module.__name__, addon_config)


def _assert_database_is_at_bootstrap_for_legacy_import() -> None:
    with open_database() as conn:
        try:
            rows = conn.execute("SELECT migration_id FROM _yoyo_migration").fetchall()
        except sqlite3.OperationalError as error:
            raise RuntimeError(
                "Cannot import legacy Smart Fields because the SQLite bootstrap "
                "migration has not run"
            ) from error

    applied_migrations = {str(row["migration_id"]) for row in rows}
    if "0001_initial_smart_fields_schema" not in applied_migrations:
        raise RuntimeError(
            "Cannot import legacy Smart Fields because the SQLite bootstrap "
            "migration has not run"
        )

    later_migrations = sorted(
        migration_id
        for migration_id in applied_migrations
        if migration_id != "0001_initial_smart_fields_schema"
    )
    if later_migrations:
        raise RuntimeError(
            "Cannot import legacy Smart Fields because SQL data migrations have "
            "already run before legacy config import: " + ", ".join(later_migrations)
        )


def _upsert_legacy_chat_generation_defaults(
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


def _upsert_legacy_tts_generation_defaults(
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


def _upsert_legacy_image_generation_defaults(
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


def _upsert_bootstrap_smart_fields(
    conn: sqlite3.Connection, smart_fields: list[SmartFieldCreate]
) -> None:
    deduped_fields: dict[tuple[int, int, str], SmartFieldCreate] = {}
    for smart_field in smart_fields:
        deduped_fields[
            (
                smart_field.note_type_id,
                int(smart_field.deck_id),
                smart_field.target_field_name.lower(),
            )
        ] = smart_field

    for smart_field in deduped_fields.values():
        conn.execute(
            """
            DELETE FROM smart_fields
            WHERE note_type_id = ?
                AND deck_id = ?
                AND lower(target_field_name) = lower(?)
            """,
            (
                smart_field.note_type_id,
                int(smart_field.deck_id),
                smart_field.target_field_name,
            ),
        )
        _insert_bootstrap_smart_field(conn, smart_field)


def _insert_bootstrap_smart_field(
    conn: sqlite3.Connection, smart_field: SmartFieldCreate
) -> None:
    smart_field_id = str(uuid4())
    now = datetime.now(timezone.utc).isoformat()
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
    _insert_bootstrap_smart_field_settings(conn, smart_field_id, smart_field.settings)


def _insert_bootstrap_smart_field_settings(
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
