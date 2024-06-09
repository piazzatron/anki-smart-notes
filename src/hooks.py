"""
Setup the hooks for the Anki plugin
"""

from typing import List, Any
from aqt import QAction, QMenu, QMessageBox, gui_hooks, editor, mw, browser, webview, Qt
from anki.cards import Card

from .ui.ui_utils import show_message_box
from .ui.sparkle import Sparkle
from .processor import Processor

from .prompts import is_ai_field
from .ui.addon_options_dialog import AddonOptionsDialog

from .utils import bump_usage_counter, check_for_api_key
from .config import config


def with_processor(fn):
    # Too annoying to type this thing
    """Decorator to pass the processor to the function."""

    def wrapper(processor: Processor):
        def inner(*args, **kwargs):
            return fn(processor, *args, **kwargs)

        return inner

    return wrapper


@with_processor  # type: ignore
def on_options(processor: Processor, second: Any):
    dialog = AddonOptionsDialog(config, processor)
    dialog.exec()


@with_processor  # type: ignore
def add_editor_top_button(processor: Processor, buttons: List[str], e: editor.Editor):
    def fn(editor: editor.Editor):
        if not check_for_api_key():
            return

        note = editor.note

        if not note:
            print("Error: no note found")
            return

        if not mw:
            return

        def on_success(did_change: bool):
            if not did_change:
                return

            # New notes have note id 0
            if note.id:
                # Only update note if it's already in the database
                mw.col.update_note(note)
            editor.loadNote()

        processor.process_note(note, overwrite_fields=True, on_success=on_success)

    button = e.addButton(
        cmd="Generate Smart Fields",
        label="✨",
        func=fn,
        icon=None,
        tip="Generate Smart Fields",
        disables=True,
    )

    buttons.append(button)


@with_processor  # type: ignore
def on_browser_context(processor: Processor, browser: browser.Browser, menu: QMenu):  # type: ignore
    item = QAction("✨ Generate Smart Fields", menu)
    menu.addAction(item)

    # TODO: should show # succeess and failed
    notes = browser.selected_notes()

    def on_success() -> None:
        show_message_box(f"Processed {len(notes)} notes successfully.")

    item.triggered.connect(
        lambda: processor.process_notes_with_progress(notes, on_success)
    )


@with_processor  # type: ignore
def on_main_window(processor: Processor):
    if not mw:
        return

    # Add options to Anki Menu
    options_action = QAction("Smart Notes", mw)
    options_action.triggered.connect(on_options(processor))
    mw.form.menuTools.addAction(options_action)
    # TODO: not working for some reason
    mw.addonManager.setConfigAction(__name__, on_options(processor))


# TODO: do I need a profile_will_close thing here?


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
    item.triggered.connect(
        lambda: processor.process_single_field(note, ai_field, editor)
    )
    menu.addAction(item)


@with_processor  # type: ignore
def on_review(processor: Processor, card: Card):
    print("Reviewing...")
    if not check_for_api_key(show_box=False):
        return
    note = card.note()

    def on_success(did_change: bool):
        if not did_change:
            return

        if not mw:
            print("Error: mw not found")
            return

        print("Did update card on review...")

        mw.col.update_note(note)
        card.load()
        Sparkle()

        # NOTE: Calling this inside processor causes a crash with
        # Suppressing invocation of -[NSApplication runModalSession:]. -[NSApplication runModalSession:] cannot run inside a transaction begin/commit pair, or inside a transaction commit. Consider switching to an asynchronous equivalent.
        bump_usage_counter()

    print("Trying to set up web...")

    processor.process_note(note, overwrite_fields=False, on_success=on_success)


def setup_hooks(processor: Processor):
    gui_hooks.browser_will_show_context_menu.append(on_browser_context(processor))
    gui_hooks.editor_did_init_buttons.append(add_editor_top_button(processor))
    gui_hooks.editor_will_show_context_menu.append(on_editor_context(processor))
    gui_hooks.reviewer_did_show_question.append(on_review(processor))

    gui_hooks.main_window_did_init.append(on_main_window(processor))
