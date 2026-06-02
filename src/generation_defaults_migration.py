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
from .services.generation_defaults_service import generation_defaults_service


def migrate_legacy_generation_defaults_config() -> None:
    if not mw:
        return
    addon_config = mw.addonManager.getConfig(config_module.__name__)
    if addon_config is None:
        return
    if addon_config.get("did_migrate_smart_fields_to_sqlite"):
        logger.debug("Generation defaults DB migration: already completed")
        return

    # Global generation defaults used to live in config.json while Smart Fields
    # lived in prompts_map. Import the defaults into SQL before importing fields
    # so any non-custom field rows can point at these rows immediately. Model
    # data migrations run after both imports, so later model backfills update the
    # default row first and inherited fields automatically see the new value.
    logger.info("Generation defaults DB migration: importing config defaults")
    generation_defaults_service.import_from_legacy_config(addon_config)
