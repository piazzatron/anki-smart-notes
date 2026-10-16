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

from typing import Optional

from aqt import mw

from ..event_bus import ScreenRequested, event_bus
from ..logger import logger
from .assistant_window import AssistantWindow
from .web_app_dialog import WebAppDialog

_web_app_dialog: Optional[WebAppDialog] = None
_assistant_window: Optional[AssistantWindow] = None


def open_web_app_window(url: str, screen: Optional[str] = None) -> None:
    """Shows the main window at `url`, or raises the one already open.

    An open webview cannot be re-pointed through its URL, so a screen for one
    that is already up is asked for over the event channel it is listening on."""
    global _web_app_dialog

    if _web_app_dialog is not None:
        _web_app_dialog.raise_()
        _web_app_dialog.activateWindow()
        if screen is not None:
            event_bus.publish(ScreenRequested(screen=screen))
        return

    dialog = WebAppDialog(url, mw)
    _web_app_dialog = dialog

    def clear_web_app_dialog(_: object) -> None:
        global _web_app_dialog
        if _web_app_dialog is dialog:
            _web_app_dialog = None

    dialog.finished.connect(clear_web_app_dialog)
    dialog.show()


def open_assistant_window(url: str) -> None:
    global _assistant_window

    if _assistant_window is not None:
        _assistant_window.raise_()
        _assistant_window.activateWindow()
        return

    window = AssistantWindow(url)
    _assistant_window = window

    def clear_assistant_window() -> None:
        global _assistant_window
        if _assistant_window is window:
            _assistant_window = None

    window.closed.connect(clear_assistant_window)
    window.show()


def close_assistant() -> None:
    global _assistant_window

    if _assistant_window is None:
        return

    logger.info("Closing Smart Notes assistant before profile close")
    window = _assistant_window
    _assistant_window = None
    window.close()


def close_web_app() -> None:
    global _web_app_dialog

    if _web_app_dialog is None:
        return

    # Close the webview before its Anki profile state becomes stale. Production
    # sessions also receive a new local API token on the next profile load.
    logger.info("Closing Smart Notes web app before profile close")
    dialog = _web_app_dialog
    _web_app_dialog = None
    dialog.close()
