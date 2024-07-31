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

from typing import Any, Dict, Literal, Optional, TypedDict, Union

from aqt import addons, mw

# TODO: these should be moved
OpenAIModels = Literal["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-4"]
AnthropicModels = Literal["claude-3-opus", "claude-3-haiku", "claude-3-5-sonnet"]
ChatModels = Union[OpenAIModels, AnthropicModels]
ChatProviders = Literal["openai", "anthropic"]


class FieldExtras(TypedDict):
    automatic: Optional[bool]
    chat_model: Optional[ChatModels]
    chat_provider: Optional[ChatProviders]


class NoteTypeMap(TypedDict):
    fields: Dict[str, str]
    extras: Union[Dict[str, FieldExtras], None]  # maps from field name -> extras


class PromptMap(TypedDict):
    note_types: Dict[str, NoteTypeMap]


class Config:
    """Fancy config class that uses the Anki addon manager to store config values."""

    openai_api_key: Union[str, None]
    prompts_map: PromptMap
    generate_at_review: bool
    times_used: int
    did_show_rate_dialog: bool
    last_seen_version: Union[str, None]
    uuid: Union[str, None]
    openai_endpoint: Union[str, None]
    regenerate_notes_when_batching: bool
    allow_empty_fields: bool
    last_message_id: int
    debug: bool
    chat_provider: ChatProviders
    chat_model: ChatModels
    auth_token: Union[str, None]

    # Deprecated fields:
    # openai_model: OpenAIModels

    def __init__(self):
        self._perform_cleanup()

    def _perform_cleanup(self) -> None:
        print("Cleaning up config")
        try:
            old_openai_model = self.__getattr__("openai_model")
            if old_openai_model:
                print(f"Migration: old_openai_model={old_openai_model}")
                self.chat_model = old_openai_model  # type: ignore
                self.__setattr__("openai_model", None)
        except Exception as e:
            print(f"Error: Unexepctedly caught exception cleaning up config {e}")

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


config = Config()  # type: ignore
