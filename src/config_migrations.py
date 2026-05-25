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

from aqt import mw

from . import config as config_module
from .logger import logger

LEGACY_CHAT_MODELS_TO_AUTO = {"deepseek-v3", "gpt-4o-mini", "gpt-5-nano"}


def migrate_legacy_addon_config() -> None:
    # Database migrations only see Smart Fields already in SQLite. The add-on's
    # default chat provider/model still lives in Anki's config.json, so migrate
    # that separately from yoyo's DB-only migration package.
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
