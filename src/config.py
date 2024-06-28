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

from typing import Any, Dict, Literal, TypedDict, Union

from aqt import addons, mw


class NoteTypeMap(TypedDict):
    fields: Dict[str, str]


class PromptMap(TypedDict):
    note_types: Dict[str, NoteTypeMap]


OpenAIModels = Literal["gpt-3.5-turbo", "gpt-4o", "gpt-4-turbo", "gpt-4"]


class Config:
    """Fancy config class that uses the Anki addon manager to store config values."""

    openai_api_key: str
    prompts_map: PromptMap
    openai_model: OpenAIModels
    generate_at_review: bool
    times_used: int
    did_show_rate_dialog: bool
    last_seen_version: Union[str, None]
    uuid: Union[str, None]

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

    def get_prompt(self, note_type: str, field: str):
        return (
            self.prompts_map.get("note_types", {})
            .get(note_type, {"fields": {}})
            .get("fields", {})
            .get(field, None)
        )

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


config = Config()
