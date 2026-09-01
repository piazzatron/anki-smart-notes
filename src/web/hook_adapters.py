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

from typing import Any, Optional, cast

from anki.cards import Card
from anki.collection import OpChanges
from aqt import gui_hooks, mw
from aqt.browser.browser import Browser
from aqt.editor import Editor
from aqt.main import MainWindowState
from aqt.qt import QApplication, QWidget

from ..decks import rebuild_deck_cache
from ..event_bus import (
    BrowserSelectionChanged,
    StateInvalidated,
    event_bus,
)
from ..logger import logger
from ..services.assistant_target_service import assistant_target_service
from . import dto


def setup_web_hooks() -> None:
    gui_hooks.add_cards_did_change_deck.append(on_add_cards_deck_changed)
    gui_hooks.browser_did_change_row.append(on_browser_row_changed)
    gui_hooks.editor_did_init.append(on_editor_initialized)
    gui_hooks.editor_did_load_note.append(on_editor_note_loaded)
    gui_hooks.operation_did_execute.append(on_operation_did_execute)
    gui_hooks.reviewer_did_show_question.append(on_reviewer_did_show_question)
    gui_hooks.state_did_change.append(on_state_did_change)
    application = cast(Optional[QApplication], QApplication.instance())
    if application is not None:
        application.focusChanged.connect(on_focus_changed)


def on_operation_did_execute(changes: OpChanges, handler: Optional[object]) -> None:
    # Note type and deck creates/renames/deletes change the names the web UI
    # renders. Smart-field writes already publish via @republish_state.
    if changes.notetype or changes.deck:
        rebuild_deck_cache()
        event_bus.publish(StateInvalidated())


def on_reviewer_did_show_question(card: Card) -> None:
    try:
        assistant_target_service.on_reviewer_card_changed(card)
    except Exception as e:
        # Reviewer eventing is best-effort; never break review over it.
        logger.warning(f"Failed to publish reviewer card event: {e}")


def on_state_did_change(new_state: MainWindowState, old_state: MainWindowState) -> None:
    if old_state == "review" and new_state != "review":
        assistant_target_service.on_reviewer_closed()


def on_browser_row_changed(browser: Browser) -> None:
    try:
        event_bus.publish(BrowserSelectionChanged(_build_selection_payload(browser)))
        if browser.isActiveWindow() and browser.editor is not None:
            assistant_target_service.activate_editor(browser.editor)
    except Exception as e:
        # Selection eventing is best-effort; never break the browser over it.
        logger.warning(f"Failed to publish browser selection event: {e}")


def on_editor_initialized(editor: Editor) -> None:
    assistant_target_service.register_editor(editor)


def on_editor_note_loaded(editor: Editor) -> None:
    assistant_target_service.on_editor_loaded(editor)


def on_add_cards_deck_changed(_deck_id: int) -> None:
    assistant_target_service.refresh_active_editor()


def on_focus_changed(_old: Optional[QWidget], current: Optional[QWidget]) -> None:
    assistant_target_service.on_focus_changed(current)


def _build_selection_payload(browser: Browser) -> dict[str, Any]:
    selected_row_count = browser.table.len_selection()
    card = browser.table.get_single_selected_card()
    if not mw or not mw.col or card is None:
        return dto.build_selection_cleared(selected_row_count)

    return dto.build_selection_changed(card.note(), card.id, card.did)
