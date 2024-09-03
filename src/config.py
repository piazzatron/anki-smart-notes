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

import os
from typing import Any, Dict, Literal, Optional, TypedDict, Union

from aqt import addons, mw

from .models import ChatModels, ChatProviders, TTSModels, TTSProviders


class FieldExtras(TypedDict):
    """Should be only used internally by config"""

    automatic: Optional[bool]
    type: Optional[Literal["chat", "tts"]]
    use_custom_model: Optional[bool]
    # Chat
    chat_model: Optional[ChatModels]
    chat_provider: Optional[ChatProviders]
    chat_temperature: Optional[int]
    # TTS
    tts_provider: Optional[TTSProviders]
    tts_model: Optional[str]
    tts_voice: Optional[str]


class FieldExtrasWithDefaults(TypedDict):
    """This is the type returned by get_extras, that the actual app should deal with"""

    automatic: bool
    use_custom_model: bool
    type: Literal["chat", "tts"]
    # Chat
    chat_model: ChatModels
    chat_provider: ChatProviders
    chat_temperature: int

    # TTS
    tts_provider: TTSProviders
    tts_model: TTSModels
    tts_voice: str


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
    last_seen_version: Union[str, None]
    uuid: Union[str, None]
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

    # TTS
    tts_provider: TTSProviders
    tts_voice: str
    tts_model: TTSModels

    # Dialogs
    did_show_chained_error_dialog: bool
    did_show_rate_dialog: bool
    did_show_premium_tts_dialog: bool

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

            # If we've never set the legacy_support flag
            # set it to whether or not we have an openai key
            if self.__getattr__("legacy_support") is None:
                is_legacy = bool(self.openai_api_key)
                print(f"Setting legacy_support to {is_legacy}")
                self.__setattr__("legacy_support", is_legacy)
        except Exception as e:
            if not os.getenv("IS_TEST"):
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
