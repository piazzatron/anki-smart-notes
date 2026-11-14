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
from collections.abc import Callable, Sequence
from typing import Any, Optional

from anki.cards import Card
from anki.collection import Collection
from anki.decks import DeckId
from anki.hooks import note_will_be_added
from anki.notes import Note
from anki.utils import is_mac
from aqt import QAction, QMenu, browser, editor, gui_hooks, mw
from aqt.browser.sidebar.item import SidebarItemType
from aqt.qt import QKeySequence, QMenuBar, QShortcut

from .add_time_evaluator import AddTimeEvaluator
from .app_state import app_state
from .config import config, get_install_id
from .database.migrations import run_migrations
from .decks import deck_id_to_name_map
from .event_bus import event_bus
from .feature_flags import refresh_feature_flags
from .generation_access import ensure_generation_available
from .logger import cleanup_logger, logger
from .note_proccessor import NoteProcessor
from .review_time_evaluator import ReviewTimeEvaluator
from .sentry import sentry, with_sentry
from .tasks import run_async_in_background
from .telemetry import track_event
from .ui.changelog import ChangeLogDialog, is_new_major_or_minor_version
from .ui.field_menu import FieldMenu
from .ui.generate_affordances import (
    EDITOR_CHANGED_COMMAND,
    GENERATE_FIELD_COMMAND,
    GENERATE_SHORTCUT,
    LEGACY_GENERATE_SHORTCUT,
    add_dialog_banner,
    add_generate_banner,
    editor_busy,
    editor_card,
    fields_regenerated_with,
    generate_from_banner,
    is_editor,
    on_add_cards_did_change_deck,
    on_operation_did_execute as on_banner_operation_did_execute,
    refresh_banner,
    refresh_editor,
    schedule_editor_refresh,
    set_editor_busy,
    show_generated_note,
    with_editor_card,
)
from .ui.i18n import native_action_text
from .ui.ui_utils import show_message_box
from .utils import get_version
from .utils.notes_utils import get_field_from_index, is_ai_field
from .web.hook_adapters import setup_web_hooks
from .web_app import (
    close_web_app,
    ensure_local_server_started,
    open_web_app,
    stop_local_server,
)

_review_time_evaluator: Optional[ReviewTimeEvaluator] = None
_add_time_evaluator: Optional[AddTimeEvaluator] = None

# Set once Anki starts replacing or deleting this add-on's files. This code stays
# loaded until Anki restarts, but the database and web files can vanish under it,
# so hook entry points stand down until then.
_addon_files_changing = False


def _with_processor(fn: Any):
    # Too annoying to type this thing
    """Decorator to pass the processor to the function."""

    def wrapper(processor: NoteProcessor):
        @with_sentry
        def inner(*args: Any, **kwargs: Any):
            if _addon_files_changing:
                return None
            return fn(processor, *args, **kwargs)

        return inner

    return wrapper


@_with_processor  # type: ignore
def on_editor_did_init_shortcuts(
    processor: NoteProcessor, cuts: list[tuple[Any, ...]], e: editor.Editor
) -> None:
    # The Browser has its own shortcut (on_browser_will_show): two for the same
    # keys in one window would be ambiguous, and Qt would fire neither.
    if isinstance(e.parentWindow, browser.Browser):  # type: ignore
        return
    # The third element keeps it working while no field is focused.
    for keys in (GENERATE_SHORTCUT, LEGACY_GENERATE_SHORTCUT):
        cuts.append((keys, lambda: _generate_editor_note(processor, e), True))


@_with_processor  # type: ignore
def on_editor_did_init(processor: NoteProcessor, e: editor.Editor) -> None:
    add_dialog_banner(
        e,
        lambda overwrite_fields: _generate_editor_note(processor, e, overwrite_fields),
    )


def _generate_editor_note(
    processor: NoteProcessor, e: editor.Editor, overwrite_fields: bool = False
) -> None:
    """Fills the editor note's empty Smart Fields, or regenerates them all."""
    if editor_busy(e):
        return
    set_editor_busy(e, True, "all" if overwrite_fields else "empty")

    @with_sentry
    def generate(card: Card) -> None:
        # The shortcut outlives the hook call that added it.
        if not mw or _addon_files_changing or not ensure_generation_available():
            set_editor_busy(e, False)
            return

        # The processor fills in card.note(), then the editor shows it.
        note = card.note()
        original_fields = [note[name] for name in note.keys()]  # noqa: SIM118

        def on_success(did_change: bool) -> None:
            if did_change:
                show_generated_note(e, note, original_fields)
            set_editor_busy(e, False)

        processor.process_card(
            card,
            overwrite_fields=overwrite_fields,
            on_success=on_success,
            on_failure=lambda _: set_editor_busy(e, False),
            on_field_update=lambda: show_generated_note(e, note, original_fields),
            show_progress=False,
        )

    e.call_after_note_saved(lambda: with_editor_card(e, generate), keepFocus=True)


def on_webview_did_receive_js_message(
    processor: NoteProcessor,
) -> Callable[[tuple[bool, Any], str, Any], tuple[bool, Any]]:
    """Handles clicks on an editor field's Generate button, and refreshes the
    editor's buttons as its fields change."""

    def handle(
        handled: tuple[bool, Any], message: str, context: Any
    ) -> tuple[bool, Any]:
        if _addon_files_changing:
            return handled
        command, _, field_index = message.partition(":")
        if command == GENERATE_FIELD_COMMAND:
            _generate_editor_field(processor, context, int(field_index))
            return (True, None)
        # Both editors report typing and leaving a field with key and blur; the
        # experimental editor reports a loaded note with editorState, and its
        # Add dialog's note type and deck changes through our own command.
        refreshing = ("key", "blur", "editorState", EDITOR_CHANGED_COMMAND)
        if command in refreshing and is_editor(context):
            schedule_editor_refresh(context)
        return handled

    return handle


def _generate_editor_field(
    processor: NoteProcessor, e: editor.Editor, field_index: int
) -> None:
    """Generates one field like the field's right-click Generate Smart Field: it
    always regenerates, its inputs fill only if empty, and regenerating a filled
    field also regenerates the fields that depend on it."""

    if editor_busy(e):
        return
    set_editor_busy(e, True, frozenset({field_index}))

    @with_sentry
    def generate(card: Card) -> None:
        note = card.note()
        field_names = note.keys()
        if (
            not mw
            or _addon_files_changing
            or field_index >= len(field_names)
            or not ensure_generation_available()
        ):
            set_editor_busy(e, False)
            return

        original_fields = [note[name] for name in note.keys()]  # noqa: SIM118
        # Its dependents read Generating too, when they're regenerated with it.
        set_editor_busy(
            e, True, fields_regenerated_with(card, field_names[field_index])
        )

        # Also on failure: fields generated before a later one failed are kept.
        def on_done() -> None:
            show_generated_note(e, note, original_fields)
            set_editor_busy(e, False)

        processor.process_card(
            card,
            overwrite_fields=False,
            target_field=field_names[field_index],
            on_success=lambda _: on_done(),
            on_failure=lambda _: on_done(),
            show_progress=True,
        )

    e.call_after_note_saved(lambda: with_editor_card(e, generate), keepFocus=True)


def _make_on_batch_success(
    browser: browser.Browser,  # type: ignore
) -> Callable[[list[Note], list[Note], list[Note]], None]:
    def wrapped_on_batch_success(
        updated: list[Note], errors: list[Note], skipped: list[Note]
    ):
        browser.on_all_or_selected_rows_changed()

        def pluralize(word: str, count: int) -> str:
            return f"{count} {word}{'s' if count != 1 else ''}"

        if not len(updated) and len(errors):
            show_message_box("All notes failed. Try again soon.")
        elif len(errors) or len(skipped):
            parts = [f"Processed {pluralize('note', len(updated))} successfully"]
            if len(errors):
                parts.append(f"{pluralize('note', len(errors))} failed")
            if len(skipped):
                parts.append(f"{pluralize('note', len(skipped))} skipped")
            show_message_box(". ".join(parts) + ".")
        else:
            show_message_box(
                f"Processed {pluralize('note', len(updated))} successfully."
            )

    return wrapped_on_batch_success


@_with_processor  # type: ignore
def on_browser_will_show(processor: NoteProcessor, b: browser.Browser) -> None:  # type: ignore
    @with_sentry
    def generate(overwrite_fields: bool) -> None:
        if _addon_files_changing or not ensure_generation_available():
            return
        processor.process_cards_with_progress(
            b.selected_cards(),
            on_success=_make_on_batch_success(b),
            overwrite_fields=overwrite_fields,
        )

    add_generate_banner(b, generate)

    @with_sentry
    def on_shortcut() -> None:
        # One note in the editor generates as in any editor, which saves its
        # edits first and isn't a batch; otherwise it's the banner's button.
        if getattr(b, "singleCard", False) and b.editor:
            # On Anki 26.9 this can be the experimental editor (NewEditor), which
            # the editor helpers handle as they do in its Add and Edit dialogs.
            _generate_editor_note(processor, b.editor)  # pyright: ignore[reportArgumentType]
        else:
            generate_from_banner(b)

    QShortcut(QKeySequence(GENERATE_SHORTCUT), b, activated=on_shortcut)  # type: ignore


@_with_processor  # type: ignore
def on_browser_context(processor: NoteProcessor, browser: browser.Browser, menu: QMenu):  # type: ignore
    item = QAction(f"✨ {native_action_text('generate_smart_fields')}", menu)
    menu.addSeparator()
    menu.addAction(item)

    cards = browser.selected_cards()

    def wrapped():
        if not ensure_generation_available():
            return

        processor.process_cards_with_progress(
            cards,
            on_success=_make_on_batch_success(browser),
            overwrite_fields=False,
        )

    item.triggered.connect(wrapped)


def _on_start_actions() -> None:
    # Create the install ID on the main thread before any request needs it:
    # background requests creating it at once would each write a different one.
    get_install_id()
    refresh_feature_flags()

    app_state.update_account_state()
    if sentry:
        sentry.configure_scope()

    async def cache_leaf_decks_map():
        deck_id_to_name_map()

    run_async_in_background(cache_leaf_decks_map)


def _stamp_version_and_show_first_load_window() -> None:
    try:
        current_version = get_version()
        prior_version = config.last_seen_version
        config.last_seen_version = current_version

        logger.info(
            f"current version: {current_version}, prior version: {prior_version}, is first use: {not prior_version}"
        )

        if not mw:
            return

        if not prior_version:
            track_event("plugin_installed")
            open_web_app()
            return

        if is_new_major_or_minor_version(current_version, prior_version):
            ChangeLogDialog(prior_version).exec()
    except PermissionError as e:
        # The add-on folder isn't writable for this OS user (e.g. a shared Anki
        # folder owned by another account), so Anki can't save our config.
        logger.warning(f"Couldn't save the last seen version: {e}")
    except Exception as e:
        logger.error(f"Error checking for updates: {e}")


@_with_processor  # type: ignore
def on_main_window(processor: NoteProcessor):
    if not mw:
        return

    run_migrations()

    mw.form.menubar.addMenu(_smart_notes_menu(mw))
    # On macOS the menu bar belongs to the focused window. Windows without one of
    # their own, like the Add and Edit dialogs, show this parentless one.
    if is_mac:
        global _mac_default_menubar
        _mac_default_menubar = QMenuBar(None)
        _mac_default_menubar.addMenu(_smart_notes_menu(_mac_default_menubar))
    mw.addonManager.setConfigAction(__name__, open_web_app)

    _on_start_actions()

    _start_background_generation(processor)
    ensure_local_server_started()

    # Show either the first load window or the changelog once the web app's
    # local server is ready.
    _stamp_version_and_show_first_load_window()


_mac_default_menubar: Optional[QMenuBar] = None


def _smart_notes_menu(parent: Any) -> QMenu:
    menu = QMenu("Smart Notes", parent)
    action = QAction("Smart Notes", parent)
    action.triggered.connect(lambda _: open_web_app())
    menu.addAction(action)
    return menu


def on_browser_menus_did_init(b: browser.Browser) -> None:  # type: ignore
    """Gives the Browser the Smart Notes menu too: on macOS the menu bar belongs
    to the focused window, so the main window's menu is gone while the Browser
    is in front."""
    b.form.menubar.addMenu(_smart_notes_menu(b))


@_with_processor  # type: ignore
def on_profile_did_open(processor: NoteProcessor) -> None:
    # Profile cleanup stops background generation, so a profile switch needs
    # it started again.
    _start_background_generation(processor)
    ensure_local_server_started()


def _start_background_generation(processor: NoteProcessor) -> None:
    # Anki usually opens the profile before main_window_did_init, but can open it
    # after (Windows waits for its webviews), so both hooks call this.
    global _review_time_evaluator, _add_time_evaluator
    if _review_time_evaluator is None:
        _review_time_evaluator = ReviewTimeEvaluator(processor)
    if _add_time_evaluator is None:
        _add_time_evaluator = AddTimeEvaluator(processor)


@_with_processor  # type: ignore
def on_editor_context(
    processor: NoteProcessor, editor_web_view: editor.EditorWebView, menu: QMenu
):
    editor = editor_web_view.editor
    card = editor_card(editor)
    if card is None:
        return

    current_field_num = editor.currentField
    if current_field_num is None:
        return

    is_smart_field = bool(is_ai_field(current_field_num, card))

    # The FieldMenu UI component will add its own separators/actions as needed.

    field = get_field_from_index(card.note(), current_field_num)
    if not field:
        return

    field_menu = FieldMenu(
        editor_instance=editor,
        menu=menu,
        processor=processor,
        card=card,
        field_upper=field,
        is_smart_field=is_smart_field,
    )

    # Keep a reference to avoid premature garbage collection
    menu._smartnotes_field_menu = field_menu  # type: ignore


@_with_processor  # type: ignore
def add_deck_option(
    processor: NoteProcessor,
    tree_view: browser.sidebar.SidebarTreeView,  # type: ignore
    menu: QMenu,
    sidebar_item: browser.SidebarItem,  # type: ignore
    _,
) -> None:
    if not mw or not mw.col:
        return
    cards: Sequence[int] = []

    if sidebar_item.item_type == SidebarItemType.NOTETYPE:
        cards = mw.col.find_cards(f'"note:{sidebar_item.name}"')
    elif sidebar_item.item_type in [SidebarItemType.DECK, SidebarItemType.DECK_CURRENT]:
        query = f'"deck:{sidebar_item.full_name}"'
        cards = mw.col.find_cards(query)
    else:
        return

    item = QAction(f"✨ {native_action_text('generate_smart_fields')}", menu)
    menu.addSeparator()
    menu.addAction(item)

    def wrapped():
        if not ensure_generation_available():
            return
        processor.process_cards_with_progress(
            cards,
            on_success=_make_on_batch_success(tree_view.browser),
            overwrite_fields=False,
        )

    item.triggered.connect(wrapped)


@with_sentry
def cleanup() -> None:
    event_bus.clear_browser_selection()
    close_web_app()
    stop_local_server()

    global _review_time_evaluator, _add_time_evaluator
    if _review_time_evaluator is not None:
        _review_time_evaluator.stop()
    _review_time_evaluator = None
    if _add_time_evaluator is not None:
        _add_time_evaluator.stop()
    _add_time_evaluator = None

    logger.info("Shutting down loggers")
    # Ridiculous hack to fix this sentry logger error:
    # I don't quite understand it but the stream handler setup in sentry_sdk
    # isn't torn down correctly.
    #   Traceback (most recent call last):
    #   File "logging", line 2141, in shutdown
    #   File "logging", line 1066, in flush
    # RuntimeError: wrapped C/C++ object of type ErrorHandler has been deleted

    sentry_logger = logging.getLogger("sentry_sdk.errors")
    sentry_logger.handlers.clear()
    cleanup_logger()


def on_addon_manager_will_install_addon(_: Any, package: str) -> None:
    if not _is_current_addon_package(package):
        return

    _cleanup_before_addon_files_change()


def on_addons_dialog_will_delete_addons(_: Any, packages: Sequence[str]) -> None:
    if not any(_is_current_addon_package(package) for package in packages):
        return

    _cleanup_before_addon_files_change()


def _cleanup_before_addon_files_change() -> None:
    # Anki updates loaded add-ons in-process. On Windows, open files under the
    # add-on folder can block user_files backup or package deletion, leaving a
    # partial install. This hook runs on Anki's installer thread, so keep it to
    # non-UI resources instead of calling full profile-close cleanup.
    global _addon_files_changing
    _addon_files_changing = True
    logger.info("Preparing Smart Notes for add-on file replacement")

    # stop() only sets flags and clears a set, so it's safe off the main thread.
    logger.info("Stopping Smart Notes background generation")
    if _review_time_evaluator is not None:
        _review_time_evaluator.stop()
    if _add_time_evaluator is not None:
        _add_time_evaluator.stop()

    logger.info("Stopping Smart Notes local server before add-on file replacement")
    stop_local_server()

    logger.info("Closing Smart Notes log handlers before add-on file replacement")
    cleanup_logger()


def _is_current_addon_package(package: str) -> bool:
    return package == __name__.split(".", maxsplit=1)[0]


@with_sentry
def evaluate_review_time_generation() -> None:
    if _review_time_evaluator:
        _review_time_evaluator.tick()


@with_sentry
def on_note_will_be_added(_: Collection, note: Note, __: DeckId) -> None:
    # Fires for every Python-side add (Add dialog, AnkiConnect, other add-ons),
    # possibly off the main thread. Package imports run in the backend and
    # don't fire it.
    if _add_time_evaluator:
        _add_time_evaluator.on_note_will_be_added(note)


@with_sentry
def setup_hooks(processor: NoteProcessor):
    setup_web_hooks()
    gui_hooks.browser_will_show_context_menu.append(on_browser_context(processor))
    gui_hooks.browser_menus_did_init.append(on_browser_menus_did_init)
    gui_hooks.browser_sidebar_will_show_context_menu.append(add_deck_option(processor))
    gui_hooks.editor_did_init_shortcuts.append(on_editor_did_init_shortcuts(processor))
    gui_hooks.editor_will_show_context_menu.append(on_editor_context(processor))
    gui_hooks.webview_did_receive_js_message.append(
        on_webview_did_receive_js_message(processor)
    )
    gui_hooks.browser_will_show.append(on_browser_will_show(processor))
    gui_hooks.browser_did_change_row.append(refresh_banner)
    gui_hooks.operation_did_execute.append(on_banner_operation_did_execute)
    gui_hooks.editor_did_load_note.append(refresh_editor)
    gui_hooks.editor_did_init.append(on_editor_did_init(processor))
    # Not in every supported Anki.
    if hasattr(gui_hooks, "add_cards_did_change_deck"):
        gui_hooks.add_cards_did_change_deck.append(on_add_cards_did_change_deck)
    gui_hooks.overview_did_refresh.append(lambda _: evaluate_review_time_generation())
    gui_hooks.reviewer_did_show_question.append(
        lambda _: evaluate_review_time_generation()
    )
    gui_hooks.reviewer_did_answer_card.append(
        lambda *_: evaluate_review_time_generation()
    )
    note_will_be_added.append(on_note_will_be_added)
    gui_hooks.main_window_did_init.append(on_main_window(processor))
    gui_hooks.profile_did_open.append(on_profile_did_open(processor))
    gui_hooks.profile_will_close.append(cleanup)

    # These cleanup hooks were added in different Anki versions.
    if hasattr(gui_hooks, "addon_manager_will_install_addon"):
        gui_hooks.addon_manager_will_install_addon.append(
            on_addon_manager_will_install_addon
        )
    if hasattr(gui_hooks, "addons_dialog_will_delete_addons"):
        gui_hooks.addons_dialog_will_delete_addons.append(
            on_addons_dialog_will_delete_addons
        )
