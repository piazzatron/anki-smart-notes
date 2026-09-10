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

from typing import Optional
from unittest.mock import MagicMock

import pytest

from src.ui.field_menu import FieldMenu


class FakeNote(dict[str, str]):
    def __init__(self, note_id: Optional[int]) -> None:
        super().__init__()
        self.id = note_id


def test_custom_field_success_updates_live_editor_note(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import src.ui.field_menu

    live_note = FakeNote(note_id=123)
    stale_card_note = FakeNote(note_id=123)
    editor = MagicMock()
    editor.note = live_note
    card = MagicMock()
    card.note.return_value = stale_card_note
    mw = MagicMock()
    monkeypatch.setattr(src.ui.field_menu, "mw", mw)
    field_menu = FieldMenu.__new__(FieldMenu)
    field_menu.editor = editor
    field_menu.card = card
    field_menu.field_upper = "Audio"

    field_menu._make_custom_field_success()(  # pyright: ignore[reportPrivateUsage]
        "[sound: generated.mp3]"
    )

    assert live_note["Audio"] == "[sound: generated.mp3]"
    assert "Audio" not in stale_card_note
    mw.col.update_note.assert_called_once_with(live_note)
    editor.loadNoteKeepingFocus.assert_called_once()


def test_custom_field_success_updates_new_editor_note_without_persisting(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import src.ui.field_menu

    live_note = FakeNote(note_id=None)
    editor = MagicMock()
    editor.note = live_note
    card = MagicMock()
    mw = MagicMock()
    monkeypatch.setattr(src.ui.field_menu, "mw", mw)
    field_menu = FieldMenu.__new__(FieldMenu)
    field_menu.editor = editor
    field_menu.card = card
    field_menu.field_upper = "Image"

    field_menu._make_custom_field_success()(  # pyright: ignore[reportPrivateUsage]
        '<img src="generated.webp"/>'
    )

    assert live_note["Image"] == '<img src="generated.webp"/>'
    mw.col.update_note.assert_not_called()
    editor.loadNoteKeepingFocus.assert_called_once()
