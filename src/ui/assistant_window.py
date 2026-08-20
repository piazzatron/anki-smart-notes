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

from aqt.qt import QCloseEvent, Qt, QUrl, QVBoxLayout, QWidget, pyqtSignal

from .web_app_dialog import SmartNotesWebView

PREFERRED_WINDOW_WIDTH = 460
PREFERRED_WINDOW_HEIGHT = 720
MAX_SCREEN_USAGE_RATIO = 0.9


class AssistantWindow(QWidget):
    """The chat assistant's own window.

    A plain `Qt.Window` rather than a `QDialog` so it sits alongside the main
    Anki window instead of always floating above it — the user studies and
    chats at the same time. Narrow by default so it parks beside Anki.
    """

    closed = pyqtSignal()

    def __init__(self, url: str) -> None:
        super().__init__(None, Qt.WindowType.Window)
        self.setWindowTitle("Smart Notes Assistant")

        screen = self.screen()
        if screen is None:
            raise RuntimeError("Smart Notes assistant window screen is unavailable")

        available_size = screen.availableGeometry().size()
        self.resize(
            min(
                PREFERRED_WINDOW_WIDTH,
                int(available_size.width() * MAX_SCREEN_USAGE_RATIO),
            ),
            min(
                PREFERRED_WINDOW_HEIGHT,
                int(available_size.height() * MAX_SCREEN_USAGE_RATIO),
            ),
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        app_url = QUrl(url)
        self._web_view = SmartNotesWebView(app_url, self)
        self._web_view.setUrl(app_url)
        layout.addWidget(self._web_view)

    def closeEvent(self, a0: Optional[QCloseEvent]) -> None:  # noqa: N802
        self.closed.emit()
        super().closeEvent(a0)
