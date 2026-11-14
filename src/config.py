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

import uuid
from typing import Any, Optional

from aqt import addons, mw

from .utils import USES_BEFORE_RATE_DIALOG


class Config:
    """Fancy config class that uses the Anki addon manager to store config values."""

    openai_api_key: Optional[str]
    generate_at_review: bool
    generate_on_add: bool
    times_used: int
    last_seen_version: Optional[str]
    openai_endpoint: Optional[str]
    allow_empty_fields: bool
    last_message_id: int
    debug: bool
    language: str
    auth_token: Optional[str]
    install_id: Optional[str]
    legacy_support: Optional[bool]
    did_dismiss_review_prompt: bool
    did_dismiss_discord_prompt: bool
    did_see_free_plan_welcome: bool
    did_see_generated_prompt_tip: bool
    # The prompt mode new text and image fields open in: the one last saved with.
    # None until set (see build_settings).
    prefers_writing_prompts: Optional[bool]

    # Dialogs / Migrations
    did_show_chained_error_dialog: bool
    did_show_rate_dialog: bool
    did_show_premium_tts_dialog: bool
    did_click_rate_link: bool
    did_migrate_smart_fields_to_sqlite: bool

    # Deprecated fields:
    legacy_openai_model: str

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


def get_install_id() -> str:
    """A random ID for this Anki install, created on first use and kept for the
    install's lifetime. The server sends it to Amplitude as the device ID, which
    ties a signed-out install's events to the account it later signs in to."""
    if not config.install_id:
        config.install_id = str(uuid.uuid4())
    return config.install_id


def bump_usage_counter() -> None:
    from .app_state import app_state

    config.times_used += 1
    if (
        config.times_used > USES_BEFORE_RATE_DIALOG
        and not config.did_show_rate_dialog
        and app_state.state["status"] == "AUTHENTICATED"
    ):
        from .ui.rate_dialog import RateDialog

        config.did_show_rate_dialog = True
        dialog = RateDialog()
        dialog.exec()
