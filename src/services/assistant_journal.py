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

import threading

from ..web.dto import AssistantHistoryDto, AssistantRecordDto


class AssistantJournal:
    """Append-only transcript of assistant chat sessions.

    Records are held in memory only: they survive closing and reopening the
    assistant window and die with Anki, which is the v0.1 persistence scope.
    A SQLite store replaces this behind the same two operations later.

    Records are stored oldest-first and read newest-session-first, so the web
    UI can page backwards through earlier sessions as the user scrolls up.
    """

    def __init__(self) -> None:
        # The server's asyncio thread appends while the main thread may read.
        self._lock = threading.Lock()
        self._records: list[AssistantRecordDto] = []

    def append(self, record: AssistantRecordDto) -> AssistantRecordDto:
        with self._lock:
            stored = AssistantRecordDto(
                sessionId=record["sessionId"],
                cardId=record["cardId"],
                deckId=record["deckId"],
                noteTypeId=record["noteTypeId"],
                seq=len(self._records),
                message=record["message"],
            )
            self._records.append(stored)
            return stored

    def history(self, limit: int, cursor: int | None) -> AssistantHistoryDto:
        """One page of sessions, newest first.

        Paging is by session rather than by record so a page never splits a
        conversation in half. `cursor` is the `seq` returned as `nextCursor` by
        the previous page; records at or after it are already loaded.
        """
        with self._lock:
            records = self._records

            unread = records if cursor is None else records[:cursor]
            if not unread:
                return AssistantHistoryDto(records=[], nextCursor=None)

            # Walk back from the newest record, collecting whole sessions.
            session_ids: list[str] = []
            start = len(unread)
            for index in range(len(unread) - 1, -1, -1):
                session_id = unread[index]["sessionId"]
                if session_id not in session_ids:
                    if len(session_ids) == limit:
                        break
                    session_ids.append(session_id)
                start = index

            return AssistantHistoryDto(
                records=list(unread[start:]),
                nextCursor=start if start > 0 else None,
            )

    def clear(self) -> None:
        with self._lock:
            self._records = []


assistant_journal = AssistantJournal()
