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

from pathlib import Path

import pytest

from src.database.migrations import apply_database_migrations
from src.services.assistant_settings_service import (
    AssistantSettings,
    AssistantSettingsService,
)

TEST_PROFILE = "__test__"


def settings_service_for_profile(
    profile_name: str = TEST_PROFILE,
) -> AssistantSettingsService:
    return AssistantSettingsService(get_profile_name=lambda: profile_name)


@pytest.fixture(autouse=True)
def sqlite_database(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import src.database.connection

    monkeypatch.setattr(
        src.database.connection,
        "get_database_path",
        lambda: str(tmp_path / "smart_notes.sqlite3"),
    )
    apply_database_migrations()


def test_defaults_to_matching_the_user_when_nothing_is_saved() -> None:
    settings = settings_service_for_profile().get_assistant_settings()

    assert settings.response_language == "auto"


def test_round_trips_a_saved_language() -> None:
    service = settings_service_for_profile()

    service.save_assistant_settings(AssistantSettings(response_language="ja"))

    assert service.get_assistant_settings().response_language == "ja"


def test_saving_twice_updates_the_profile_row() -> None:
    service = settings_service_for_profile()

    service.save_assistant_settings(AssistantSettings(response_language="ja"))
    service.save_assistant_settings(AssistantSettings(response_language="pt-BR"))

    assert service.get_assistant_settings().response_language == "pt-BR"


def test_settings_are_scoped_to_the_open_profile() -> None:
    settings_service_for_profile("first").save_assistant_settings(
        AssistantSettings(response_language="ja")
    )

    other = settings_service_for_profile("second").get_assistant_settings()

    assert other.response_language == "auto"
