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

import uuid
from dataclasses import dataclass
from typing import TYPE_CHECKING

from .. import utils
from ..database.connection import open_database
from ..event_bus import republish_state

if TYPE_CHECKING:
    import sqlite3
    from collections.abc import Callable

STARTER_PROMPT_LABEL = "Explain this card"
STARTER_PROMPT_TEXT = "Explain this card to me."


@dataclass(frozen=True)
class AssistantPrompt:
    """One saved prompt, shown as a button in the chat."""

    id: str
    label: str
    prompt: str


class AssistantPromptService:
    """The chat's saved prompt buttons, scoped to the open Anki profile."""

    def __init__(self, get_profile_name: Callable[[], str] | None = None) -> None:
        self._get_profile_name = get_profile_name or utils.get_current_profile_name

    def get_assistant_prompts(self) -> list[AssistantPrompt]:
        profile_name = self._get_profile_name()

        with open_database() as conn:
            self._seed_profile_once(conn, profile_name)
            rows = conn.execute(
                """
                SELECT id, label, prompt_text
                FROM assistant_prompts
                WHERE profile_name = ?
                ORDER BY position
                """,
                (profile_name,),
            ).fetchall()

        return [
            AssistantPrompt(id=row["id"], label=row["label"], prompt=row["prompt_text"])
            for row in rows
        ]

    @republish_state
    def save_assistant_prompts(self, prompts: list[AssistantPrompt]) -> None:
        """Replace this profile's prompts. Order comes from the list itself."""
        profile_name = self._get_profile_name()

        with open_database() as conn:
            # The client always sends the whole list, so a rewrite is simpler
            # than reconciling rows, and nothing on a prompt outlives it.
            conn.execute(
                "DELETE FROM assistant_prompts WHERE profile_name = ?",
                (profile_name,),
            )
            conn.executemany(
                """
                INSERT INTO assistant_prompts (
                    id, profile_name, label, prompt_text, position
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (prompt.id, profile_name, prompt.label, prompt.prompt, position)
                    for position, prompt in enumerate(prompts)
                ],
            )
            self._mark_profile_seeded(conn, profile_name)

    def _seed_profile_once(self, conn: sqlite3.Connection, profile_name: str) -> None:
        if self._is_profile_seeded(conn, profile_name):
            return

        conn.execute(
            """
            INSERT INTO assistant_prompts (
                id, profile_name, label, prompt_text, position
            )
            VALUES (?, ?, ?, ?, 0)
            """,
            (
                str(uuid.uuid4()),
                profile_name,
                STARTER_PROMPT_LABEL,
                STARTER_PROMPT_TEXT,
            ),
        )
        self._mark_profile_seeded(conn, profile_name)

    def _is_profile_seeded(self, conn: sqlite3.Connection, profile_name: str) -> bool:
        return (
            conn.execute(
                "SELECT 1 FROM assistant_prompt_seeds WHERE profile_name = ?",
                (profile_name,),
            ).fetchone()
            is not None
        )

    def _mark_profile_seeded(self, conn: sqlite3.Connection, profile_name: str) -> None:
        conn.execute(
            "INSERT OR IGNORE INTO assistant_prompt_seeds (profile_name) VALUES (?)",
            (profile_name,),
        )


assistant_prompt_service = AssistantPromptService()
