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
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import cast

from aqt import mw

from . import config as config_module
from .config import config
from .database import get_user_files_path
from .logger import logger
from .models import PromptMap
from .smart_field_prompt_map import replace_from_prompt_map
from .ui.ui_utils import show_message_box

CONFIG_KEYS_TO_REMOVE_AFTER_IMPORT = [
    "prompts_map",
    "did_deck_filter_migration",
    "did_cleanup_config_defaults",
]
LEGACY_CHAT_MODELS_TO_AUTO = {"deepseek-v3", "gpt-4o-mini", "gpt-5-nano"}


def migrate_legacy_smart_field_config() -> None:
    if config.did_migrate_smart_fields_to_sqlite:
        logger.debug("Smart fields DB migration: already completed")
        return

    try:
        logger.info("Smart fields DB migration: starting legacy config import")
        backup_config_for_sqlite_migration()
        legacy_prompt_map = deepcopy(
            cast(
                PromptMap,
                config.__getattr__("prompts_map") or {"note_types": {}},
            )
        )
        logger.debug(
            "Smart fields DB migration: importing "
            f"{len(legacy_prompt_map.get('note_types', {}))} note types"
        )
        replace_from_prompt_map(legacy_prompt_map)
        finish_legacy_config_migration()
        logger.info("Smart fields DB migration: completed")
    except Exception as e:
        logger.error(f"Smart fields DB migration failed: {e}", exc_info=True)
        try:
            from .sentry import sentry

            if sentry:
                sentry.capture_exception(e)
        except Exception as sentry_error:
            logger.error(
                f"Smart fields DB migration: failed to notify Sentry: {sentry_error}"
            )

        show_message_box(
            "Smart Notes could not finish upgrading your Smart Fields.",
            "Please email support@smart-notes.xyz and include your smart-notes.log file.",
        )
        raise


def migrate_legacy_chat_config_to_auto() -> None:
    if not mw:
        return
    addon_config = mw.addonManager.getConfig(config_module.__name__)
    if addon_config is None:
        return

    if (
        addon_config.get("chat_provider") != "deepseek"
        and addon_config.get("chat_model") not in LEGACY_CHAT_MODELS_TO_AUTO
    ):
        return

    logger.info("Migrating legacy chat config to Auto")
    addon_config["chat_provider"] = "auto"
    addon_config["chat_model"] = "auto"
    mw.addonManager.writeConfig(config_module.__name__, addon_config)


def backup_config_for_sqlite_migration() -> None:
    if not mw:
        raise RuntimeError("Cannot backup config because mw is unavailable")
    addon_config = mw.addonManager.getConfig(config_module.__name__)
    if addon_config is None:
        raise RuntimeError("Cannot backup config because addon config is missing")

    backup_path = Path(
        get_user_files_path(
            "config_backup_before_sqlite_"
            f"{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
        )
    )
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    backup_path.write_text(json.dumps(addon_config, indent=2), encoding="utf-8")
    logger.info(f"Smart fields DB migration: backed up config to {backup_path}")


def finish_legacy_config_migration() -> None:
    if not mw:
        raise RuntimeError("Cannot cleanup config because mw is unavailable")
    addon_config = mw.addonManager.getConfig(config_module.__name__)
    if addon_config is None:
        raise RuntimeError("Cannot cleanup config because addon config is missing")

    for key in CONFIG_KEYS_TO_REMOVE_AFTER_IMPORT:
        if key in addon_config:
            logger.debug(f"Smart fields DB migration: removing config key {key}")
            addon_config.pop(key)
    addon_config["did_migrate_smart_fields_to_sqlite"] = True
    mw.addonManager.writeConfig(config_module.__name__, addon_config)
