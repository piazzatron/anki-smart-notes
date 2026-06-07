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
    DEFAULT_IMAGE_GENERATION_SETTINGS,
    DEFAULT_TEXT_GENERATION_SETTINGS,
    DEFAULT_TTS_GENERATION_SETTINGS,
    ChatGenerationSettings,
    ChatModels,
    ChatProviders,
    ChatReasoningLevel,
    GenerationDefaults,
    ImageGenerationSettings,
    ImageModels,
    ImageProviders,
    PromptMap,
    SmartFieldCreate,
    TTSGenerationSettings,
    TTSModels,
    TTSProviders,
)
from ..smart_field_prompt_map_conversion import smart_field_creates_from_prompt_map
from ..ui.ui_utils import show_message_box
from . import connection
from .connection import get_user_files_path
from .smart_field_persistence import (
    insert_smart_field_settings,
    upsert_chat_generation_defaults,
    upsert_image_generation_defaults,
    upsert_tts_generation_defaults,
)

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


def migrate_legacy_config_to_database() -> None:
    if config.did_migrate_smart_fields_to_sqlite:
        logger.debug("Legacy config DB migration: already completed")
        return

    try:
        logger.info("Legacy config DB migration: starting legacy config import")
        addon_config = _get_addon_config()

        # Preserve the pre-migration config before any import or cleanup mutates it.
        _backup_config_for_sqlite_migration(addon_config)

        # Import generation defaults first so inherited Smart Field rows can
        # point at SQL default rows as soon as they are created.
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

        # Import Smart Fields after generation defaults so fields using default
        # settings inherit from the SQL rows instead of config.json.
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
    # so any non-custom field rows can point at these rows immediately. Model
    # data migrations run after both imports, so later model backfills update the
    # default row first and inherited fields automatically see the new value.
    logger.info("Legacy config DB migration: importing generation defaults")
    chat_reasoning_level = addon_config.get("chat_reasoning_level")
    if chat_reasoning_level not in {"off", "low", "high"}:
        chat_reasoning_level = DEFAULT_TEXT_GENERATION_SETTINGS.reasoning_level

    generation_defaults = GenerationDefaults(
        chat=ChatGenerationSettings(
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
            reasoning_level=cast(ChatReasoningLevel, chat_reasoning_level),
            web_search_enabled=bool(
                addon_config.get("chat_web_search")
                if addon_config.get("chat_web_search") is not None
                else DEFAULT_TEXT_GENERATION_SETTINGS.web_search_enabled
            ),
        ),
        tts=TTSGenerationSettings(
            provider=cast(
                TTSProviders,
                addon_config.get("tts_provider")
                or DEFAULT_TTS_GENERATION_SETTINGS.provider,
            ),
            model=cast(
                TTSModels,
                addon_config.get("tts_model") or DEFAULT_TTS_GENERATION_SETTINGS.model,
            ),
            voice_id=str(
                addon_config.get("tts_voice")
                or DEFAULT_TTS_GENERATION_SETTINGS.voice_id
            ),
        ),
        image=ImageGenerationSettings(
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
        ),
    )

    with connection.open_database() as conn:
        upsert_chat_generation_defaults(conn, generation_defaults.chat)
        upsert_tts_generation_defaults(conn, generation_defaults.tts)
        upsert_image_generation_defaults(conn, generation_defaults.image)

    return generation_defaults


def _migrate_legacy_prompt_map(
    prompt_map: PromptMap, generation_defaults: GenerationDefaults
) -> None:
    smart_fields = smart_field_creates_from_prompt_map(prompt_map, generation_defaults)

    with connection.open_database() as conn:
        conn.execute("DELETE FROM smart_fields")
        for smart_field in smart_fields:
            _insert_legacy_smart_field(conn, smart_field)


def _insert_legacy_smart_field(
    conn: sqlite3.Connection, smart_field: SmartFieldCreate
) -> None:
    smart_field_id = str(uuid4())
    now = datetime.now(timezone.utc).isoformat()
    # The legacy import runs against the bootstrap schema, before the
    # profile_name column exists. Later SQL migrations add and backfill it.
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
    insert_smart_field_settings(conn, smart_field_id, smart_field.settings)


def _finish_legacy_config_migration(addon_config: dict[str, object]) -> None:
    if not mw:
        raise RuntimeError("Cannot cleanup config because mw is unavailable")

    for key in CONFIG_KEYS_TO_REMOVE_AFTER_IMPORT:
        if key in addon_config:
            logger.debug(f"Legacy config DB migration: removing config key {key}")
            addon_config.pop(key)
    addon_config["did_migrate_smart_fields_to_sqlite"] = True
    mw.addonManager.writeConfig(config_module.__name__, addon_config)
