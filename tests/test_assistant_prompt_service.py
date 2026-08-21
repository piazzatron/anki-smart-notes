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
from src.services.assistant_prompt_service import (
    STARTER_PROMPT_LABEL,
    AssistantPrompt,
    AssistantPromptService,
)

TEST_PROFILE = "__test__"


def prompt_service_for_profile(
    profile_name: str = TEST_PROFILE,
) -> AssistantPromptService:
    return AssistantPromptService(get_profile_name=lambda: profile_name)


@pytest.fixture(autouse=True)
def sqlite_database(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import src.database.connection

    monkeypatch.setattr(
        src.database.connection,
        "get_database_path",
        lambda: str(tmp_path / "smart_notes.sqlite3"),
    )
    apply_database_migrations()


def test_seeds_the_starter_prompt_for_a_new_profile() -> None:
    prompts = prompt_service_for_profile().get_assistant_prompts()

    assert [prompt.label for prompt in prompts] == [STARTER_PROMPT_LABEL]


def test_does_not_reseed_a_profile_whose_prompts_were_all_deleted() -> None:
    service = prompt_service_for_profile()
    service.get_assistant_prompts()

    service.save_assistant_prompts([])

    assert service.get_assistant_prompts() == []


def test_save_replaces_the_list_and_keeps_its_order() -> None:
    service = prompt_service_for_profile()

    service.save_assistant_prompts(
        [
            AssistantPrompt(id="b", label="Mnemonic", prompt="Give me a mnemonic."),
            AssistantPrompt(id="a", label="Simpler", prompt="Say that more simply."),
        ]
    )

    assert [
        (prompt.id, prompt.label) for prompt in service.get_assistant_prompts()
    ] == [
        ("b", "Mnemonic"),
        ("a", "Simpler"),
    ]


def test_prompts_are_scoped_to_the_open_profile() -> None:
    prompt_service_for_profile("first").save_assistant_prompts(
        [AssistantPrompt(id="a", label="Only mine", prompt="Mine.")]
    )

    other = prompt_service_for_profile("second").get_assistant_prompts()

    assert [prompt.label for prompt in other] == [STARTER_PROMPT_LABEL]
