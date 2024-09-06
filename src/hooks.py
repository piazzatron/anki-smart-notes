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

"""
Setup the hooks for the Anki plugin
"""


import logging
from typing import List, Sequence

from anki.cards import Card
from anki.notes import Note, NoteId
from aqt import QAction, QMenu, browser, editor, gui_hooks, mw
from aqt.browser import SidebarItemType

from .app_state import app_state, is_app_unlocked_or_legacy
from .config import config
from .logger import logger
from .message_polling import start_polling_for_messages
from .notes import is_ai_field, is_note_fully_processed
from .processor import Processor
from .sentry import pinger, sentry, with_sentry
from .tasks import run_async_in_background
from .ui.addon_options_dialog import AddonOptionsDialog
from .ui.changelog import perform_update_check
from .ui.sparkle import Sparkle
from .ui.ui_utils import show_message_box
from .utils import bump_usage_counter, make_uuid


def with_processor(fn):
    # Too annoying to type this thing
    """Decorator to pass the processor to the function."""

    def wrapper(processor: Processor):
        @with_sentry
        def inner(*args, **kwargs):
            return fn(processor, *args, **kwargs)

        return inner

    return wrapper


@with_processor  # type: ignore
def on_options(processor: Processor):
    app_state.update_subscription_state()
    dialog = AddonOptionsDialog(processor)
    dialog.exec()


@with_processor  # type: ignore
def add_editor_top_button(processor: Processor, buttons: List[str], e: editor.Editor):

    @with_sentry
    def fn(editor: editor.Editor):
        if not is_app_unlocked_or_legacy(show_box=True):
            return

        note = editor.note

        if not note:
            logger.error("no note found")
            return

        if not mw:
            return

        # Imperatively set the button styling and disabled state 🤦‍♂️
        # y u do dis, anki

        def set_button_disabled() -> None:
            if not e or not e.web:
                return
            e.web.eval(
                """
                    (() => {
                        const button = document.querySelector("#generate_smart_fields")
                        button.disabled = true
                        button.style.opacity = 0.25
                    })()
                """
            )

        def set_button_enabled() -> None:
            if not e or not e.web:
                return

            e.web.eval(
                """
                    (() => {
                        const button = document.querySelector("#generate_smart_fields")
                        button.disabled = false
                        button.style.opacity = 1.0
                    })()
                """
            )

        set_button_disabled()

        def on_success(did_change: bool):
            set_button_enabled()

            if not did_change:
                return

            # New notes have note id 0
            if note.id:
                # Only update note if it's already in the database
                mw.col.update_note(note)
            editor.loadNote()

        def on_field() -> None:
            editor.loadNote()

        is_fully_processed = is_note_fully_processed(note)
        processor.process_note(
            note,
            overwrite_fields=is_fully_processed,
            on_success=on_success,
            on_failure=lambda _: set_button_enabled(),
            on_field_update=on_field,
        )

    button = e.addButton(
        cmd="Generate Smart Fields",
        label="✨",
        func=fn,
        icon=None,
        tip="Ctrl+Shift+G: Generate Smart Fields",
        id="generate_smart_fields",
        keys="Ctrl+Shift+G",
    )

    buttons.append(button)


def on_batch_success(updated: List[Note], errors: List[Note]) -> None:
    if not len(updated) and len(errors):
        show_message_box("All notes failed. Try again soon.")
    elif len(errors):
        show_message_box(
            f"Processed {len(updated)} notes successfully. {len(errors)} notes failed."
        )
    else:
        show_message_box(f"Processed {len(updated)} notes successfully.")


@with_processor  # type: ignore
def on_browser_context(processor: Processor, browser: browser.Browser, menu: QMenu):  # type: ignore
    item = QAction("✨ Generate Smart Fields", menu)
    menu.addSeparator()
    menu.addAction(item)

    notes = browser.selected_notes()

    def wrapped():
        if not is_app_unlocked_or_legacy(show_box=True):
            return

        if not prevent_batches_on_free_trial(notes):
            return

        processor.process_notes_with_progress(
            notes,
            on_success=on_batch_success,
            overwrite_fields=config.regenerate_notes_when_batching,
        )

    item.triggered.connect(wrapped)


# TODO: where does this go now?
def migrate_models() -> None:
    if config.openai_model == "gpt-3.5-turbo":
        logger.debug(f"migrate_models: old 3.5-turbo model seen, migrating to 4o-mini")
        config.openai_model = "gpt-4o-mini"


def on_start_actions() -> None:
    if not config.uuid:
        config.uuid = make_uuid()

    run_async_in_background(pinger())
    perform_update_check()
    migrate_models()
    start_polling_for_messages()

    app_state.update_subscription_state()
    if sentry:
        sentry.configure_scope()


@with_processor  # type: ignore
def on_main_window(processor: Processor):
    if not mw:
        return

    # Add options to Anki Menu
    options_action = QAction("Smart Notes", mw)
    # Triggered passes a bool, so we need to use a lambda to pass the processor
    options_action.triggered.connect(lambda _: on_options(processor)())
    mw.form.menuTools.addAction(options_action)
    mw.addonManager.setConfigAction(__name__, on_options(processor))
    on_start_actions()


@with_processor  # type: ignore
def on_editor_context(
    processor: Processor, editor_web_view: editor.EditorWebView, menu: QMenu
):
    editor = editor_web_view.editor
    note = editor.note
    if not note:
        return

    current_field_num = editor.currentField
    if current_field_num is None:
        return

    ai_field = is_ai_field(current_field_num, note)
    if not ai_field:
        return
    item = QAction("✨ Generate Smart Field", menu)

    def on_success(_: bool):
        editor.loadNote()

    def wrapped():
        if not is_app_unlocked_or_legacy(show_box=True):
            return

        processor.process_note(
            note, overwrite_fields=False, target_field=ai_field, on_success=on_success
        )

    item.triggered.connect(wrapped)
    menu.addAction(item)


@with_processor  # type: ignore
def on_review(processor: Processor, card: Card):
    logger.debug("Reviewing...")
    if not is_app_unlocked_or_legacy(show_box=False):
        return

    if not config.generate_at_review:
        return

    note = card.note()

    def on_success(did_change: bool):
        if not did_change:
            return

        if not mw:
            logger.error("Error: mw not found")
            return

        logger.debug("Did update card on review...")

        mw.col.update_note(note)
        card.load()
        Sparkle()

        # NOTE: Calling this inside processor causes a crash with
        # Suppressing invocation of -[NSApplication runModalSession:]. -[NSApplication runModalSession:] cannot run inside a transaction begin/commit pair, or inside a transaction commit. Consider switching to an asynchronous equivalent.
        bump_usage_counter()

    processor.process_note(note, overwrite_fields=False, on_success=on_success)


@with_processor  # type: ignore
def add_deck_option(
    processor: Processor,
    tree_view,
    menu: QMenu,
    sidebar_item: browser.SidebarItem,  # type: ignore
    model_index,
) -> None:
    if not mw:
        return
    notes: Sequence[NoteId] = []

    if sidebar_item.item_type == SidebarItemType.NOTETYPE:
        notes = mw.col.find_notes(f'"note:{sidebar_item.name}"')
    elif sidebar_item.item_type in [SidebarItemType.DECK, SidebarItemType.DECK_CURRENT]:
        notes = mw.col.find_notes(f'"deck:{sidebar_item.name}"')
    else:
        return

    item = QAction("✨ Generate Smart Fields", menu)
    menu.addSeparator()
    menu.addAction(item)

    def wrapped():
        if not is_app_unlocked_or_legacy(show_box=True):
            return
        if not prevent_batches_on_free_trial(notes):
            return

        processor.process_notes_with_progress(
            notes,
            on_success=on_batch_success,
        )

    item.triggered.connect(wrapped)


@with_sentry
def cleanup() -> None:
    logger.debug("Shutting down loggers")
    # Ridiculous hack to fix this sentry logger error:
    # I don't quite understand it but the stream handler setup in sentry_sdk
    # isn't torn down correctly.
    #   Traceback (most recent call last):
    #   File "logging", line 2141, in shutdown
    #   File "logging", line 1066, in flush
    # RuntimeError: wrapped C/C++ object of type ErrorHandler has been deleted

    sentry_logger = logging.getLogger("sentry_sdk.errors")
    sentry_logger.handlers.clear()
    logger.handlers.clear()


def prevent_batches_on_free_trial(notes) -> bool:
    if app_state.is_free_trial() and len(notes) > 50:
        did_accept: bool = show_message_box(
            "Warning: your free trial is limited to 500 cards. Continue?",
            show_cancel=True,
        )
        return did_accept
    return True


@with_sentry
def setup_hooks(processor: Processor):
    gui_hooks.browser_will_show_context_menu.append(on_browser_context(processor))
    gui_hooks.browser_sidebar_will_show_context_menu.append(add_deck_option(processor))
    gui_hooks.editor_did_init_buttons.append(add_editor_top_button(processor))
    gui_hooks.editor_will_show_context_menu.append(on_editor_context(processor))
    gui_hooks.reviewer_did_show_question.append(on_review(processor))
    gui_hooks.main_window_did_init.append(on_main_window(processor))
    gui_hooks.profile_will_close.append(cleanup)
