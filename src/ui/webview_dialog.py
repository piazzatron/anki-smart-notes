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

from aqt import QDialog, QHBoxLayout, QUrl, QUrlQuery, QWebEngineView, QWidget

from ..app_state import app_state
from ..config import config
from ..constants import get_site_url


class WebviewDialog(QDialog):
    def __init__(self, parent: QWidget, path: str = "") -> None:
        super().__init__(parent)
        self._setup_ui(path)

    def _setup_ui(self, path: str) -> None:
        engine = QWebEngineView()
        engine.load(QUrl(f"{get_site_url()}/{path}"))
        engine.urlChanged.connect(self.on_engine_url_changed)
        layout = QHBoxLayout()
        self.setMinimumHeight(800)
        self.setMinimumWidth(1200)
        self.setLayout(layout)
        layout.addWidget(engine)
        engine.showMaximized()
        layout.setContentsMargins(0, 0, 0, 0)  # Remove padding

    def on_engine_url_changed(self, url: QUrl) -> None:
        query = QUrlQuery(url)
        value = query.queryItemValue("jwt")
        if value:
            print(f"Got token! value: {value}")
            config.auth_token = value
            app_state.update_subscription_state()
        else:
            print("NO VALUE")

    def closeEvent(self, event) -> None:
        app_state.update_subscription_state()
        super().closeEvent(event)
