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

# Adapters from Anki gui_hooks to the web event bus. This module owns the mw
# coupling for eventing — the local server itself never touches Anki state.

from typing import Any, Optional

from anki.collection import OpChanges
from aqt import gui_hooks, mw
from aqt.browser.browser import Browser

from ..decks import invalidate_deck_cache
from ..logger import logger
from . import dto
from .event_bus import BrowserSelectionChanged, StateInvalidated, event_bus


def setup_web_hooks() -> None:
    gui_hooks.browser_did_change_row.append(on_browser_row_changed)
    gui_hooks.operation_did_execute.append(on_operation_did_execute)


def on_operation_did_execute(changes: OpChanges, handler: Optional[object]) -> None:
    # Note type and deck creates/renames/deletes change the names the web UI
    # renders. Smart-field writes already invalidate via the command layer.
    if changes.notetype or changes.deck:
        invalidate_deck_cache()
        event_bus.publish(StateInvalidated())


def on_browser_row_changed(browser: Browser) -> None:
    try:
        event_bus.publish(BrowserSelectionChanged(_build_selection_payload(browser)))
    except Exception as e:
        # Selection eventing is best-effort; never break the browser over it.
        logger.warning(f"Failed to publish browser selection event: {e}")


def _build_selection_payload(browser: Browser) -> dict[str, Any]:
    note_ids = browser.selected_notes()
    if not mw or not mw.col or len(note_ids) != 1:
        return dto.build_selection_cleared(len(note_ids))

    note = mw.col.get_note(note_ids[0])
    cards = note.cards()
    deck_id = cards[0].did if cards else None
    return dto.build_selection_changed(note, deck_id)
