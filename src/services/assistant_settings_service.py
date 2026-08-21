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

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .. import utils
from ..database.connection import open_database
from ..event_bus import republish_state

if TYPE_CHECKING:
    from collections.abc import Callable

AUTO_RESPONSE_LANGUAGE = "auto"


@dataclass(frozen=True)
class AssistantSettings:
    """How the chat assistant behaves, for one Anki profile."""

    response_language: str


DEFAULT_ASSISTANT_SETTINGS = AssistantSettings(response_language=AUTO_RESPONSE_LANGUAGE)


class AssistantSettingsService:
    """Assistant settings for the open profile, defaulting until one is set."""

    def __init__(self, get_profile_name: Callable[[], str] | None = None) -> None:
        self._get_profile_name = get_profile_name or utils.get_current_profile_name

    def get_assistant_settings(self) -> AssistantSettings:
        with open_database() as conn:
            row = conn.execute(
                """
                SELECT response_language
                FROM assistant_settings
                WHERE profile_name = ?
                """,
                (self._get_profile_name(),),
            ).fetchone()

        # A missing row is not missing data: it means nothing has been changed
        # from the defaults yet.
        if row is None:
            return DEFAULT_ASSISTANT_SETTINGS
        return AssistantSettings(response_language=row["response_language"])

    @republish_state
    def save_assistant_settings(self, settings: AssistantSettings) -> None:
        with open_database() as conn:
            conn.execute(
                """
                INSERT INTO assistant_settings (profile_name, response_language)
                VALUES (?, ?)
                ON CONFLICT(profile_name) DO UPDATE SET
                    response_language = excluded.response_language
                """,
                (self._get_profile_name(), settings.response_language),
            )


assistant_settings_service = AssistantSettingsService()
