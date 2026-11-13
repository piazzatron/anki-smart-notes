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

import re
from typing import Optional

from anki.collection import SearchNode
from anki.decks import DeckId
from anki.models import NotetypeId
from aqt import QFont, QFormLayout, QMessageBox, QPushButton, Qt, dialogs, mw


def open_anki_browser() -> None:
    dialogs.open("Browser", mw)


def open_browser_on_field(note_type_id: int, deck_id: int, field_name: str) -> None:
    """Opens the Browser on a Smart Field's notes and selects one where the field is
    empty, so the generate banner is right there. Falls back to the first note."""
    if not mw or not mw.col:
        return
    col = mw.col

    note_type = col.models.get(NotetypeId(note_type_id))
    if not note_type:
        return
    # Readable searches, since the user sees them. A deck-specific Smart Field only
    # applies to its own deck.
    nodes = [SearchNode(note=note_type["name"])]
    deck = col.decks.get(DeckId(deck_id), default=False) if deck_id != -1 else None
    if deck:
        nodes.append(SearchNode(deck=deck["name"]))
    search = col.build_search_string(*nodes)
    # `Field:` matches an empty field; * and _ are wildcards in field names.
    escaped = re.sub(r'([\\*_"])', r"\\\1", field_name)
    empty_cards = col.find_cards(f'{search} "{escaped}:"')
    cards = empty_cards or col.find_cards(search)

    browser = dialogs.open("Browser", mw)
    browser.search_for(search)
    if cards:
        browser.table.select_single_card(cards[0])


def show_message_box(
    message: str,
    details: Optional[str] = None,
    custom_ok: Optional[str] = None,
    show_cancel: bool = False,
):
    msg = QMessageBox()
    msg.setText(message)

    if details:
        msg.setInformativeText(details)

    # TODO: this custom_ok is getting put in the wrong position (left most), idk why
    ok_button = None
    if custom_ok:
        ok_button = QPushButton(custom_ok)
        msg.addButton(ok_button, QMessageBox.ButtonRole.ActionRole)

    else:
        msg.addButton(QMessageBox.StandardButton.Ok)

    if show_cancel:
        msg.addButton(QMessageBox.StandardButton.Cancel)

    val = msg.exec()
    return msg.clickedButton() == ok_button or val == QMessageBox.StandardButton.Ok


def default_form_layout() -> QFormLayout:
    form = QFormLayout()
    form.setVerticalSpacing(12)
    form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
    form.setFormAlignment(Qt.AlignmentFlag.AlignLeft)
    return form


# UI constants
font_small = QFont()
font_small.setPointSize(10)

font_large = QFont()
font_large.setPointSize(16)
font_large.setBold(True)

font_bold = QFont()
font_bold.setBold(True)
font_bold.setPointSize(12)
