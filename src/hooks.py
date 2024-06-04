"""
Setup the hooks for the Anki plugin
"""

from typing import List, Callable, Any
from aqt import QAction, QMenu, gui_hooks, editor, mw, browser
from anki.cards import Card
from .processor import Processor

from .prompts import is_ai_field
from .ui.addon_options_dialog import AddonOptionsDialog

from .utils import check_for_api_key
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

        def on_success():

            # New notes have note id 0
            if note.id:
                # Only update note if it's already in the database
                mw.col.update_note(note)
            editor.loadNote()

        processor.process_note(note, overwrite_fields=True, on_success=on_success)

    button = e.addButton(
        cmd="AI Generate Fields",
        label="✨",
        func=fn,
        icon=None,
        tip="AI Generate Fields",
    )

    buttons.append(button)


@with_processor  # type: ignore
def on_browser_context(processor: Processor, browser: browser.Browser, menu: QMenu):  # type: ignore
    item = QAction("Process AI Fields", menu)
    menu.addAction(item)
    item.triggered.connect(
        lambda: processor.process_notes_with_progress(browser.selected_notes())
    )


@with_processor  # type: ignore
def on_main_window(processor: Processor):
    if not mw:
        return

    # Add options to Anki Menu
    options_action = QAction("AI Fields Options...", mw)
    options_action.triggered.connect(on_options(processor))
    mw.form.menuTools.addAction(options_action)

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
    item = QAction("✨ Generate AI Field", menu)
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

    def on_success():
        if not mw:
            print("Error: mw not found")
            return

        mw.col.update_note(note)
        card.load()
        print("Updated on review")

    processor.process_note(note, overwrite_fields=False, on_success=on_success)


def setup_hooks(processor: Processor):
    gui_hooks.browser_will_show_context_menu.append(on_browser_context(processor))
    gui_hooks.editor_did_init_buttons.append(add_editor_top_button(processor))
    gui_hooks.editor_will_show_context_menu.append(on_editor_context(processor))
    # TODO: I think this should be 'card did show'?
    gui_hooks.reviewer_did_show_question.append(on_review(processor))

    gui_hooks.main_window_did_init.append(on_main_window(processor))
