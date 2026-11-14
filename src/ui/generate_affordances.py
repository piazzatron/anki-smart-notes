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
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any, Optional, Union

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
    QColor,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QIcon,
    QLabel,
    QPixmap,
    QPushButton,
    QSize,
    QSizePolicy,
    Qt,
    QTimer,
    QVariantAnimation,
    sip,
)
from aqt.theme import theme_manager

from ..config import config
from ..dag import generate_fields_dag
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
    # For one note, how many fields each button fills (0 shows no count).
    generate_count: int = 0
    regenerate_count: int = 0


def note_actions(
    values: dict[str, str], smart_fields: Sequence[SmartField]
) -> SelectionActions:
    """What one note offers the generate banner. `values` maps lowercase field
    names to values; disabled Smart Fields are ignored."""
    enabled = [f for f in smart_fields if f.enabled]
    targets = {f.target_field_name.lower() for f in enabled} & set(values)
    fillable = fillable_smart_fields(values, enabled, include_manual=False)
    return SelectionActions(
        note_count=1,
        has_smart_fields=bool(targets),
        has_empty=any(not values[name] for name in targets),
        can_generate=bool(fillable),
        can_regenerate=any(values[name] for name in targets),
        generate_count=len(fillable),
        regenerate_count=len(targets),
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


# Sized from the editor toolbar's buttons (Fields..., Cards..., Preview: 15px
# text, 5px corners), with a little more room.
_BUTTON_PADDING = 12
_BUTTON_HEIGHT = 28


def _sparkle_color() -> str:
    """The sparkle's yellow, like the ✨ emoji: the one touch of colour on the
    plain buttons."""
    return "#fbbf24" if theme_manager.night_mode else "#f59e0b"


def _banner_style() -> str:
    # Both buttons are styled in full rather than left to the platform's native
    # button, which has its own height and padding on macOS and wouldn't match.
    if theme_manager.night_mode:
        # A step lighter than the #363636 card, with a light edge, so the
        # buttons stand off it.
        fg, button, border, hover = "#f4f4f5", "#4a4a4e", "#5e5e63", "#555559"
        pressed = "#3e3e42"
        disabled_bg, disabled_fg = (
            "rgba(255, 255, 255, 0.06)",
            "rgba(255, 255, 255, 0.35)",
        )
    else:
        fg, button, border, hover = "#1d1d1f", "#fcfcfc", "#c4c4c4", "#f2f2f2"
        pressed = "#e4e4e6"
        disabled_bg, disabled_fg = "rgba(0, 0, 0, 0.05)", "rgba(0, 0, 0, 0.35)"
    # Anki's own container look, as on the deck list: its raised canvas colour
    # and subtle border (the drop shadow is set in `make_generate_banner`).
    muted = "#a1a1a6" if theme_manager.night_mode else "#6b6b70"
    card, card_border = (
        ("#363636", "#252525") if theme_manager.night_mode else ("white", "#e4e4e4")
    )
    return f"""
        QFrame#{_BANNER_NAME} {{
            background: {card}; border: 1px solid {card_border}; border-radius: 12px;
        }}
        QFrame#{_BANNER_NAME} QLabel {{
            font-size: 14px; color: {muted};
            /* Mirrors the buttons' inner padding on the left. */
            padding-right: {_BUTTON_PADDING}px;
        }}
        QFrame#{_BANNER_NAME} QPushButton {{
            font-size: 15px; padding: 0 {_BUTTON_PADDING}px; margin: 0; border-radius: 5px;
            color: {fg}; background: {button}; border: 1px solid {border};
        }}
        QFrame#{_BANNER_NAME} QPushButton:hover {{ background: {hover}; }}
        QFrame#{_BANNER_NAME} QPushButton:pressed {{ background: {pressed}; }}
        QFrame#{_BANNER_NAME} QPushButton:disabled,
        QFrame#{_BANNER_NAME} QPushButton#primary:disabled {{
            color: {disabled_fg}; background: {disabled_bg}; border: 1px solid transparent;
        }}
        QFrame#{_BANNER_NAME} QPushButton[working="true"]:disabled,
        QFrame#{_BANNER_NAME} QPushButton#primary[working="true"]:disabled {{
            color: {fg}; background: {button}; border: 1px solid {border};
        }}
    """


# Material Design "refresh", for Regenerate. Its shape fills less of the 24px
# square than the sparkle's, so it's drawn from a tighter view box to match.
_REFRESH_VIEW_BOX = "2 2 20 20"
_REFRESH_PATH = "M17.65,6.35C16.2,4.9 14.21,4 12,4A8,8 0 0,0 4,12A8,8 0 0,0 12,20C15.73,20 18.84,17.45 19.73,14H17.65C16.83,16.33 14.61,18 12,18A6,6 0 0,1 6,12A6,6 0 0,1 12,6C13.66,6 15.14,6.69 16.22,7.78L13,11H20V4L17.65,6.35Z"


def _action_icons(path: str, view_box: str = "0 0 24 24") -> tuple[QIcon, QIcon]:
    """A button's icon: yellow while it's clickable and grey when disabled, plus
    the one it shows while generating, yellow though the button is disabled."""
    yellow = _sparkle_color()
    # macOS doesn't grey a coloured icon on a disabled button itself.
    grey = "#8a8a8e" if theme_manager.night_mode else "#a1a1a6"
    icon = QIcon(_icon_pixmap(path, 14, yellow, view_box))
    icon.addPixmap(_icon_pixmap(path, 14, grey, view_box), QIcon.Mode.Disabled)
    working = QIcon(_icon_pixmap(path, 14, yellow, view_box))
    working.addPixmap(_icon_pixmap(path, 14, yellow, view_box), QIcon.Mode.Disabled)
    return icon, working


# Icons are drawn at this many times their size and marked as such, so they stay
# sharp on any screen (macOS Retina is 2x, some Windows displays 3x).
_ICON_SCALE = 4


def _icon_pixmap(
    path: str, size: int, color: str, view_box: str = "0 0 24 24"
) -> QPixmap:
    """A `size`-point icon drawn straight from its vector path at `_ICON_SCALE`
    times that, never scaled up from a smaller bitmap."""
    pixels = size * _ICON_SCALE
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{pixels}" height="{pixels}"'
        f' viewBox="{view_box}"><path fill="{color}" d="{path}"/></svg>'
    )
    pixmap = QPixmap()
    pixmap.loadFromData(svg.encode(), "SVG")
    pixmap.setDevicePixelRatio(_ICON_SCALE)
    return pixmap


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
    on_generate: Callable[[bool], None],
    *,
    generate_label: str,
) -> QFrame:
    """A hidden banner with a generate-empty-fields button labelled
    `generate_label` and Regenerate all fields. `on_generate(overwrite_fields)` runs a
    button's generation; fill it in with `update_generate_banner`."""
    banner = QFrame()
    banner.setObjectName(_BANNER_NAME)
    regenerate_label = native_action_text("regenerate_all_fields")
    banner.setProperty("generate_label", generate_label)
    banner.setProperty("regenerate_label", regenerate_label)
    banner.setStyleSheet(_banner_style())
    # The soft shadow of Anki's deck list card; stylesheets can't draw one.
    shadow = QGraphicsDropShadowEffect(banner)
    # Faint in dark mode, where a dark shadow on a dark window reads as a halo.
    shadow.setBlurRadius(4 if theme_manager.night_mode else 6)
    shadow.setOffset(0, 1)
    shadow.setColor(QColor(0, 0, 0, 45 if theme_manager.night_mode else 40))
    banner.setGraphicsEffect(shadow)
    banner.hide()

    layout = QHBoxLayout(banner)
    # The same padding on every side.
    layout.setContentsMargins(6, 6, 6, 6)
    layout.setSpacing(8)

    generate = QPushButton(f" {generate_label}")
    generate.setObjectName("primary")
    icon, working_icon = _action_icons(_SPARKLE_PATH)
    generate.setIcon(icon)
    generate.setProperty("normal_icon", icon)
    generate.setProperty("working_icon", working_icon)
    generate.setIconSize(QSize(14, 14))
    generate.setFixedHeight(_BUTTON_HEIGHT)
    generate.clicked.connect(lambda: on_generate(False))
    layout.addWidget(generate)

    regenerate = QPushButton(f" {regenerate_label}")
    regenerate.setObjectName("secondary")
    icon, working_icon = _action_icons(_REFRESH_PATH, _REFRESH_VIEW_BOX)
    regenerate.setIcon(icon)
    regenerate.setProperty("normal_icon", icon)
    regenerate.setProperty("working_icon", working_icon)
    regenerate.setIconSize(QSize(14, 14))
    regenerate.setFixedHeight(_BUTTON_HEIGHT)
    regenerate.clicked.connect(lambda: on_generate(True))
    layout.addWidget(regenerate)

    # The buttons come first; the text, secondary, takes the rest of the row,
    # right-aligned.
    summary = _ElidedLabel()
    summary.setObjectName("summary")
    summary.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    layout.addWidget(summary, 1)

    return banner


def _set_button_enabled(button: QPushButton, enabled: bool) -> None:
    """Enables or disables a banner button, with the cursor saying which, as on
    the web app's buttons."""
    button.setEnabled(enabled)
    button.setCursor(
        Qt.CursorShape.PointingHandCursor if enabled else Qt.CursorShape.ForbiddenCursor
    )


def update_generate_banner(
    banner: QFrame, summary: str, actions: SelectionActions, *, one_note: bool
) -> None:
    """Shows the banner with `summary` on the left (none when empty), enabling
    the buttons that apply, or hides it when the notes have no Smart Fields.
    `one_note` words the tooltips for a single note rather than a selection."""
    if not actions.has_smart_fields:
        banner.hide()
        return

    banner.findChild(_ElidedLabel, "summary").set_full_text(summary)

    generate = banner.findChild(QPushButton, "primary")
    _set_button_enabled(generate, actions.can_generate)
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
    _set_button_enabled(regenerate, actions.can_regenerate)
    if not actions.can_regenerate:
        tip = native_action_text("nothing_to_regenerate_tip")
    else:
        tip = native_action_text(
            "regenerate_note_tip" if one_note else "regenerate_all_tip"
        )
    regenerate.setToolTip(tip)

    # For one note the labels count the fields each fills: "(3)", none for 0.
    # A running generation's animated label is left alone.
    for button, label_key, count in (
        (generate, "generate_label", actions.generate_count),
        (regenerate, "regenerate_label", actions.regenerate_count),
    ):
        if not button.property("working"):
            text = f" {banner.property(label_key)}"
            _fix_width(
                button,
                [text, f"{text} ({count})", f" {native_action_text('generating')}..."],
            )
            button.setText(f"{text} ({count})" if count else text)
    banner.show()


def _fix_width(button: QPushButton, texts: list[str]) -> None:
    """Fixes the button at the width of its widest label, with the text
    left-aligned, so clicking it (Generating, then a new count) never moves it."""
    current = button.text()
    widths = []
    for text in texts:
        button.setText(text)
        widths.append(button.sizeHint().width())
    button.setText(current)
    button.setFixedWidth(max(widths))


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
    # One note gets the banner in the editor pane instead.
    if actions.note_count < 2:
        banner.hide()
        return
    summary = native_action_text("notes_selected").format(count=actions.note_count)
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
  const { fields, command, generate, regenerate, generating } = %s;
  // Material Design icons, the set Anki's editor uses: "creation" (sparkles) and "refresh".
  const SPARKLE_ICON = '<svg viewBox="0 0 24 24"><path d="M19,1L17.74,3.75L15,5L17.74,6.26L19,9L20.25,6.26L23,5L20.25,3.75M9,4L6.5,9.5L1,12L6.5,14.5L9,20L11.5,14.5L17,12L11.5,9.5M19,15L17.74,17.74L15,19L17.74,20.25L19,23L20.25,20.25L23,19L20.25,17.74"/></svg>';
  const REFRESH_ICON = '<svg viewBox="2 2 20 20"><path d="M17.65,6.35C16.2,4.9 14.21,4 12,4A8,8 0 0,0 4,12A8,8 0 0,0 12,20C15.73,20 18.84,17.45 19.73,14H17.65C16.83,16.33 14.61,18 12,18A6,6 0 0,1 6,12A6,6 0 0,1 12,6C13.66,6 15.14,6.69 16.22,7.78L13,11H20V4L17.65,6.35Z"/></svg>';
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
      /* In dark mode Anki's button colours sit too close to the editor's. */
      .night-mode button.sn-gen { background: #45454a; border-color: #5e5e63; }
      .night-mode button.sn-gen:hover:enabled { background: #505055; border-color: #6e6e74; }
      /* Pressed: sinks a little, like Anki's own buttons. */
      button.sn-gen:active:enabled {
        transform: translateY(1px); filter: brightness(0.9);
        box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.18);
      }
      button.sn-gen:disabled { opacity: 0.45; cursor: not-allowed; }
      /* Generating: full strength, with dots that count up while it runs. */
      button.sn-gen.sn-working:disabled { opacity: 1; cursor: progress; }
      /* Draws the eye when the first-field guide opens the Browser here. */
      button.sn-gen.sn-pulse { animation: sn-pulse 1s ease-in-out 3; }
      @keyframes sn-pulse {
        0%%, 100%% { box-shadow: 0 0 0 0 rgba(245, 158, 11, 0); }
        50%% { box-shadow: 0 0 0 4px rgba(245, 158, 11, 0.45); }
      }
      .sn-labels { display: inline-grid; justify-items: center; }
      .sn-labels > .sn-label { grid-area: 1 / 1; display: inline-flex; align-items: center; gap: 3px; }
      .sn-labels > .sn-hidden { visibility: hidden; }
      .sn-dots { display: inline-block; width: 1.1em; text-align: start; margin-inline-start: -3px; }
      .sn-dots::after { content: ""; animation: sn-dots 1.2s steps(1) infinite; }
      @keyframes sn-dots {
        0%% { content: ""; } 25%% { content: "."; } 50%% { content: ".."; } 75%% { content: "..."; }
      }
      /* Action icons are yellow, like the ✨ emoji, while they're clickable. */
      button.sn-gen svg { width: 14px; height: 14px; fill: #f59e0b; }
      .night-mode button.sn-gen svg { fill: #fbbf24; }
      button.sn-gen:disabled:not(.sn-working) svg { fill: var(--fg-subtle); }
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
      button.disabled = !field.enabled || field.working;
      const icon = field.empty ? SPARKLE_ICON : REFRESH_ICON;
      if (field.working) button.classList.add("sn-working");
      // Redraws restart the pulse where it was, so it plays through once.
      if (field.pulse !== null) {
        button.classList.add("sn-pulse");
        button.style.animationDelay = `-${field.pulse}ms`;
      }
      // Every label the button can show sits in one grid cell, only the current
      // one visible, so the button is always as wide as the widest and never
      // changes width when clicked. Each carries its icon, so both centre together.
      const labels = document.createElement("span");
      labels.className = "sn-labels";
      const shown = field.working ? generating : field.empty ? generate : regenerate;
      for (const [text, labelIcon] of [
        [generate, SPARKLE_ICON],
        [regenerate, REFRESH_ICON],
        [generating, icon],
      ]) {
        const label = document.createElement("span");
        label.className = "sn-label";
        label.innerHTML = labelIcon;
        label.append(text);
        if (text === generating) {
          const dots = document.createElement("span");
          dots.className = "sn-dots";
          label.append(dots);
        }
        if (text !== shown) label.classList.add("sn-hidden");
        labels.append(label);
      }
      button.append(labels);
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
    """The banner `add_dialog_banner` gave the editor, if any. None once its
    window has closed, which a generation can outlive."""
    banner = getattr(e, _BANNER_NAME, None)
    return None if banner is None or sip.isdeleted(banner) else banner


def editor_busy(e: editor.Editor) -> bool:
    """Whether a generation started from this editor is still running."""
    return getattr(e, "_smart_notes_busy", False)


# What a running generation fills: "empty" Smart Fields, "all" of them, or the
# indices of the fields a field button regenerates.
Working = Union[str, frozenset[int], None]


def fields_regenerated_with(card: Card, target_field: str) -> frozenset[int]:
    """The indices of the fields a field button's generation of `target_field`
    regenerates: the field itself and, when it's filled, the Smart Fields that
    depend on it (as the processor's graph cascades), short of manual ones and
    anything only reachable through them, which keep their values."""
    note = card.note()
    smart_fields = smart_field_service.get_smart_fields_for_note(
        note.mid, card.did, include_global=True
    )
    dag = generate_fields_dag(
        note, smart_fields, overwrite_fields=False, target_field=target_field
    )
    reached = {target_field.lower()}
    explore = [dag[target_field.lower()]] if target_field.lower() in dag else []
    while explore:
        for node in explore.pop().out_nodes:
            if node.field in dag and node.field not in reached and not node.manual:
                reached.add(node.field)
                explore.append(node)
    names = [name.lower() for name in note.keys()]  # noqa: SIM118
    return frozenset(names.index(field) for field in reached if field in names)


def set_editor_busy(e: editor.Editor, busy: bool, working: Working = None) -> None:
    """Marks a generation from this editor as running or done, filling `working`.
    While it runs,
    those fields' buttons and the banner's button show Generating with moving
    dots, the other buttons are disabled, and further clicks and shortcuts are
    ignored, so a double-click can't pay for the same generation twice."""
    e._smart_notes_busy = busy  # type: ignore
    e._smart_notes_working = working if busy else None  # type: ignore
    banner = _dialog_banner(e)
    if banner:
        _animate_banner(banner, e._smart_notes_working)  # type: ignore
    refresh_editor(e)


def pulse_editor(e: editor.Editor, field_name: str) -> None:
    """Pulses the banner and `field_name`'s button the next time the editor
    shows a note with that Smart Field, to show where generating happens."""
    e._smart_notes_pulse = field_name.lower()  # type: ignore


def _pulse_banner(banner: QFrame) -> None:
    """Turns the banner's shadow into an amber glow that pulses three times,
    then puts the shadow back."""
    shadow = banner.graphicsEffect()
    if not isinstance(shadow, QGraphicsDropShadowEffect):
        return
    blur, offset, color = shadow.blurRadius(), shadow.offset(), shadow.color()
    amber = QColor(_sparkle_color())

    def step(value: Any) -> None:
        # 0 → 1 → 0 each loop.
        strength = 1 - abs(1 - 2 * float(value))
        amber.setAlphaF(0.8 * strength)
        shadow.setColor(amber)
        shadow.setBlurRadius(6 + 18 * strength)
        shadow.setOffset(0, 0)

    def restore() -> None:
        shadow.setBlurRadius(blur)
        shadow.setOffset(offset)
        shadow.setColor(color)

    animation = QVariantAnimation(banner)
    animation.setStartValue(0.0)
    animation.setEndValue(1.0)
    animation.setDuration(1000)
    animation.setLoopCount(3)
    animation.valueChanged.connect(step)
    animation.finished.connect(restore)
    animation.start(QVariantAnimation.DeletionPolicy.DeleteWhenStopped)


def _banner_buttons(banner: QFrame) -> tuple[QPushButton, QPushButton]:
    return (
        banner.findChild(QPushButton, "primary"),
        banner.findChild(QPushButton, "secondary"),
    )


def _show_banner_working(banner: QFrame, working: Working) -> None:
    """While a generation runs, disables both buttons (the working one keeps its
    colours through its `working` property), after the banner's usual update."""
    generate, regenerate = _banner_buttons(banner)
    for button, is_working in (
        (generate, working == "empty"),
        (regenerate, working == "all"),
    ):
        if working is not None:
            _set_button_enabled(button, False)
        if is_working:
            button.setCursor(Qt.CursorShape.BusyCursor)
        if button.property("working") != is_working:
            button.setProperty("working", is_working)
            # A changed property only restyles once the style is reapplied.
            style = button.style()
            if style:
                style.unpolish(button)
                style.polish(button)
        # Its icon stays yellow while it works, though it's disabled then.
        button.setIcon(button.property("working_icon" if is_working else "normal_icon"))


def _animate_banner(banner: QFrame, working: Working) -> None:
    """Counts dots on the working button's Generating label, or puts the labels
    back when nothing runs."""
    timer: Optional[QTimer] = getattr(banner, "_smart_notes_timer", None)
    if timer:
        timer.stop()
    generate, regenerate = _banner_buttons(banner)
    for button, label in (
        (generate, f" {banner.property('generate_label')}"),
        (regenerate, f" {banner.property('regenerate_label')}"),
    ):
        button.setText(label)
        button.setStyleSheet("")
    _show_banner_working(banner, working)
    if working not in ("empty", "all"):
        return

    # The label is left-aligned where "Generating..." would sit centred, so the
    # counting dots move neither the text nor the icon.
    button = generate if working == "empty" else regenerate
    base = f" {native_action_text('generating')}"
    button.setText(base + "...")
    left = (button.width() - button.sizeHint().width()) // 2 + _BUTTON_PADDING
    button.setStyleSheet(f"text-align: left; padding-left: {left}px;")
    count = [0]

    def tick() -> None:
        count[0] = (count[0] + 1) % 4
        button.setText(base + "." * count[0])

    timer = QTimer(banner)
    timer.timeout.connect(tick)
    timer.start(300)
    tick()
    banner._smart_notes_timer = timer  # type: ignore


def add_dialog_banner(e: editor.Editor, on_generate: Callable[[bool], None]) -> None:
    """Adds the one-note generate banner above the editor: in the Add and Edit
    dialogs, and in the Browser's editor pane (the Browser's own banner is for
    several notes). The experimental editor's Add dialog has its Type/Deck row
    inside the webview, so there the banner sits above that row."""
    parent = e.parentWindow
    edit_dialogs = tuple(
        cls
        for cls in (EditCurrent, getattr(aqt.editcurrent, "NewEditCurrent", None))
        if cls
    )
    if isinstance(parent, _add_dialogs()):
        label = native_action_text("generate_now")
    elif isinstance(parent, (*edit_dialogs, Browser)):
        label = native_action_text("generate_empty_fields")
    else:
        return

    banner = make_generate_banner(
        on_generate,
        generate_label=label,
    )
    if isinstance(parent, Browser):
        # The editor sits in a nested row of the pane, so go to the pane's top.
        layout = parent.form.verticalLayout
        index = 0
        banner.setStyleSheet(
            banner.styleSheet() + f"QFrame#{_BANNER_NAME} {{ margin: 6px 4px; }}"
        )
    else:
        parent_widget = e.widget.parentWidget()
        layout = parent_widget.layout() if parent_widget else None
        if not isinstance(layout, QBoxLayout):
            return
        index = layout.indexOf(e.widget)
    layout.insertWidget(index, banner)
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
    # While a generation runs, its fields show Generating and the rest wait.
    working = getattr(e, "_smart_notes_working", None)
    # A pulse plays for its 3 seconds from the first draw of a note with the field.
    pulse_field = getattr(e, "_smart_notes_pulse", None)
    pulse_start: Optional[float] = getattr(e, "_smart_notes_pulse_start", None)
    names_lower = [name.lower() for name in names]
    if pulse_field in names_lower and pulse_start is None:
        pulse_start = time.monotonic()
        e._smart_notes_pulse_start = pulse_start  # type: ignore
        banner_pulse = True
    else:
        banner_pulse = False
    pulse_ms = (
        int((time.monotonic() - pulse_start) * 1000)
        if pulse_start is not None
        else None
    )
    if pulse_ms is not None and pulse_ms > 3000:
        e._smart_notes_pulse = e._smart_notes_pulse_start = None  # type: ignore
        pulse_ms = None
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
        is_working = (
            (isinstance(working, frozenset) and index in working)
            or working == "all"
            or (working == "empty" and not value and name.lower() in fillable)
        )
        fields.append(
            {
                "index": index,
                "empty": not value,
                "enabled": enabled and working is None,
                "working": is_working,
                "pulse": pulse_ms if name.lower() == pulse_field else None,
                "title": title,
            }
        )
    payload: dict[str, Any] = {
        "fields": fields,
        "command": GENERATE_FIELD_COMMAND,
        "generate": native_action_text("generate"),
        "regenerate": native_action_text("regenerate"),
        "generating": native_action_text("generating"),
    }
    e.web.eval(_EDITOR_CUES_JS % json.dumps(payload))

    # The Add or Edit dialog's banner.
    banner = _dialog_banner(e)
    if banner and banner_pulse:
        _pulse_banner(banner)
    if banner:
        summary = (
            native_action_text("generates_on_add")
            if isinstance(e.parentWindow, _add_dialogs()) and config.generate_on_add
            else ""
        )
        actions = note_actions(values_by_name, smart_fields)
        update_generate_banner(banner, summary, actions, one_note=True)
        _show_banner_working(banner, working)


def on_add_cards_did_change_deck(_: int) -> None:
    """Refreshes the Add dialog, whose Smart Fields resolve by its deck."""
    for window in QApplication.topLevelWidgets():
        if isinstance(window, AddCards):
            refresh_editor(window.editor)
