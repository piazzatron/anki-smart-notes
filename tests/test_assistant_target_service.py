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

from types import SimpleNamespace
from typing import Any, Callable, cast
from unittest.mock import MagicMock

import pytest
from aqt.editor import Editor, EditorMode

from src.services import assistant_target_service as target_module
from src.services.assistant_target_service import AssistantTargetService
from src.web import dto
from tests.fixtures import MockCard, MockNote


class ImmediateCollectionOp:
    def __init__(self, before_success: Callable[[], None] | None = None) -> None:
        self._before_success = before_success
        self._success: Callable[[object], None] | None = None

    def success(self, callback: Callable[[object], None]) -> ImmediateCollectionOp:
        self._success = callback
        return self

    def failure(self, _callback: Callable[[Exception], None]) -> ImmediateCollectionOp:
        return self

    def run_in_background(self) -> None:
        if self._before_success is not None:
            self._before_success()
        assert self._success is not None
        self._success(SimpleNamespace())


class FakeSignal:
    def connect(self, _callback: Callable[..., None]) -> None:
        pass


class FakeDecks:
    def all_names_and_ids(
        self, skip_empty_default: bool = False
    ) -> list[SimpleNamespace]:
        return [
            SimpleNamespace(name="Default", id=1),
            SimpleNamespace(name="Study", id=7),
        ]

    def name_if_exists(self, deck_id: int) -> str | None:
        return "Study" if deck_id == 7 else None


class AssistantMockNote(MockNote):
    def __init__(self, data: dict[str, Any], *, note_id: int) -> None:
        super().__init__(data, note_id=note_id)
        self.tags: list[str] = []
        self.generated_card_ids: list[int] = []

    def card_ids(self) -> list[int]:
        return self.generated_card_ids


class FakeEditor:
    def __init__(self, note: AssistantMockNote, mode: EditorMode) -> None:
        self.note = note
        self.editorMode = mode
        self.card = MockCard(id=99, did=7, note=note)
        self.parentWindow = SimpleNamespace(
            destroyed=FakeSignal(),
            isActiveWindow=lambda: False,
            deck_chooser=SimpleNamespace(selected_deck_id=7),
        )
        self.reloads = 0

    def call_after_note_saved(
        self, callback: Callable[[], None], keepFocus: bool = False
    ) -> None:
        callback()

    def loadNoteKeepingFocus(self) -> None:
        self.reloads += 1


def fake_main_window(collection: Any) -> Any:
    return SimpleNamespace(
        col=collection,
        taskman=SimpleNamespace(run_on_main=lambda callback: callback()),
    )


@pytest.mark.asyncio
async def test_review_update_is_undoable_and_returns_previous_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    note = AssistantMockNote({"Front": "Question", "Back": "Old answer"}, note_id=42)
    card = MockCard(id=99, did=7, note=note)
    collection = SimpleNamespace(get_card=lambda _card_id: card)
    monkeypatch.setattr(target_module, "mw", fake_main_window(collection))
    update_note = MagicMock(return_value=ImmediateCollectionOp())
    monkeypatch.setattr(target_module, "update_note", update_note)

    service = AssistantTargetService()
    result = await service.update_field(
        dto.parse_assistant_update_field(
            {
                "target": {"mode": "review", "cardId": 99},
                "fieldName": "Back",
                "newValue": "New answer",
            }
        )
    )

    assert note["Back"] == "New answer"
    assert result == {
        "status": "updated",
        "fieldName": "Back",
        "previousValue": "Old answer",
        "value": "New answer",
    }
    update_note.assert_called_once()


@pytest.mark.asyncio
async def test_editor_update_changes_only_the_bound_buffer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    note = AssistantMockNote({"Front": "Question", "Back": "Old answer"}, note_id=42)
    editor = FakeEditor(note, EditorMode.BROWSER)
    monkeypatch.setattr(
        target_module,
        "mw",
        fake_main_window(SimpleNamespace(decks=FakeDecks())),
    )

    service = AssistantTargetService()
    service.register_editor(cast(Editor, editor))
    bus = MagicMock()
    monkeypatch.setattr(target_module, "event_bus", bus)
    service.activate_editor(cast(Editor, editor))
    published_target = bus.publish.call_args.args[0].payload["target"]
    handle = published_target["handle"]

    assert published_target["noteTypeName"] == note.note_type()["name"]
    assert published_target["deckName"] == "Study"

    result = await service.update_field(
        dto.parse_assistant_update_field(
            {
                "target": handle,
                "fieldName": "Back",
                "newValue": "Buffered answer",
            }
        )
    )

    assert note["Back"] == "Buffered answer"
    assert editor.reloads == 1
    assert result["status"] == "buffered"
    assert result["previousValue"] == "Old answer"


@pytest.mark.asyncio
async def test_add_note_returns_the_generated_card_ids(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    note = AssistantMockNote({"Front": "", "Back": ""}, note_id=0)
    note.generated_card_ids = [201, 202]
    models = SimpleNamespace(
        by_name=lambda name: {"id": 1, "name": name} if name == "Basic" else None,
        all=lambda: [{"id": 1, "name": "Basic"}],
    )
    collection = SimpleNamespace(
        decks=FakeDecks(),
        models=models,
        new_note=lambda _model: note,
    )
    monkeypatch.setattr(target_module, "mw", fake_main_window(collection))
    monkeypatch.setattr(target_module, "deck_name_to_id_map", lambda: {"Study": 7})

    def mark_added() -> None:
        note.id = 101

    monkeypatch.setattr(
        target_module,
        "add_note",
        MagicMock(return_value=ImmediateCollectionOp(mark_added)),
    )

    service = AssistantTargetService()
    result = await service.add_note(
        dto.parse_assistant_add_note(
            {
                "noteType": "Basic",
                "deck": "Default",
                "fields": {"Front": "Question", "Back": "Answer"},
                "tags": ["assistant-created"],
            }
        )
    )

    assert note["Front"] == "Question"
    assert note["Back"] == "Answer"
    assert note.tags == ["assistant-created"]
    assert result == {"noteId": 101, "cardIds": [201, 202], "cardCount": 2}
