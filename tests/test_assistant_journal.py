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

os.environ["IS_TEST"] = "True"

from src.services.assistant_journal import AssistantJournal  # noqa: E402
from src.web.dto import AssistantRecordDto  # noqa: E402


def _record(session_id: str, text: str) -> AssistantRecordDto:
    return AssistantRecordDto(
        sessionId=session_id,
        cardId=1,
        deckId=2,
        noteTypeId=3,
        seq=0,
        message={"role": "user", "content": text},
    )


def test_append_assigns_increasing_sequence_numbers() -> None:
    journal = AssistantJournal()

    first = journal.append(_record("a", "one"))
    second = journal.append(_record("a", "two"))

    assert (first["seq"], second["seq"]) == (0, 1)


def test_history_returns_whole_sessions_newest_first() -> None:
    journal = AssistantJournal()
    for session_id in ("a", "b", "c"):
        journal.append(_record(session_id, "question"))
        journal.append(_record(session_id, "answer"))

    page = journal.history(limit=2, cursor=None)

    # The two newest sessions, complete, in original order.
    assert [record["sessionId"] for record in page["records"]] == [
        "b",
        "b",
        "c",
        "c",
    ]
    assert page["nextCursor"] == 2


def test_history_pages_backwards_through_older_sessions() -> None:
    journal = AssistantJournal()
    for session_id in ("a", "b", "c"):
        journal.append(_record(session_id, "question"))

    first_page = journal.history(limit=2, cursor=None)
    older = journal.history(limit=2, cursor=first_page["nextCursor"])

    assert [record["sessionId"] for record in older["records"]] == ["a"]
    assert older["nextCursor"] is None


def test_history_of_an_empty_journal_has_no_cursor() -> None:
    assert AssistantJournal().history(limit=10, cursor=None) == {
        "records": [],
        "nextCursor": None,
    }
