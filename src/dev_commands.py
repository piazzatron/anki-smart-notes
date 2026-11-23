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

import asyncio
import inspect
from collections.abc import Callable
from typing import Any, Optional

from anki import lang
from aqt import mw
from aqt.browser.sidebar.item import SidebarItemType
from aqt.qt import (
    QAbstractButton,
    QAction,
    QApplication,
    QItemSelectionModel,
    QKeySequence,
    QLineEdit,
    QMenu,
    QMessageBox,
    QObject,
    QPlainTextEdit,
    QPoint,
    Qt,
    QTextEdit,
    QTimer,
    QWidget,
    pyqtSignal,
    pyqtSlot,
)
from PyQt6.QtTest import QTest

from .config import config
from .services.usage_service import get_times_used, set_times_used


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
        # A dialog parented to another window is a window of its own: list its
        # buttons once, under it.
        if b.window() is w and b.isVisible() and (b.objectName() or b.text().strip())
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


def usage(payload: dict[str, Any]) -> dict[str, Any]:
    """This profile's generation count and whether the one-time rate dialog has
    shown, setting either when the payload has `count` or `rateDialogShown`."""
    if "count" in payload:
        set_times_used(int(payload["count"]))
    if "rateDialogShown" in payload:
        config.did_show_rate_dialog = bool(payload["rateDialogShown"])
    return {
        "count": get_times_used(),
        "rateDialogShown": bool(config.did_show_rate_dialog),
    }


class _MainThreadEvents(QObject):
    """Runs work on Anki's main thread as a Qt event of its own.

    Anki's taskman runs its pending closures as one batch, so a command queued
    into the batch whose closure opens a modal box (a batch's result) would wait
    until the box closed, and a check waiting for that very box would time out.
    An event of its own runs from the box's event loop."""

    work = pyqtSignal(object)

    def __init__(self) -> None:
        super().__init__()
        # Created on the server's thread when the first command loads this
        # module; its slot has to run on the main thread.
        app = QApplication.instance()
        assert app
        self.moveToThread(app.thread())
        self.work.connect(self._run)

    @pyqtSlot(object)
    def _run(self, fn: Callable[[], None]) -> None:
        fn()


_main_thread_events = _MainThreadEvents()


async def _on_main(start: Callable[[Callable[[Any], None]], None]) -> Any:
    """Runs `start` on Anki's main thread and waits for it to call the `done`
    callback it's given: webview evals answer asynchronously."""
    loop = asyncio.get_running_loop()
    future: asyncio.Future[Any] = loop.create_future()

    def done(value: Any) -> None:
        loop.call_soon_threadsafe(future.set_result, value)

    def work() -> None:
        try:
            start(done)
        except Exception as e:
            loop.call_soon_threadsafe(future.set_exception, e)

    _main_thread_events.work.emit(work)
    return await asyncio.wait_for(future, 15)


def _editor(title: str) -> Any:
    """The editor of the one visible window whose title contains `title`: the
    Browser's editor pane, the Add dialog or the Edit dialog."""
    windows = [
        w
        for w in QApplication.topLevelWidgets()
        if w.isVisible() and title in w.windowTitle() and getattr(w, "editor", None)
    ]
    if len(windows) != 1:
        raise ValueError(
            f"Expected one editor window titled *{title}*, found {[w.windowTitle() for w in windows]}"
        )
    return windows[0].editor  # pyright: ignore[reportAttributeAccessIssue]


async def eval_in_editor(payload: dict[str, Any]) -> dict[str, Any]:
    """Runs `js` in the editor webview of the window titled `window` and
    returns its result, so tooling can read and click what the editor shows
    (a Smart Field's Generate button) the way the page itself would."""
    result = await _on_main(
        lambda done: _editor(payload["window"]).web.evalWithCallback(
            payload["js"], done
        )
    )
    return {"result": result}


def editor_kind(payload: dict[str, Any]) -> dict[str, Any]:
    """Which of Anki's editors the window titled `window` shows: "experimental"
    (the Svelte editor, NewEditor) or "classic"."""
    e = _editor(payload["window"])
    return {"kind": "experimental" if type(e).__name__ == "NewEditor" else "classic"}


_FOCUS_FIELD_JS = """
document.querySelector('.field-container[data-index="%d"] .rich-text-editable')
  .shadowRoot.querySelector("anki-editable").focus()
"""


async def focus_field(payload: dict[str, Any]) -> dict[str, Any]:
    """Puts the cursor in the editor field at `index` as a click on it would:
    the window and its webview take focus, then the field, and the page
    reports it to the editor."""
    window: str = payload["window"]
    index = int(payload["index"])

    def start(done: Callable[[Any], None]) -> None:
        e = _editor(window)
        e.parentWindow.activateWindow()
        e.web.setFocus()
        e.web.evalWithCallback(_FOCUS_FIELD_JS % index, done)

    await _on_main(start)
    focused = None
    for _ in range(40):
        focused = await _on_main(
            lambda done: done(getattr(_editor(window), "currentField", None))
        )
        if focused == index:
            return {"focused": index}
        await asyncio.sleep(0.05)
    raise ValueError(f"Field {index} never took focus (focused: {focused})")


_FIELD_CENTER_JS = """
(() => {
  const rect = document.querySelector('.field-container[data-index="%d"] .rich-text-editable')
    .getBoundingClientRect();
  return [rect.left + rect.width / 2, rect.top + rect.height / 2];
})()
"""


async def open_field_menu(payload: dict[str, Any]) -> dict[str, Any]:
    """Right-clicks the editor field at `index`, opening its context menu: the
    field takes focus, then a right mouse click lands on it, so Chromium
    sends the webview the context menu request Anki builds its menu from."""
    await focus_field(payload)
    window: str = payload["window"]
    x, y = await _on_main(
        lambda done: _editor(window).web.evalWithCallback(
            _FIELD_CENTER_JS % int(payload["index"]), done
        )
    )

    def start(done: Callable[[Any], None]) -> None:
        web = _editor(window).web
        zoom = web.zoomFactor()
        point = QPoint(int(x * zoom), int(y * zoom))
        target = web.focusProxy() or web
        QTimer.singleShot(
            0,
            lambda: QTest.mouseClick(  # pyright: ignore[reportCallIssue]
                target,  # pyright: ignore[reportArgumentType]
                Qt.MouseButton.RightButton,  # pyright: ignore[reportArgumentType]
                Qt.KeyboardModifier.NoModifier,  # pyright: ignore[reportArgumentType]
                point,  # pyright: ignore[reportArgumentType]
            ),
        )
        done(None)

    await _on_main(start)
    return {"opened": payload["index"]}


def open_notes_menu(payload: dict[str, Any]) -> dict[str, Any]:
    """Opens the Browser's notes (table) context menu as a right-click on the
    selection would."""
    browser = _editor("Browse").parentWindow
    view = browser.table._view
    point = view.visualRect(view.currentIndex()).center()
    QTimer.singleShot(0, lambda: view.customContextMenuRequested.emit(point))
    return {"opened": "notes"}


def open_sidebar_menu(payload: dict[str, Any]) -> dict[str, Any]:
    """Selects the Browser sidebar's deck or note type named `name` and opens
    its context menu, as a right-click on it would."""
    kinds = {
        "deck": (SidebarItemType.DECK, SidebarItemType.DECK_CURRENT),
        "notetype": (SidebarItemType.NOTETYPE,),
    }[payload["kind"]]
    name: str = payload["name"]
    sidebar = _editor("Browse").parentWindow.sidebar
    item = sidebar.find_item(
        lambda i: i.item_type in kinds and name in (i.name, i.full_name)
    )
    if item is None:
        raise ValueError(f"No {payload['kind']} named {name} in the sidebar")
    index = sidebar.model().index_for_item(item)
    sidebar.scrollTo(index)
    sidebar.selectionModel().setCurrentIndex(
        index, QItemSelectionModel.SelectionFlag.ClearAndSelect
    )
    point = sidebar.visualRect(index).center()
    QTimer.singleShot(0, lambda: sidebar.customContextMenuRequested.emit(point))
    return {"opened": item.full_name}


def _open_menus() -> list[QMenu]:
    return [
        w
        for w in QApplication.topLevelWidgets()
        if isinstance(w, QMenu) and w.isVisible()
    ]


def list_menu(payload: dict[str, Any]) -> dict[str, Any]:
    """The items of the open context menus, as their labels."""
    return {
        "items": [
            {"text": a.text().replace("&", ""), "enabled": a.isEnabled()}
            for m in _open_menus()
            for a in m.actions()
            if not a.isSeparator() and a.isVisible()
        ]
    }


def trigger_menu_item(payload: dict[str, Any]) -> dict[str, Any]:
    """Chooses the item whose label contains `text` in the open context menu:
    the menu closes, then the item runs, as a click on it would."""
    text: str = payload["text"].lower()
    matches = [
        (m, a)
        for m in _open_menus()
        for a in m.actions()
        if a.isVisible() and text in a.text().replace("&", "").lower()
    ]
    if len(matches) != 1:
        raise ValueError(
            f"Expected one menu item labelled *{payload['text']}*, found {list_menu({})['items']}"
        )
    menu, action = matches[0]
    if not action.isEnabled():
        raise ValueError(f"{action.text()} is disabled")

    def choose() -> None:
        # As a click does: the menu closes and the item runs in the same turn,
        # before a menu shown with exec() returns and takes its items with it.
        menu.hide()
        action.trigger()

    # Deferred so a handler that opens a modal dialog doesn't hold this request.
    QTimer.singleShot(0, choose)
    return {"triggered": action.text()}


def _one_window(title: str) -> QWidget:
    windows = [
        w
        for w in QApplication.topLevelWidgets()
        if w.isVisible() and w.windowTitle() and title in w.windowTitle()
    ]
    if len(windows) != 1:
        raise ValueError(
            f"Expected one window titled *{title}*, found {[w.windowTitle() for w in windows]}"
        )
    return windows[0]


def type_text(payload: dict[str, Any]) -> dict[str, Any]:
    """Types `text` key by key into the focused text box of the one visible
    window whose title contains `window`, as the keyboard would."""
    window = _one_window(payload["window"])
    target = window.focusWidget()
    if not isinstance(target, (QLineEdit, QTextEdit, QPlainTextEdit)):
        raise ValueError(f"No text box has focus in {window.windowTitle()}: {target}")
    QTest.keyClicks(target, payload["text"])  # pyright: ignore[reportCallIssue]
    return {"typed": payload["text"], "into": type(target).__name__}


async def send_keys(payload: dict[str, Any]) -> dict[str, Any]:
    """Presses the window shortcut `keys` (e.g. "Ctrl+Shift+Return") in the one
    visible window whose title contains `window`, through Qt's shortcut
    handling as a real key press goes. Qt gives a key press to the active
    window's shortcuts, and activating a window takes a moment, so it waits for
    the window to be active first, as it is when a user types in it."""
    window = await _on_main(lambda done: done(_one_window(payload["window"])))
    combo = QKeySequence(payload["keys"])[0]
    await _on_main(lambda done: done(window.activateWindow()))
    for _ in range(100):
        if await _on_main(lambda done: done(QApplication.activeWindow() is window)):
            break
        await asyncio.sleep(0.05)
    else:
        raise ValueError(f"{window.windowTitle()} never became the active window")
    # Qt must not go on reporting the modifiers held afterwards: Anki opens the
    # next Browser on its experimental editor while Shift looks held. So the keys
    # go to the window rather than a focused editor web view, which hands them
    # back to Qt later with their modifiers, and the modifiers are released after,
    # as a real keyboard's are.
    target = window
    modifiers = combo.keyboardModifiers()
    held = [
        key
        for modifier, key in (
            (Qt.KeyboardModifier.ShiftModifier, Qt.Key.Key_Shift),
            (Qt.KeyboardModifier.ControlModifier, Qt.Key.Key_Control),
            (Qt.KeyboardModifier.AltModifier, Qt.Key.Key_Alt),
            (Qt.KeyboardModifier.MetaModifier, Qt.Key.Key_Meta),
        )
        if modifiers & modifier
    ]
    # PyQt6's QtTest stubs miss that these are static.
    click: Any = QTest.keyClick
    release: Any = QTest.keyRelease

    def press() -> None:
        click(target, combo.key(), modifiers)
        for key in held:
            release(target, key, Qt.KeyboardModifier.NoModifier)

    # Deferred, so a shortcut that opens a modal dialog doesn't block the reply.
    await _on_main(lambda done: done(QTimer.singleShot(0, press)))
    return {"pressed": payload["keys"], "window": window.windowTitle()}


def widget_tree(payload: dict[str, Any]) -> dict[str, Any]:
    """The widgets of the one visible window titled `window`, nested, with each
    one's geometry, size hints, size policy and size limits, plus the screen's
    available geometry, to see what constrains a layout."""

    def size(s: Any) -> list[int]:
        return [s.width(), s.height()]

    def describe(w: QWidget) -> dict[str, Any]:
        policy = w.sizePolicy()
        layout = w.layout()
        return {
            "class": type(w).__name__,
            "name": w.objectName(),
            "text": str(getattr(w, "text", getattr(w, "title", lambda: ""))())[:40],
            "visible": w.isVisible(),
            "geometry": [w.x(), w.y(), w.width(), w.height()],
            "sizeHint": size(w.sizeHint()),
            "minimumSizeHint": size(w.minimumSizeHint()),
            "minimumSize": size(w.minimumSize()),
            "maximumSize": size(w.maximumSize()),
            "policy": [policy.horizontalPolicy().name, policy.verticalPolicy().name],
            "layout": None
            if layout is None
            else {
                "class": type(layout).__name__,
                "constraint": layout.sizeConstraint().name,
                "minimumSize": size(layout.minimumSize()),
                "sizeHint": size(layout.sizeHint()),
            },
            "children": [
                describe(c)
                for c in w.findChildren(
                    QWidget, options=Qt.FindChildOption.FindDirectChildrenOnly
                )
            ],
        }

    window = _one_window(payload["window"])
    screen = window.screen()
    return {
        "screen": [
            screen.availableGeometry().width(),
            screen.availableGeometry().height(),
        ]
        if screen
        else None,
        "window": describe(window),
    }


def list_browsers(payload: dict[str, Any]) -> dict[str, Any]:
    """Every Browser window Qt still has, shown or not, with its selection and
    editor note, and which one Anki has registered as the Browser (the one
    AnkiConnect and Anki's own menus open and drive)."""
    from aqt import dialogs
    from aqt.browser.browser import Browser
    from aqt.editor import Editor

    registered = dialogs._dialogs.get("Browser", [None, None])[1]  # pyright: ignore[reportPrivateUsage]
    browsers = [w for w in QApplication.topLevelWidgets() if isinstance(w, Browser)]
    return {
        "browsers": [
            {
                "id": id(b),
                "registered": b is registered,
                "visible": b.isVisible(),
                "title": b.windowTitle(),
                "selectedNotes": [int(n) for n in b.selected_notes()],
                "editor": type(b.editor).__name__,
                "editorNote": b.editor.note.id
                if isinstance(b.editor, Editor) and b.editor.note
                else None,
            }
            for b in browsers
        ],
        "registeredIsShown": registered is not None and registered in browsers,
        # A progress window holds back Anki's deferred work, such as a new
        # Browser's first search, while it's open.
        "progressLevels": mw.progress._levels if mw else None,  # pyright: ignore[reportPrivateUsage]
        # Anki picks a new Browser's editor by whether Shift is held as it opens.
        "modifiers": int(QApplication.keyboardModifiers().value),
    }


def sign_in(payload: dict[str, Any]) -> dict[str, Any]:
    """Signs the add-on in with `token` (a Smart Notes JWT), as a finished
    browser handoff would, so tooling can switch accounts without the site."""
    from .app_state import app_state
    from .config import config

    config.auth_token = payload["token"]
    app_state.update_account_state()
    return {}


def refresh_flags(payload: dict[str, Any]) -> dict[str, Any]:
    """Fetches the server's feature flags again, as Anki's startup does."""
    from .feature_flags import refresh_feature_flags

    refresh_feature_flags()
    return {}


async def check_web(payload: dict[str, Any]) -> dict[str, Any]:
    """Checks our server for the web build now, as Anki's startup does."""
    from .web_loader import web_loader

    await asyncio.get_running_loop().run_in_executor(None, web_loader.check)
    return {"target": web_loader.target, "failed": web_loader.failed}


def select_web(payload: dict[str, Any]) -> dict[str, Any]:
    """Picks the web build to serve, as opening the window does."""
    from .web_loader import web_loader

    web_loader.select_for_window()
    return {"serving": web_loader.serving_build}


def set_web_window(payload: dict[str, Any]) -> dict[str, Any]:
    """Makes the Smart Notes window load downloaded builds from the local server
    (served) or Vite, until Anki restarts."""
    from .web_loader import web_loader

    web_loader.served_in_dev = bool(payload["served"])
    return {"served": web_loader.served_in_dev}


def reset_web(payload: dict[str, Any]) -> dict[str, Any]:
    """Forgets every downloaded web build, as on a fresh install."""
    from .web_loader import web_loader

    web_loader.reset()
    return {}


def _own_event(
    handler: Callable[[dict[str, Any]], Any],
) -> Callable[[dict[str, Any]], Any]:
    """Runs a synchronous command on the main thread through `_on_main`, so it
    isn't held behind a modal box that another taskman closure has open."""
    if inspect.iscoroutinefunction(handler):
        return handler

    async def run(payload: dict[str, Any]) -> Any:
        return await _on_main(lambda done: done(handler(payload)))

    return run


_HANDLERS: dict[str, Callable[[dict[str, Any]], Any]] = {
    "dev.qt.widgets": list_widgets,
    "dev.qt.browsers": list_browsers,
    "dev.qt.tree": widget_tree,
    "dev.qt.click": click_widget,
    "dev.qt.close": close_windows,
    "dev.qt.resize": resize_window,
    "dev.qt.lang": set_language,
    "dev.usage": usage,
    "dev.qt.keys": send_keys,
    "dev.qt.type": type_text,
    "dev.qt.menu": list_menu,
    "dev.qt.menu.trigger": trigger_menu_item,
    "dev.qt.menu.notes": open_notes_menu,
    "dev.qt.menu.sidebar": open_sidebar_menu,
    "dev.editor.eval": eval_in_editor,
    "dev.editor.kind": editor_kind,
    "dev.editor.focus": focus_field,
    "dev.editor.menu": open_field_menu,
    "dev.auth.signIn": sign_in,
    "dev.flags.refresh": refresh_flags,
    "dev.web.check": check_web,
    "dev.web.select": select_web,
    "dev.web.reset": reset_web,
    "dev.web.window": set_web_window,
}

DEV_COMMAND_HANDLERS = {name: _own_event(h) for name, h in _HANDLERS.items()}
