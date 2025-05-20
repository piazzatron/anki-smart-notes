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
import os
from copy import deepcopy
from typing import Any, Dict, Mapping, Optional, TypedDict, TypeVar, Union, cast

from aqt import addons, mw

from .constants import DEFAULT_TEMPERATURE, GLOBAL_DECK_ID
from .logger import logger
from .models import (
    DEFAULT_EXTRAS,
    ChatModels,
    ChatProviders,
    ImageModels,
    ImageProviders,
    NoteTypeMap,
    OpenAIModels,
    PromptMap,
    TTSModels,
    TTSProviders,
)
from .ui.rate_dialog import RateDialog
from .utils import USES_BEFORE_RATE_DIALOG, get_file_path


class Config:
    """Fancy config class that uses the Anki addon manager to store config values."""

    openai_api_key: Union[str, None]
    prompts_map: PromptMap
    generate_at_review: bool
    times_used: int
    last_seen_version: Union[str, None]
    uuid: str
    openai_endpoint: Union[str, None]
    regenerate_notes_when_batching: bool
    allow_empty_fields: bool
    last_message_id: int
    debug: bool
    auth_token: Union[str, None]
    legacy_support: Union[bool, None]

    # Chat
    chat_provider: ChatProviders
    chat_model: ChatModels
    chat_temperature: int
    chat_markdown_to_html: bool

    # TTS
    tts_provider: TTSProviders
    tts_voice: str
    tts_model: TTSModels
    tts_strip_html: bool

    # Images
    image_provider: ImageProviders
    image_model: ImageModels

    # Dialogs / Migrations
    did_show_chained_error_dialog: bool
    did_show_rate_dialog: bool
    did_show_premium_tts_dialog: bool
    did_deck_filter_migration: bool
    did_cleanup_config_defaults: bool
    did_click_rate_link: bool

    # Deprecated fields:
    legacy_openai_model: OpenAIModels

    def setup_config(self) -> None:
        try:
            self.migrate_models()
            self.perform_deck_filter_migration()
            self.perform_extras_cleanup()

        except Exception as e:
            if not os.getenv("IS_TEST"):
                logger.error(
                    f"Error: Unexepctedly caught exception cleaning up config {e}"
                )

    def __getattr__(self, key: str) -> object:
        if not mw:
            raise Exception("Error: mw not found")

        config = mw.addonManager.getConfig(__name__)
        if not config:
            return None
        return config.get(key)

    def __setattr__(self, name: str, value: object) -> None:
        if not mw:
            raise Exception("Error: mw not found")

        old_config = mw.addonManager.getConfig(__name__)
        if not old_config:
            raise Exception("Error: no config found")

        old_config[name] = value
        mw.addonManager.writeConfig(__name__, old_config)

    def restore_defaults(self) -> None:
        defaults = self._defaults()
        if not defaults:
            return

        for key, value in defaults.items():
            setattr(self, key, value)

    def _defaults(self) -> Union[Dict[str, Any], None]:
        if not mw:
            return {}

        mgr = addons.AddonManager(mw)
        defaults = mgr.addonConfigDefaults("smart-notes")
        return defaults

    # Migrations

    def migrate_models(self) -> None:
        migration_map = {"o1-mini": "o4-mini"}

        # Migrate base model
        for old_model, new_model in migration_map.items():
            if self.chat_model == old_model:
                logger.debug(f"Migration: {old_model} -> {new_model}")
                self.chat_model = new_model  # type: ignore

        # Migrate any custom models
        prompts_map = deepcopy(self.prompts_map)
        # Notes
        for _, decks in prompts_map["note_types"].items():
            # Decks
            for _, fields_and_extras in decks.items():
                # Fields
                for _, extras in fields_and_extras["extras"].items():
                    if extras.get("chat_model") and migration_map.get(
                        extras["chat_model"]  # type: ignore
                    ):
                        new_model = migration_map[extras["chat_model"]]  # type: ignore
                        logger.debug(
                            f"Custom prompt migration: {extras['chat_model']} -> {new_model}"
                        )
                        extras["chat_model"] = new_model  # type: ignore
        self.prompts_map = prompts_map

    def perform_deck_filter_migration(self) -> None:
        if self.did_deck_filter_migration:
            return

        self._backup_config()

        logger.debug("Migration: prompts map migration for per-deck prompts")
        old_prompts_map: OldPromptsMap = cast(OldPromptsMap, self.prompts_map)
        new_prompts_map: PromptMap = {"note_types": {}}

        for note_type, fields_and_extras in old_prompts_map["note_types"].items():
            new_prompts_map["note_types"][note_type] = {
                str(GLOBAL_DECK_ID): fields_and_extras.copy()
            }
        self.prompts_map = new_prompts_map

        self.did_deck_filter_migration = True

    def perform_extras_cleanup(self) -> None:
        """Add new extras"""
        if not self.did_cleanup_config_defaults:
            self.chat_temperature = DEFAULT_TEMPERATURE
            self.did_cleanup_config_defaults = True

        logger.debug("Migration: writing sane defaults for prompt extras")
        prompts_map = deepcopy(self.prompts_map)

        for decks_map in prompts_map["note_types"].values():
            for extras_and_fields in decks_map.values():
                # Theoretically extras might not exist at all. Make it
                if not extras_and_fields.get("extras"):
                    extras_and_fields["extras"] = {}

                # Make sure extras exists for every prompt field
                for field in extras_and_fields["fields"].keys():
                    if not extras_and_fields["extras"].get(field):
                        extras_and_fields["extras"][field] = {}  # type: ignore

                # Add all default fields
                for extras in extras_and_fields["extras"].values():
                    for k, v in DEFAULT_EXTRAS.items():
                        if not k in extras:
                            logger.debug(f"Adding extra {k}: {v}")
                            extras[k] = v  # type: ignore

        self.prompts_map = prompts_map

    def _backup_config(self) -> None:
        try:
            if not mw:
                return
            config = mw.addonManager.getConfig(__name__)
            if config:
                json_config = json.dumps(config)
                file_path = get_file_path("config_backup.json")
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(json_config)
        except Exception as e:
            logger.error(f"Could not backup config due to error: {e}")


class OldPromptsMap(TypedDict):
    note_types: Dict[str, NoteTypeMap]


config = Config()


def bump_usage_counter() -> None:
    config.times_used += 1
    if config.times_used > USES_BEFORE_RATE_DIALOG and not config.did_show_rate_dialog:
        config.did_show_rate_dialog = True
        dialog = RateDialog()
        dialog.exec()


T = TypeVar("T")
M = TypeVar("M", bound=Mapping[str, object])


# TODO: this belongs in utils but ciruclar import
# TODO: make this use the none_defaulting (too much type golf for now tho)
def key_or_config_val(vals: Optional[M], k: str) -> T:  # type: ignore
    return (
        cast(T, vals[k])
        if (vals and vals.get(k) is not None)
        else cast(T, config.__getattr__(k))
    )
