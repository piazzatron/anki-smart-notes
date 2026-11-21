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

# Development-only local-server commands that let tooling see and click Anki's
# native widgets, so scripted checks (`cli/sn qt`) can drive the Qt UI (the
# generate banner, dialogs) like a user. The release build leaves this module out.

from collections.abc import Callable
from typing import Any, Optional

from anki import lang
from aqt import mw
from aqt.qt import (
    QAbstractButton,
    QAction,
    QApplication,
    QMessageBox,
    QPoint,
    QTimer,
    QWidget,
)


def _window_title(widget: QWidget) -> str:
    window = widget.window()
    return window.windowTitle() if window else ""


def _describe(widget: QWidget) -> dict[str, Any]:
    rect = widget.rect()
    top_left = widget.mapToGlobal(rect.topLeft())
    # Banner buttons keep their tooltip on a wrapper so it shows while disabled.
    parent = widget.parentWidget()
    tooltip = widget.toolTip() or (parent.toolTip() if parent else "")
    text = widget.text() if isinstance(widget, (QAbstractButton, QMessageBox)) else ""
    return {
        "name": widget.objectName(),
        "class": type(widget).__name__,
        "text": text.strip(),
        "enabled": widget.isEnabled(),
        "visible": widget.isVisible(),
        "tooltip": tooltip,
        "window": _window_title(widget),
        "geometry": [top_left.x(), top_left.y(), rect.width(), rect.height()],
        "clipped": isinstance(widget, QAbstractButton) and _clipped(widget),
    }


def _clipped(button: QAbstractButton) -> bool:
    """Whether part of the button's label is cut off: the button is narrower
    than its label needs, or a parent too narrow for it hides part of it."""
    if button.sizeHint().width() > button.width():
        return True
    shown = button.rect()
    parent = button.parentWidget()
    while parent:
        offset = button.mapTo(parent, QPoint(0, 0))
        shown = shown.intersected(parent.rect().translated(-offset))
        parent = parent.parentWidget()
    return shown.width() < button.width()


def _visible_widgets() -> list[QWidget]:
    """Every visible window, and the visible buttons inside each."""
    windows = [w for w in QApplication.topLevelWidgets() if w.isVisible()]
    buttons = [
        b
        for w in windows
        for b in w.findChildren(QAbstractButton)
        if b.isVisible() and (b.objectName() or b.text().strip())
    ]
    return [*windows, *buttons]


def list_widgets(payload: dict[str, Any]) -> dict[str, Any]:
    return {"widgets": [_describe(w) for w in _visible_widgets()]}


def _matches(
    name: Optional[str], text: Optional[str], obj_name: str, obj_text: str
) -> bool:
    return (not name or obj_name == name) and (
        not text or text.lower() in obj_text.replace("&", "").lower()
    )


def click_widget(payload: dict[str, Any]) -> dict[str, Any]:
    """Clicks the one visible button (or window action) matching `name` (its
    objectName) and/or `text` (part of its label), in the windows whose title
    contains `window` when it's given."""
    name: Optional[str] = payload.get("name")
    text: Optional[str] = payload.get("text")
    window: str = payload.get("window") or ""
    if not name and not text:
        raise ValueError("Pass a name or text")

    buttons = [
        w
        for w in _visible_widgets()
        if isinstance(w, QAbstractButton)
        and window in _window_title(w)
        and _matches(name, text, w.objectName(), w.text())
    ]
    actions = (
        []
        if buttons
        else [
            a
            for w in QApplication.topLevelWidgets()
            if w.isVisible() and window in w.windowTitle()
            for a in w.findChildren(QAction)
            if _matches(name, text, a.objectName(), a.text())
        ]
    )
    targets: list[Any] = buttons or actions
    if len(targets) != 1:
        found = [_describe(b) for b in buttons] or [a.text() for a in actions]
        raise ValueError(f"Expected one match for {payload}, found {found}")

    target = targets[0]
    if not target.isEnabled():
        tooltip = _describe(target)["tooltip"] if buttons else target.toolTip()
        raise ValueError(f"{name or text} is disabled: {tooltip}")
    # Deferred so a handler that opens a modal dialog doesn't hold this request.
    trigger: Callable[[], Any] = target.click if buttons else target.trigger
    QTimer.singleShot(0, trigger)
    return {"clicked": _describe(target) if buttons else {"text": target.text()}}


def close_windows(payload: dict[str, Any]) -> dict[str, Any]:
    """Closes the visible windows (never Anki's main one) whose title contains
    `window`, as their close button would."""
    title: str = payload["window"]
    windows = [
        w
        for w in QApplication.topLevelWidgets()
        if w.isVisible() and w is not mw and title in w.windowTitle()
    ]
    for window in windows:
        QTimer.singleShot(0, window.close)
    return {"closed": [w.windowTitle() for w in windows]}


def resize_window(payload: dict[str, Any]) -> dict[str, Any]:
    """Resizes the one visible window whose title contains `window` to `width`
    by `height`, as dragging its corner would."""
    title: str = payload["window"]
    windows = [
        w
        for w in QApplication.topLevelWidgets()
        if w.isVisible() and title in w.windowTitle()
    ]
    if len(windows) != 1:
        raise ValueError(
            f"Expected one window titled *{title}*, found {[w.windowTitle() for w in windows]}"
        )
    window = windows[0]
    window.resize(int(payload["width"]), int(payload["height"]))
    return {"window": window.windowTitle(), "size": [window.width(), window.height()]}


def set_language(payload: dict[str, Any]) -> dict[str, Any]:
    """Switches Anki's interface language to `lang` (e.g. "ja") until Anki
    restarts, as its Preferences would. Windows opened after it use it."""
    lang.set_lang(payload["lang"])
    return {"lang": lang.current_lang}


DEV_COMMAND_HANDLERS: dict[str, Callable[[dict[str, Any]], Any]] = {
    "dev.qt.widgets": list_widgets,
    "dev.qt.click": click_widget,
    "dev.qt.close": close_windows,
    "dev.qt.resize": resize_window,
    "dev.qt.lang": set_language,
}
