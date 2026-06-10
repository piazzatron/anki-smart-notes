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

from aqt.qt import QDialog, QUrl, QVBoxLayout, QWebEngineView, QWidget


class WebAppDialog(QDialog):
    """Chrome around the Smart Notes web app — just a webview pointed at the
    local server. All state and logic live behind the URL it loads (see
    specs/web-ui-architecture.md in the top-level repo)."""

    def __init__(self, url: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Smart Notes")
        self.resize(1100, 800)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._web_view = QWebEngineView(self)
        self._web_view.setUrl(QUrl(url))
        layout.addWidget(self._web_view)
