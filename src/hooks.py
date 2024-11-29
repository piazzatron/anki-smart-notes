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
from typing import Callable, List, Sequence

from anki.cards import Card
from anki.notes import Note
from aqt import QAction, QMenu, browser, editor, gui_hooks, mw
from aqt.addcards import AddCards
from aqt.browser import SidebarItemType

from .app_state import app_state, is_app_unlocked_or_legacy
from .config import bump_usage_counter, config
from .decks import deck_id_to_name_map
from .logger import logger, setup_logger
from .message_polling import start_polling_for_messages
from .note_proccessor import NoteProcessor
from .notes import get_field_from_index, is_ai_field, is_card_fully_processed
from .sentry import pinger, sentry, with_sentry
from .tasks import run_async_in_background
from .ui.addon_options_dialog import AddonOptionsDialog
from .ui.changelog import perform_update_check
from .ui.custom_prompt import CustomImagePrompt, CustomTextPrompt, CustomTTSPrompt
from .ui.sparkle import Sparkle
from .ui.ui_utils import show_message_box
from .utils import make_uuid


def with_processor(fn):
    # Too annoying to type this thing
    """Decorator to pass the processor to the function."""

    def wrapper(processor: NoteProcessor):
        @with_sentry
        def inner(*args, **kwargs):
            return fn(processor, *args, **kwargs)

        return inner

    return wrapper


@with_processor  # type: ignore
def on_options(processor: NoteProcessor):
    app_state.update_subscription_state()
    dialog = AddonOptionsDialog(processor)
    dialog.exec()


@with_processor  # type: ignore
def add_editor_top_button(
    processor: NoteProcessor, buttons: List[str], e: editor.Editor
):

    @with_sentry
    def fn(editor: editor.Editor):
        if not mw:
            return

        if not is_app_unlocked_or_legacy(show_box=True):
            return

        card = editor.card
        note = editor.note

        if note is None:
            logger.error("Unexpectedly found no note")
            return

        # New notes don't have cards yet, fetch into the deck_chooser to get the deckId
        if card is None:
            parent = editor.parentWindow
            # Parent should always be AddCards if there's no card
            if isinstance(parent, AddCards):
                deck_id = parent.deck_chooser.selected_deck_id
                logger.debug(f"Setting deck_id to {deck_id}")
            card = note.ephemeral_card()
            if deck_id:
                card.did = deck_id

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

        def reloadNote() -> None:
            # Don't reload notes if they don't exist yet
            if note.id:
                note.load()
            editor.loadNote()

            parent = editor.parentWindow

            # Reload previewer if we need to
            if isinstance(parent, browser.Browser):  # type: ignore
                if parent._previewer:
                    parent._previewer.render_card()

        def on_success(did_change: bool):
            set_button_enabled()

            if not did_change:
                return

            reloadNote()

        def on_field() -> None:
            reloadNote()

        is_fully_processed = is_card_fully_processed(card)
        processor.process_card(
            card,
            overwrite_fields=is_fully_processed,
            on_success=on_success,
            on_failure=lambda _: set_button_enabled(),
            on_field_update=on_field,
            show_progress=True,
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


def make_on_batch_success(
    browser: browser.Browser,  # type: ignore
) -> Callable[[List[Note], List[Note]], None]:
    def wrapped_on_batch_success(updated: List[Note], errors: List[Note]):
        browser.on_all_or_selected_rows_changed()

        if not len(updated) and len(errors):
            show_message_box("All notes failed. Try again soon.")
        elif len(errors):
            show_message_box(
                f"Processed {len(updated)} notes successfully. {len(errors)} notes failed."
            )
        else:
            show_message_box(f"Processed {len(updated)} notes successfully.")

    return wrapped_on_batch_success


@with_processor  # type: ignore
def on_browser_context(processor: NoteProcessor, browser: browser.Browser, menu: QMenu):  # type: ignore
    item = QAction("✨ Generate Smart Fields", menu)
    menu.addSeparator()
    menu.addAction(item)

    cards = browser.selected_cards()

    def wrapped():
        if not is_app_unlocked_or_legacy(show_box=True):
            return

        if not prevent_batches_on_free_trial(cards):
            return

        processor.process_cards_with_progress(
            cards,
            on_success=make_on_batch_success(browser),
            overwrite_fields=config.regenerate_notes_when_batching,
        )

    item.triggered.connect(wrapped)


def on_start_actions() -> None:
    # Make UUID if necessary
    if not config.uuid:
        config.uuid = make_uuid()

    run_async_in_background(pinger("session_start"), use_collection=False)
    perform_update_check()
    start_polling_for_messages()

    app_state.update_subscription_state()
    if sentry:
        sentry.configure_scope()

    async def cache_leaf_decks_map():
        deck_id_to_name_map()

    run_async_in_background(cache_leaf_decks_map)


@with_processor  # type: ignore
def on_main_window(processor: NoteProcessor):
    if not mw:
        return

    # Setup logger as first thing
    setup_logger()
    # Then setup config, which depends on logger
    config.setup_config()

    # Add options to Anki Menu
    options_action = QAction("Smart Notes", mw)
    # Triggered passes a bool, so we need to use a lambda to pass the processor
    options_action.triggered.connect(lambda _: on_options(processor)())
    mw.form.menuTools.addAction(options_action)
    mw.addonManager.setConfigAction(__name__, on_options(processor))
    on_start_actions()


@with_processor  # type: ignore
def on_editor_context(
    processor: NoteProcessor, editor_web_view: editor.EditorWebView, menu: QMenu
):
    editor = editor_web_view.editor
    card = editor.card
    if not card:
        return

    current_field_num = editor.currentField
    if current_field_num is None:
        return

    ai_field = is_ai_field(current_field_num, card)

    def on_generate_success(_: bool):
        editor.loadNote()

    def process_card_wrapped():
        if not is_app_unlocked_or_legacy(show_box=True):
            return

        processor.process_card(
            card,
            overwrite_fields=False,
            target_field=ai_field,
            on_success=on_generate_success,
            show_progress=True,
        )

    menu.addSeparator()

    if ai_field:
        generate_field_item = QAction("✨ Generate Smart Field", menu)
        generate_field_item.triggered.connect(process_card_wrapped)
        menu.addAction(generate_field_item)
        menu.addSeparator()

    custom_text_item = QAction("💬 Custom Text", menu)
    custom_tts_item = QAction("📣 Custom TTS", menu)
    custom_image_item = QAction("🖼️ Custom Image", menu)

    field = get_field_from_index(card.note(), current_field_num)
    if not field:
        return

    def on_custom_text(_: bool):
        custom_prompt = CustomTextPrompt(
            note=card.note(),
            deck_id=card.did,
            field_upper=field,
            on_success=lambda: editor.loadNote(),
        )
        custom_prompt.exec()

    def on_custom_image(_: bool):
        custom_prompt = CustomImagePrompt(
            note=card.note(),
            deck_id=card.did,
            field_upper=field,
            on_success=lambda: editor.loadNote(),
            parent=editor.parentWindow,
        )
        # This should be called with exec instead of show, but
        # for some reason having a webview inside of this dialog
        # causes UI bugs when using exec
        custom_prompt.show()

    def on_custom_tts(_: bool):
        custom_tts = CustomTTSPrompt(
            note=card.note(),
            deck_id=card.did,
            field_upper=field,
            on_success=lambda: editor.loadNote(),
        )
        custom_tts.exec()

    custom_text_item.triggered.connect(on_custom_text)
    custom_image_item.triggered.connect(on_custom_image)
    custom_tts_item.triggered.connect(on_custom_tts)

    menu.addAction(custom_text_item)
    menu.addAction(custom_tts_item)
    menu.addAction(custom_image_item)


@with_processor  # type: ignore
def on_review(processor: NoteProcessor, card: Card):
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

    processor.process_card(
        card, overwrite_fields=False, on_success=on_success, show_progress=False
    )


@with_processor  # type: ignore
def add_deck_option(
    processor: NoteProcessor,
    tree_view: browser.sidebar.SidebarTreeView,  # type: ignore
    menu: QMenu,
    sidebar_item: browser.SidebarItem,  # type: ignore
    _,
) -> None:
    if not mw:
        return
    cards: Sequence[int] = []

    if sidebar_item.item_type == SidebarItemType.NOTETYPE:
        cards = mw.col.find_cards(f'"note:{sidebar_item.name}"')
    elif sidebar_item.item_type in [SidebarItemType.DECK, SidebarItemType.DECK_CURRENT]:
        query = f'"deck:{sidebar_item.full_name}"'
        cards = mw.col.find_cards(query)
    else:
        return

    item = QAction("✨ Generate Smart Fields", menu)
    menu.addSeparator()
    menu.addAction(item)

    def wrapped():
        if not is_app_unlocked_or_legacy(show_box=True):
            return
        if not prevent_batches_on_free_trial(cards):
            return

        processor.process_cards_with_progress(
            cards,
            on_success=make_on_batch_success(tree_view.browser),
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
            "Warning: your free trial allows a limited number of cards. Continue?",
            show_cancel=True,
        )
        return did_accept
    return True


@with_sentry
def setup_hooks(processor: NoteProcessor):
    gui_hooks.browser_will_show_context_menu.append(on_browser_context(processor))
    gui_hooks.browser_sidebar_will_show_context_menu.append(add_deck_option(processor))
    gui_hooks.editor_did_init_buttons.append(add_editor_top_button(processor))
    gui_hooks.editor_will_show_context_menu.append(on_editor_context(processor))
    gui_hooks.reviewer_did_show_question.append(on_review(processor))
    gui_hooks.main_window_did_init.append(on_main_window(processor))
    gui_hooks.profile_will_close.append(cleanup)
