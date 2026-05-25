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

from collections.abc import Mapping
from typing import Any, Optional, TypeVar, cast

from aqt import addons, mw

from .models import (
    ChatModels,
    ChatProviders,
    ImageModels,
    ImageProviders,
    OpenAIModels,
    TTSModels,
    TTSProviders,
)
from .utils import USES_BEFORE_RATE_DIALOG


class Config:
    """Fancy config class that uses the Anki addon manager to store config values."""

    openai_api_key: Optional[str]
    generate_at_review: bool
    times_used: int
    last_seen_version: Optional[str]
    openai_endpoint: Optional[str]
    regenerate_notes_when_batching: bool
    allow_empty_fields: bool
    last_message_id: int
    debug: bool
    auth_token: Optional[str]
    legacy_support: Optional[bool]

    # Chat
    chat_provider: ChatProviders
    chat_model: ChatModels
    chat_temperature: int
    chat_web_search: bool

    # TTS
    tts_provider: TTSProviders
    tts_voice: str
    tts_model: TTSModels

    # Images
    image_provider: ImageProviders
    image_model: ImageModels

    # Dialogs / Migrations
    did_show_chained_error_dialog: bool
    did_show_rate_dialog: bool
    did_show_premium_tts_dialog: bool
    did_click_rate_link: bool
    did_migrate_smart_fields_to_sqlite: bool

    # Capacity alerts
    did_show_capacity_threshold_this_cycle: bool

    # Deprecated fields:
    legacy_openai_model: OpenAIModels

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

    def _defaults(self) -> Optional[dict[str, Any]]:
        if not mw:
            return {}

        mgr = addons.AddonManager(mw)
        defaults = mgr.addonConfigDefaults("smart-notes")
        return defaults


config = Config()


def bump_usage_counter() -> None:
    from .app_state import app_state

    config.times_used += 1
    if (
        config.times_used > USES_BEFORE_RATE_DIALOG
        and not config.did_show_rate_dialog
        and app_state.is_free_trial()
    ):
        from .ui.rate_dialog import RateDialog

        config.did_show_rate_dialog = True
        dialog = RateDialog()
        dialog.exec()


T = TypeVar("T")
M = TypeVar("M", bound=Mapping[str, object])


# TODO: this belongs in utils but ciruclar import
def key_or_config_val(vals: Optional[M], k: str) -> T:  # type: ignore
    return (
        cast(T, vals[k])
        if (vals and vals.get(k) is not None)
        else cast(T, config.__getattr__(k))
    )
