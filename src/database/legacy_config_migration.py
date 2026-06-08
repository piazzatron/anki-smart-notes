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
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast
from uuid import uuid4

from anki.collection import Collection
from anki.decks import DeckId
from aqt import mw

from .. import config as config_module, utils
from ..config import config
from ..constants import GLOBAL_DECK_ID
from ..logger import logger
from ..models import (
    DEFAULT_EXTRAS,
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
from ..smart_field_prompt_map_conversion import smart_field_settings_from_prompt_parts
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


@dataclass(frozen=True)
class _ProfilePromptMapContext:
    """Lookup data for importing legacy note-type-name rows into one profile."""

    profile_name: str
    note_type_ids_by_name: dict[str, int]
    deck_ids: set[int]


@dataclass(frozen=True)
class _ProfileSmartField:
    profile_name: str
    smart_field: SmartFieldCreate


def migrate_legacy_config_to_database() -> None:
    if config.did_migrate_smart_fields_to_sqlite:
        logger.debug("Legacy config DB migration: already completed")
        return

    try:
        logger.info("Legacy config DB migration: starting legacy config import")
        addon_config = _get_addon_config()

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
    if not prompt_map["note_types"]:
        return

    # This import intentionally writes SQL directly instead of using
    # SmartFieldService or shared service write helpers. It is an upgrade
    # artifact that writes the bootstrap schema, while the service owns the final
    # runtime schema and replacement semantics. Keeping this SQL local lets
    # future runtime-service changes force explicit importer decisions without
    # making old-data porting depend on the service; this is also the only phase
    # that still has note type names and can preserve the old shared-by-name
    # behavior across profiles. A little duplicated SQL is preferable here to
    # coupling one-time old-data recovery to mutable runtime persistence code.
    smart_fields = _profile_smart_fields_from_legacy_prompt_map(
        prompt_map, generation_defaults, _get_profile_prompt_map_contexts()
    )

    with open_database() as conn:
        # Re-run safety: a failed prior attempt may have inserted rows before
        # config cleanup marked the legacy migration complete.
        _upsert_bootstrap_smart_fields(conn, smart_fields)


def _get_profile_prompt_map_contexts() -> list[_ProfilePromptMapContext]:
    if not mw or not mw.pm or not mw.col:
        raise RuntimeError(
            "Cannot migrate Smart Fields because Anki profile is unavailable"
        )

    # The prompt-map import still has note type names, so it can preserve the old
    # shared-by-name behavior. The SQL compatibility migration handles already
    # imported rows separately because those rows only have profile-local ids.
    current_profile = utils.get_current_profile_name()
    profile_names = [str(profile_name) for profile_name in mw.pm.profiles()]
    if current_profile not in profile_names:
        profile_names.append(current_profile)

    # Opening other profile collections can trigger Anki collection-level
    # housekeeping, but note type and deck ids are profile-local. The importer
    # cannot reconstruct the old shared-by-name prompt map without reading them.
    contexts: list[_ProfilePromptMapContext] = []
    for profile_name in profile_names:
        collection = mw.col
        close_after = False
        if profile_name != current_profile:
            collection_path = Path(str(mw.pm.base)) / profile_name / "collection.anki2"
            if not collection_path.exists():
                logger.warning(
                    "Legacy config DB migration: skipping profile="
                    f"{profile_name} because collection.anki2 does not exist"
                )
                continue

            try:
                collection = Collection(str(collection_path))
            except Exception:
                logger.warning(
                    "Legacy config DB migration: skipping profile="
                    f"{profile_name} because collection.anki2 could not be opened",
                    exc_info=True,
                )
                continue
            close_after = True

        try:
            contexts.append(_profile_prompt_map_context(profile_name, collection))
        except Exception:
            if profile_name == current_profile:
                raise
            logger.warning(
                "Legacy config DB migration: skipping profile="
                f"{profile_name} because collection metadata could not be read",
                exc_info=True,
            )
        finally:
            if close_after:
                collection.close()

    return contexts


def _profile_prompt_map_context(
    profile_name: str, collection: Any
) -> _ProfilePromptMapContext:
    note_type_ids_by_name = {
        str(model["name"]): int(model["id"]) for model in collection.models.all()
    }
    deck_ids = {int(deck["id"]) for deck in collection.decks.all()}
    return _ProfilePromptMapContext(
        profile_name=profile_name,
        note_type_ids_by_name=note_type_ids_by_name,
        deck_ids=deck_ids,
    )


def _profile_smart_fields_from_legacy_prompt_map(
    prompt_map: PromptMap,
    generation_defaults: GenerationDefaults,
    profile_contexts: list[_ProfilePromptMapContext],
) -> list[_ProfileSmartField]:
    smart_fields: list[_ProfileSmartField] = []
    for note_type, decks in prompt_map["note_types"].items():
        matching_contexts = [
            context
            for context in profile_contexts
            if note_type in context.note_type_ids_by_name
        ]
        if not matching_contexts:
            logger.warning(
                "Legacy config DB migration: skipping legacy smart fields for "
                f"note_type={note_type} because no Anki profile has that note type name"
            )
            continue

        for context in matching_contexts:
            note_type_id = context.note_type_ids_by_name[note_type]
            logger.info(
                "Legacy config DB migration: importing note_type="
                f"{note_type} into profile={context.profile_name} "
                f"as note_type_id={note_type_id}"
            )
            for deck_id_text, note_type_map in decks.items():
                deck_id = int(deck_id_text)
                if deck_id != int(GLOBAL_DECK_ID) and deck_id not in context.deck_ids:
                    logger.warning(
                        "Legacy config DB migration: skipping legacy smart fields "
                        f"for profile={context.profile_name}, note_type={note_type}, "
                        f"deck_id={deck_id} because the deck id does not exist in "
                        "that profile"
                    )
                    continue

                for field, prompt in note_type_map.get("fields", {}).items():
                    extras = (
                        note_type_map.get("extras", {}).get(field) or DEFAULT_EXTRAS
                    )
                    smart_fields.append(
                        _ProfileSmartField(
                            profile_name=context.profile_name,
                            smart_field=SmartFieldCreate(
                                note_type_id=note_type_id,
                                deck_id=cast(DeckId, deck_id),
                                target_field_name=field,
                                enabled=extras["automatic"],
                                settings=smart_field_settings_from_prompt_parts(
                                    prompt, extras, generation_defaults
                                ),
                            ),
                        )
                    )

    return smart_fields


def _finish_legacy_config_migration(addon_config: dict[str, object]) -> None:
    if not mw:
        raise RuntimeError("Cannot cleanup config because mw is unavailable")

    for key in CONFIG_KEYS_TO_REMOVE_AFTER_IMPORT:
        if key in addon_config:
            logger.debug(f"Legacy config DB migration: removing config key {key}")
            addon_config.pop(key)
    addon_config["did_migrate_smart_fields_to_sqlite"] = True
    mw.addonManager.writeConfig(config_module.__name__, addon_config)


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
    conn: sqlite3.Connection, smart_fields: list[_ProfileSmartField]
) -> None:
    deduped_fields: dict[tuple[str, int, int, str], _ProfileSmartField] = {}
    for profile_smart_field in smart_fields:
        smart_field = profile_smart_field.smart_field
        deduped_fields[
            (
                profile_smart_field.profile_name,
                smart_field.note_type_id,
                int(smart_field.deck_id),
                smart_field.target_field_name.lower(),
            )
        ] = profile_smart_field

    for profile_smart_field in deduped_fields.values():
        smart_field = profile_smart_field.smart_field
        conn.execute(
            """
            DELETE FROM smart_fields
            WHERE profile_name = ?
                AND note_type_id = ?
                AND deck_id = ?
                AND lower(target_field_name) = lower(?)
            """,
            (
                profile_smart_field.profile_name,
                smart_field.note_type_id,
                int(smart_field.deck_id),
                smart_field.target_field_name,
            ),
        )
        _insert_bootstrap_smart_field(conn, profile_smart_field)


def _insert_bootstrap_smart_field(
    conn: sqlite3.Connection, profile_smart_field: _ProfileSmartField
) -> None:
    smart_field = profile_smart_field.smart_field
    smart_field_id = str(uuid4())
    now = datetime.now(timezone.utc).isoformat()
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
            profile_smart_field.profile_name,
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
