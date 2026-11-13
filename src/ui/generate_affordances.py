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

import json
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any, Optional

import aqt.addcards
import aqt.editcurrent
from anki.cards import Card
from anki.collection import OpChanges
from anki.models import NotetypeId
from anki.notes import Note
from anki.utils import ids2str
from aqt import editor, mw
from aqt.addcards import AddCards
from aqt.browser.browser import Browser
from aqt.editcurrent import EditCurrent
from aqt.qt import (
    QApplication,
    QBoxLayout,
    QFrame,
    QHBoxLayout,
    QIcon,
    QLabel,
    QPixmap,
    QPushButton,
    QSize,
    QSizePolicy,
    Qt,
    QTimer,
)

from ..config import config
from ..logger import logger
from ..models.smart_fields import SmartField, TTSSmartFieldSettings
from ..prompt_fields import get_prompt_fields
from ..prompt_helpers import html_to_text
from ..services.smart_field_service import smart_field_service
from ..utils.notes_utils import note_decks
from .i18n import native_action_text

_BANNER_NAME = "smartNotesGenerateBanner"

# The pycmd a field's Generate button sends, followed by ":<field index>".
GENERATE_FIELD_COMMAND = "smartNotesGenerateField"

# Free in the Browser and both editors, and it pairs with Anki's Ctrl+Enter (Add).
# Ctrl+Shift+G is Anki's Grade Now in the Browser and Ctrl+Alt+G its Create
# Filtered Deck; Ctrl+Alt combinations are AltGr on many non-English keyboards.
GENERATE_SHORTCUT = "Ctrl+Shift+Return"
# The old shortcut, kept for people used to it. The Browser can't have it: it's
# Anki's own Grade Now there.
LEGACY_GENERATE_SHORTCUT = "Ctrl+Shift+G"

# Notes read per query when sizing up a selection.
_NOTES_PER_QUERY = 1000


def _shortcut_label() -> str:
    # Qt maps Ctrl to Cmd on macOS.
    return "⌘⇧↩" if sys.platform == "darwin" else "Ctrl+Shift+Enter"


def _inputs(smart_field: SmartField) -> list[str]:
    """The lowercase fields a Smart Field reads."""
    settings = smart_field.settings
    if isinstance(settings, TTSSmartFieldSettings):
        return [settings.source_field_name.lower()]
    return get_prompt_fields(settings.prompt_text)


def fillable_smart_fields(
    values: dict[str, str], smart_fields: Sequence[SmartField], *, include_manual: bool
) -> set[str]:
    """The lowercase names of a note's empty Smart Fields that generation could
    fill. Generation skips a field whose inputs are all empty, so each must read
    a field with text, or one generation fills first. `values` maps lowercase
    field names to values; `include_manual` counts disabled Smart Fields, which
    generate only when targeted or feeding the target."""
    empty = {
        name: _inputs(smart_field)
        for smart_field in smart_fields
        if (name := smart_field.target_field_name.lower()) in values
        and not values[name]
        and (include_manual or smart_field.enabled)
    }

    if not empty:
        return set()
    has_text = {name for name, value in values.items() if html_to_text(value)}

    # Each pass adds the fields whose inputs the previous passes can fill.
    fillable: set[str] = set()
    while True:
        added = {
            name
            for name, inputs in empty.items()
            if name not in fillable
            and (not inputs or any(i in has_text or i in fillable for i in inputs))
        }
        if not added:
            return fillable
        fillable |= added


@dataclass(frozen=True)
class SelectionActions:
    """What a set of notes offers the generate banner. Only enabled Smart Fields
    count, since batch generation skips disabled ones."""

    note_count: int
    has_smart_fields: bool
    # Some note has an empty Smart Field...
    has_empty: bool
    # ...that generation could fill (`fillable_smart_fields`).
    can_generate: bool
    # Some note has a filled Smart Field.
    can_regenerate: bool


def note_actions(
    values: dict[str, str], smart_fields: Sequence[SmartField]
) -> SelectionActions:
    """What one note offers the generate banner. `values` maps lowercase field
    names to values; disabled Smart Fields are ignored."""
    enabled = [f for f in smart_fields if f.enabled]
    targets = {f.target_field_name.lower() for f in enabled} & set(values)
    return SelectionActions(
        note_count=1,
        has_smart_fields=bool(targets),
        has_empty=any(not values[name] for name in targets),
        can_generate=bool(fillable_smart_fields(values, enabled, include_manual=False)),
        can_regenerate=any(values[name] for name in targets),
    )


def selection_actions(card_ids: Sequence[int]) -> SelectionActions:
    """Sizes up selected cards for the banner. Each note resolves its Smart Fields
    by the same card as batch generation (`note_decks`)."""
    decks = note_decks(card_ids)
    if not mw or not mw.col or not mw.col.db:
        return SelectionActions(len(decks), False, False, False, False)
    db = mw.col.db

    enabled_by_type_and_deck: dict[tuple[int, int], list[SmartField]] = {}
    field_names_by_type: dict[int, list[str]] = {}
    has_smart_fields = has_empty = can_generate = can_regenerate = False

    # Read the notes' raw fields in chunks rather than loading each Note: a
    # selection can be the whole collection, and this runs on every selection
    # change. Stop once both buttons apply.
    note_ids = list(decks)
    for start in range(0, len(note_ids), _NOTES_PER_QUERY):
        chunk = note_ids[start : start + _NOTES_PER_QUERY]
        rows = db.all(f"select id, mid, flds from notes where id in {ids2str(chunk)}")
        for note_id, note_type_id, fields in rows:
            key = (note_type_id, decks[note_id])
            if key not in enabled_by_type_and_deck:
                enabled_by_type_and_deck[key] = [
                    smart_field
                    for smart_field in smart_field_service.get_smart_fields_for_note(
                        note_type_id, key[1], include_global=True
                    )
                    if smart_field.enabled
                ]
            smart_fields = enabled_by_type_and_deck[key]
            if not smart_fields:
                continue

            if note_type_id not in field_names_by_type:
                note_type = mw.col.models.get(note_type_id)
                field_names_by_type[note_type_id] = (
                    [field["name"].lower() for field in note_type["flds"]]
                    if note_type
                    else []
                )
            note = note_actions(
                dict(zip(field_names_by_type[note_type_id], fields.split("\x1f"))),
                smart_fields,
            )
            has_smart_fields = has_smart_fields or note.has_smart_fields
            has_empty = has_empty or note.has_empty
            can_generate = can_generate or note.can_generate
            can_regenerate = can_regenerate or note.can_regenerate
            if can_generate and can_regenerate:
                return SelectionActions(len(decks), True, True, True, True)

    return SelectionActions(
        len(decks), has_smart_fields, has_empty, can_generate, can_regenerate
    )


# Material Design "creation" (sparkles), the icon set Anki's editor uses.
_SPARKLE_PATH = "M19,1L17.74,3.75L15,5L17.74,6.26L19,9L20.25,6.26L23,5L20.25,3.75M9,4L6.5,9.5L1,12L6.5,14.5L9,20L11.5,14.5L17,12L11.5,9.5M19,15L17.74,17.74L15,19L17.74,20.25L19,23L20.25,20.25L23,19L20.25,17.74"


def _banner_style() -> str:
    # Smart Notes green: a faint tint for the band, solid on the button.
    band = "rgba(22, 163, 74, 0.07)"
    edge = "rgba(22, 163, 74, 0.30)"
    start = "#1fb257"
    end = "#16a34a"
    return f"""
        QFrame#{_BANNER_NAME} {{
            background: {band}; border: 1px solid {edge}; border-radius: 8px;
        }}
        QFrame#{_BANNER_NAME} QLabel {{ font-size: 14px; font-weight: 600; }}
        QFrame#{_BANNER_NAME} QPushButton {{ min-height: 30px; font-size: 14px; }}
        QFrame#{_BANNER_NAME} QPushButton#primary {{
            color: white; border: none; border-radius: 5px; font-weight: 600;
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {start}, stop:1 {end});
        }}
        QFrame#{_BANNER_NAME} QPushButton#primary:hover {{ background: {end}; }}
        QFrame#{_BANNER_NAME} QPushButton#primary:disabled {{
            background: rgba(22, 163, 74, 0.35); color: rgba(255, 255, 255, 0.85);
        }}
    """


def _sparkle_pixmap(size: int, color: str) -> QPixmap:
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="{_SPARKLE_PATH}"/></svg>'
    pixmap = QPixmap()
    pixmap.loadFromData(svg.encode(), "SVG")
    return pixmap.scaled(size, size)


class _ElidedLabel(QLabel):
    """One line of text that ends in "…" when it doesn't fit, so it never clips
    and never squeezes the buttons beside it. The full text is its tooltip."""

    def __init__(self) -> None:
        super().__init__()
        self._full_text = ""
        self.setMinimumWidth(0)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)

    def set_full_text(self, text: str) -> None:
        self._full_text = text
        self.setToolTip(text)
        self._elide()

    def resizeEvent(self, a0: Any) -> None:  # noqa: N802
        super().resizeEvent(a0)
        self._elide()

    def _elide(self) -> None:
        self.setText(
            self.fontMetrics().elidedText(
                self._full_text, Qt.TextElideMode.ElideRight, self.width()
            )
        )


def make_generate_banner(
    on_generate: Callable[[bool], None], *, generate_label: str
) -> QFrame:
    """A hidden banner with a generate-empty-fields button labelled
    `generate_label` and Regenerate all. `on_generate(overwrite_fields)` runs a
    button's generation; fill it in with `update_generate_banner`."""
    banner = QFrame()
    banner.setObjectName(_BANNER_NAME)
    banner.setStyleSheet(_banner_style())
    banner.hide()

    layout = QHBoxLayout(banner)
    layout.setContentsMargins(14, 8, 10, 8)
    layout.setSpacing(8)

    sparkle = QLabel()
    sparkle.setObjectName("sparkle")
    sparkle.setPixmap(_sparkle_pixmap(18, "#16a34a"))
    layout.addWidget(sparkle)

    summary = _ElidedLabel()
    summary.setObjectName("summary")
    # Takes the free space, so the buttons stay right-aligned at full size.
    layout.addWidget(summary, 1)

    generate = QPushButton(f" {generate_label}")
    generate.setObjectName("primary")
    generate.setIcon(QIcon(_sparkle_pixmap(32, "white")))
    generate.setIconSize(QSize(16, 16))
    generate.clicked.connect(lambda: on_generate(False))
    layout.addWidget(generate)

    regenerate = QPushButton(f"↻  {native_action_text('regenerate_all')}")
    regenerate.setObjectName("secondary")
    regenerate.clicked.connect(lambda: on_generate(True))
    layout.addWidget(regenerate)

    return banner


def update_generate_banner(
    banner: QFrame, summary: str, actions: SelectionActions, *, one_note: bool
) -> None:
    """Shows the banner with `summary` on the left (none when empty), enabling
    the buttons that apply, or hides it when the notes have no Smart Fields.
    `one_note` words the tooltips for a single note rather than a selection."""
    if not actions.has_smart_fields:
        banner.hide()
        return

    banner.findChild(QLabel, "sparkle").setVisible(bool(summary))
    banner.findChild(_ElidedLabel, "summary").set_full_text(summary)

    generate = banner.findChild(QPushButton, "primary")
    generate.setEnabled(actions.can_generate)
    if actions.can_generate:
        tip = native_action_text(
            "fill_note_tip" if one_note else "generate_empty_fields_tip"
        ).format(shortcut=_shortcut_label())
    elif actions.has_empty:
        tip = native_action_text("inputs_empty_tip")
    else:
        tip = native_action_text("all_filled_tip")
    generate.setToolTip(tip)

    regenerate = banner.findChild(QPushButton, "secondary")
    regenerate.setEnabled(actions.can_regenerate)
    if not actions.can_regenerate:
        tip = native_action_text("nothing_to_regenerate_tip")
    else:
        tip = native_action_text(
            "regenerate_note_tip" if one_note else "regenerate_all_tip"
        )
    regenerate.setToolTip(tip)
    banner.show()


def add_generate_banner(b: Browser, on_generate: Callable[[bool], None]) -> None:
    """Adds the generate banner above the Browser's table and editor."""
    banner = make_generate_banner(
        on_generate, generate_label=native_action_text("generate_empty_fields")
    )
    b.form.verticalLayout_3.insertWidget(0, banner)
    refresh_banner(b)


def refresh_banner(b: Browser) -> None:
    """Updates the Browser's banner for its selection."""
    banner: Optional[QFrame] = b.findChild(QFrame, _BANNER_NAME)
    # An edit saved as the Browser closes lands after its table is torn down.
    if not banner or getattr(b, "_closeEventHasCleanedUp", False):
        return

    actions = selection_actions(b.selected_cards())
    key = "notes_selected_one" if actions.note_count == 1 else "notes_selected_other"
    summary = native_action_text(key).format(count=actions.note_count)
    update_generate_banner(banner, summary, actions, one_note=False)


def generate_from_banner(b: Browser) -> bool:
    """Clicks the Browser banner's Generate empty fields, if it's showing and
    enabled. Returns whether it did."""
    banner: Optional[QFrame] = b.findChild(QFrame, _BANNER_NAME)
    generate = banner.findChild(QPushButton, "primary") if banner else None
    if not banner or not banner.isVisible() or not generate or not generate.isEnabled():
        return False
    generate.click()
    return True


def on_operation_did_execute(changes: OpChanges, handler: Optional[object]) -> None:
    """Refreshes the banner after an edit made in the Browser: the classic editor
    passes itself as the handler, the experimental one its window."""
    if not changes.note_text:
        return
    window = (
        handler
        if isinstance(handler, Browser)
        else getattr(handler, "parentWindow", None)
    )
    if isinstance(window, Browser):
        refresh_banner(window)


_EDITOR_CUES_JS = """
(() => {
  const { fields, command, generate, regenerate } = %s;
  // Material Design icons, the set Anki's editor uses: "creation" (sparkles) and "refresh".
  const SPARKLE_ICON = '<svg viewBox="0 0 24 24"><path d="M19,1L17.74,3.75L15,5L17.74,6.26L19,9L20.25,6.26L23,5L20.25,3.75M9,4L6.5,9.5L1,12L6.5,14.5L9,20L11.5,14.5L17,12L11.5,9.5M19,15L17.74,17.74L15,19L17.74,20.25L19,23L20.25,20.25L23,19L20.25,17.74"/></svg>';
  const REFRESH_ICON = '<svg viewBox="0 0 24 24"><path d="M17.65,6.35C16.2,4.9 14.21,4 12,4A8,8 0 0,0 4,12A8,8 0 0,0 12,20C15.73,20 18.84,17.45 19.73,14H17.65C16.83,16.33 14.61,18 12,18A6,6 0 0,1 6,12A6,6 0 0,1 12,6C13.66,6 15.14,6.69 16.22,7.78L13,11H20V4L17.65,6.35Z"/></svg>';
  if (!document.getElementById("sn-cue-style")) {
    const style = document.createElement("style");
    style.id = "sn-cue-style";
    // Anki styles every editor button, so reset it first.
    style.textContent = `
      /* Anki's own button look, sized to fit the label row; the green icon marks a Smart Field. */
      button.sn-gen {
        all: unset; display: inline-flex; align-items: center; align-self: center;
        gap: 3px; margin-inline-start: 12px; padding: 0 8px; border-radius: 5px;
        font-size: 13px; font-weight: 500; line-height: 18px; cursor: pointer;
        color: var(--fg); background: var(--button-bg);
        border: 1px solid var(--border); border-bottom-color: var(--shadow);
      }
      button.sn-gen:hover:enabled { border-color: var(--button-hover-border); }
      button.sn-gen:disabled { opacity: 0.45; cursor: default; }
      button.sn-gen svg { width: 14px; height: 14px; fill: #16a34a; }
      .night-mode button.sn-gen svg { fill: #4ade80; }
    `;
    document.head.appendChild(style);
  }

  // Svelte renders the fields after loadNote, so wait for them.
  const apply = (tries) => {
    document.querySelectorAll(".sn-cue").forEach((el) => el.remove());
    let missing = false;
    for (const field of fields) {
      const container = document.querySelector(
        `.field-container[data-index="${field.index}"]`
      );
      // Beside the collapse toggle rather than inside it, so a click doesn't collapse the field.
      const label = container?.querySelector(".collapse-label");
      if (!label) {
        missing = true;
        continue;
      }
      const button = document.createElement("button");
      button.className = "sn-cue sn-gen";
      button.tabIndex = -1;
      button.title = field.title;
      button.disabled = !field.enabled;
      button.innerHTML = field.empty ? SPARKLE_ICON : REFRESH_ICON;
      button.append(field.empty ? generate : regenerate);
      button.addEventListener("click", () => pycmd(`${command}:${field.index}`));
      label.after(button);
    }
    if (missing && tries > 0) setTimeout(() => apply(tries - 1), 50);
  };
  apply(20);
})();
"""


def editor_card(e: editor.Editor) -> Optional[Card]:
    """The editor's card, whose deck resolves its Smart Fields, holding the note
    as the editor last saved it. In the Add dialog it's an unsaved card in the
    deck chooser's deck. None without a note, and in the experimental editor's
    Add dialog, whose note only `with_editor_card` can read."""
    if not hasattr(e, "note"):
        # Anki 26.9's experimental Svelte editor (NewEditor) saves straight to
        # the collection and keeps only the note's id.
        nid = getattr(e, "nid", None)
        if not nid or not e.card or not mw or not mw.col:
            return None
        return mw.col.get_card(e.card.id)

    note = e.note
    if note is None:
        return None
    if e.card:
        return e.card

    card = note.ephemeral_card()
    parent = e.parentWindow
    if isinstance(parent, AddCards) and parent.deck_chooser.selected_deck_id:
        card.did = parent.deck_chooser.selected_deck_id
    return card


def _is_new_add(e: editor.Editor) -> bool:
    """Whether e is the experimental editor's Add dialog, whose unsaved note,
    note type and deck exist only in its webview."""
    return not hasattr(e, "note") and bool(getattr(e, "addMode", False))


# Reads the experimental Add dialog's note and chosen deck, and watches its
# note type and deck choosers, which tell Python nothing when they change.
_READ_ADD_PAGE_JS = """
(() => {
  const bar = document.querySelector(".top-bar");
  if (bar && !window.smartNotesWatchesChoosers) {
    window.smartNotesWatchesChoosers = true;
    new MutationObserver(() => pycmd("%s")).observe(bar, {
      subtree: true, childList: true, characterData: true,
    });
  }
  try {
    const deck = document.querySelector(".deck-chooser .chooser-button");
    return { info: getNoteInfo(), deck: deck ? deck.textContent.trim() : null };
  } catch {
    return null;
  }
})()
"""

# The pycmd the experimental Add dialog sends when its note type or deck changes.
EDITOR_CHANGED_COMMAND = "smartNotesEditorChanged"


def with_editor_card(e: editor.Editor, on_card: Callable[[Card], None]) -> None:
    """Calls `on_card` with `editor_card`, or in the experimental Add dialog
    with an unsaved card built from its page, once the page answers."""
    if not _is_new_add(e):
        card = editor_card(e)
        if card:
            on_card(card)
        return
    if not e.web:
        return

    def on_page(page: Optional[dict[str, Any]]) -> None:
        if not page or not page.get("info") or not mw or not mw.col:
            return
        col = mw.col
        info = page["info"]
        note_type = col.models.get(NotetypeId(int(info["mid"])))
        if not note_type:
            return
        note = Note(col, note_type)
        note.fields = list(info["fields"])
        card = note.ephemeral_card()

        # Deck names are unique, so the chooser's label names exactly one deck.
        deck_id = col.decks.id_for_name(page["deck"]) if page["deck"] else None
        if not deck_id:
            logger.debug(f"Add dialog deck {page['deck']!r} not found; using default")
            deck_id = col.default_deck_for_notetype(note_type["id"])
        if deck_id:
            card.did = deck_id
        on_card(card)

    e.web.evalWithCallback(_READ_ADD_PAGE_JS % EDITOR_CHANGED_COMMAND, on_page)


def _write_back_to_add_page(
    e: editor.Editor, note: Note, original_fields: list[str]
) -> None:
    """Puts generated values into the experimental Add dialog's page, keeping
    whatever the user typed meanwhile in the fields generation didn't touch."""
    generated: dict[int, str] = {
        index: value
        for index, (value, original) in enumerate(
            zip([note[name] for name in note.keys()], original_fields)  # noqa: SIM118
        )
        if value != original
    }

    def on_info(info: Optional[dict[str, Any]]) -> None:
        if not info or not e.web or not mw or not mw.col:
            return
        if int(info["mid"]) != note.mid:
            return
        current: list[str] = info["fields"]
        # A filled field that generation didn't write has changed: the user
        # edited what the results came from, or added the note and the page moved
        # on to the next one. Either way the results don't belong here.
        if any(
            original and i not in generated and current[i] != original
            for i, original in enumerate(original_fields)
        ):
            return
        # Only fill fields the user hasn't touched since generation started.
        values = [
            generated[i] if i in generated and value == original_fields[i] else value
            for i, value in enumerate(current)
        ]
        # The page takes media references escaped, as Anki's own loadNote does.
        escaped = [mw.col.media.escape_media_filenames(v) for v in values]
        e.web.eval(f"setFields({json.dumps(note.keys())}, {json.dumps(escaped)});")

    if generated and e.web:
        e.web.evalWithCallback(
            "(() => { try { return getNoteInfo(); } catch { return null; } })()",
            on_info,
        )


def show_generated_note(
    e: editor.Editor, note: Note, original_fields: list[str]
) -> None:
    """Shows a generated note in the editor if it's still on that note, and
    redraws the Browser's preview and banner. `original_fields` are the note's
    values before generation."""
    if _is_new_add(e):
        _write_back_to_add_page(e, note, original_fields)
        return
    if hasattr(e, "note"):
        shown = e.note
        if shown is None or not (shown is note or (note.id and shown.id == note.id)):
            return
        # Don't note.load() it: that runs before the queued save and would wipe
        # values not yet written. The card's note is usually editor.note, but the
        # browser's previewer swaps the card's cached note for a fresh copy.
        e.note = note
        e.loadNote()
    else:
        if not e.web or getattr(e, "nid", None) != note.id:
            return
        # Reloads from the collection and fires editor_did_load_note.
        e.set_note(note)

    parent = e.parentWindow
    if isinstance(parent, Browser):
        if getattr(parent, "_previewer", None):
            parent._previewer.render_card()  # type: ignore
        refresh_banner(parent)


def _add_dialogs() -> tuple[type, ...]:
    new_add_cards = getattr(aqt.addcards, "NewAddCards", None)
    return (AddCards, new_add_cards) if new_add_cards else (AddCards,)


def is_editor(obj: Any) -> bool:
    """Whether obj is one of Anki's editors, classic or experimental."""
    return isinstance(obj, editor.Editor) or type(obj).__name__ == "NewEditor"


def _dialog_banner(e: editor.Editor) -> Optional[QFrame]:
    """The banner `add_dialog_banner` gave the editor, if any."""
    return getattr(e, _BANNER_NAME, None)


def editor_busy(e: editor.Editor) -> bool:
    """Whether a generation started from this editor is still running."""
    return getattr(e, "_smart_notes_busy", False)


def set_editor_busy(e: editor.Editor, busy: bool) -> None:
    """Marks a generation from this editor as running or done. While it runs, the
    dialog's banner is disabled and further clicks and shortcuts are ignored, so
    a double-click can't pay for the same generation twice."""
    e._smart_notes_busy = busy  # type: ignore
    banner = _dialog_banner(e)
    if banner:
        banner.setEnabled(not busy)
    if not busy:
        refresh_editor(e)


def add_dialog_banner(e: editor.Editor, on_generate: Callable[[bool], None]) -> None:
    """Adds the generate banner above the editor in the Add and Edit dialogs.
    The experimental editor's Add dialog has its Type/Deck row inside the
    webview, so there the banner sits above that row."""
    parent = e.parentWindow
    edit_dialogs = tuple(
        cls
        for cls in (EditCurrent, getattr(aqt.editcurrent, "NewEditCurrent", None))
        if cls
    )
    if isinstance(parent, _add_dialogs()):
        label = native_action_text("generate_now")
    elif isinstance(parent, edit_dialogs):
        label = native_action_text("generate_empty_fields")
    else:
        return

    parent_widget = e.widget.parentWidget()
    layout = parent_widget.layout() if parent_widget else None
    if not isinstance(layout, QBoxLayout):
        return
    banner = make_generate_banner(on_generate, generate_label=label)
    layout.insertWidget(layout.indexOf(e.widget), banner)
    setattr(e, _BANNER_NAME, banner)


def schedule_editor_refresh(e: editor.Editor) -> None:
    """Refreshes the editor's buttons once typing pauses. Runs after the editor
    has taken in the edit that triggered it."""
    timer: Optional[QTimer] = getattr(e, "_smart_notes_refresh_timer", None)
    if timer is None:
        timer = QTimer(e.widget)
        timer.setSingleShot(True)
        timer.setInterval(300)
        timer.timeout.connect(lambda: refresh_editor(e))
        e._smart_notes_refresh_timer = timer  # type: ignore
    timer.start()


def refresh_editor(e: editor.Editor) -> None:
    """Redraws the editor's field buttons and its dialog's banner for the note
    as the editor shows it, unsaved edits included."""
    if not e.web or not mw or not mw.col:
        return

    if _is_new_add(e):
        with_editor_card(
            e,
            lambda card: _draw_editor(
                e, card, card.note().mid, card.note().keys(), card.note().fields
            ),
        )
        return

    card = editor_card(e)
    if not card:
        return

    if hasattr(e, "note") and e.note is not None:
        _draw_editor(e, card, e.note.mid, e.note.keys(), e.note.fields)
        return

    # The experimental editor holds unsaved edits in its webview. Call its
    # getNoteInfo() directly: Anki's get_note_info() wrapper throws when the
    # page has no note loaded yet, which happens while it's still loading.
    def on_note_info(info: Optional[dict[str, Any]]) -> None:
        if not info or not mw or not mw.col or not e.web:
            return
        # The page sends ids as strings.
        mid = NotetypeId(int(info["mid"]))
        note_type = mw.col.models.get(mid)
        if note_type and info["id"] is not None and int(info["id"]) == card.nid:
            names = [field["name"] for field in note_type["flds"]]
            _draw_editor(e, card, mid, names, info["fields"])

    e.web.evalWithCallback(
        "(() => { try { return getNoteInfo(); } catch { return null; } })()",
        on_note_info,
    )


def _draw_editor(
    e: editor.Editor,
    card: Card,
    note_type_id: int,
    names: list[str],
    values: list[str],
) -> None:
    if not e.web:
        return
    smart_fields = smart_field_service.get_smart_fields_for_note(
        note_type_id, card.did, include_global=True
    )
    smart_field_names = {f.target_field_name.lower() for f in smart_fields}
    values_by_name = {name.lower(): value for name, value in zip(names, values)}

    # Field buttons. A clicked field also fills its empty inputs, disabled or not.
    fillable = fillable_smart_fields(values_by_name, smart_fields, include_manual=True)
    fields: list[dict[str, Any]] = []
    for index, (name, value) in enumerate(zip(names, values)):
        if name.lower() not in smart_field_names:
            continue
        if value:
            enabled = True
            title = native_action_text("regenerate_field_tip").format(field=name)
        else:
            enabled = name.lower() in fillable
            title = (
                native_action_text("generate_field_tip").format(field=name)
                if enabled
                else native_action_text("field_inputs_empty_tip")
            )
        fields.append(
            {"index": index, "empty": not value, "enabled": enabled, "title": title}
        )
    payload: dict[str, Any] = {
        "fields": fields,
        "command": GENERATE_FIELD_COMMAND,
        "generate": native_action_text("generate"),
        "regenerate": native_action_text("regenerate"),
    }
    e.web.eval(_EDITOR_CUES_JS % json.dumps(payload))

    # The Add or Edit dialog's banner.
    banner = _dialog_banner(e)
    if banner:
        summary = (
            native_action_text("generates_on_add")
            if isinstance(e.parentWindow, _add_dialogs()) and config.generate_on_add
            else ""
        )
        actions = note_actions(values_by_name, smart_fields)
        update_generate_banner(banner, summary, actions, one_note=True)


def on_add_cards_did_change_deck(_: int) -> None:
    """Refreshes the Add dialog, whose Smart Fields resolve by its deck."""
    for window in QApplication.topLevelWidgets():
        if isinstance(window, AddCards):
            refresh_editor(window.editor)
