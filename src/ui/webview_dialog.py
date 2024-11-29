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

import time
from typing import Dict
from urllib.parse import urlencode

from aqt import (
    QDateTime,
    QDialog,
    QHBoxLayout,
    QUrl,
    QUrlQuery,
    QWebEngineView,
    QWidget,
)
from PyQt6.QtNetwork import QNetworkCookie

from ..app_state import app_state
from ..config import config
from ..constants import get_site_url
from ..logger import logger

CLERK_DEV_JWT = "dvb_2jUh8kOg9bIN8jQzywLdD3E5bMl"


class WebviewDialog(QDialog):
    def __init__(
        self, parent: QWidget, path: str = "", query_params: Dict[str, str] = {}
    ) -> None:
        super().__init__(parent)
        self._setup_ui(path, query_params)

    def _setup_ui(self, path: str, query_params: Dict[str, str]) -> None:
        query_params["anki"] = "true"
        query_params["uuid"] = config.uuid or ""
        if config.legacy_support:
            query_params["isLegacy"] = "true"

        engine = QWebEngineView()
        encoded = urlencode(query_params)

        url = f"{get_site_url()}{path}?{encoded}"
        engine.load(QUrl(url))
        engine.urlChanged.connect(self.on_engine_url_changed)
        layout = QHBoxLayout()
        self.setMinimumHeight(1080)
        self.setMinimumWidth(1080)
        self.resize(1400, 1200)

        self.setLayout(layout)
        layout.addWidget(engine)
        engine.showMaximized()
        layout.setContentsMargins(0, 0, 0, 0)  # Remove padding

        self.add_session_cookie(engine)

    def add_session_cookie(self, engine: QWebEngineView) -> None:
        jwt = config.auth_token
        if not jwt:
            return
        page = engine.page()
        if not page:
            return
        profile = page.profile()
        if profile is None:
            return
        cookie_store = profile.cookieStore()
        if not cookie_store:
            return

        # Add cookies to automatically auth the user
        seconds_since_epoch = str(int(time.time()))
        c1 = self.make_cookie(b"__session", jwt.encode())
        c2 = self.make_cookie(b"__client_uat", seconds_since_epoch.encode())
        # Just a dev cookie
        c3 = self.make_cookie(b"__clerk_db_jwt", CLERK_DEV_JWT.encode())

        url = QUrl(get_site_url())
        cookie_store.setCookie(c1, url)
        cookie_store.setCookie(c2, url)
        cookie_store.setCookie(c3, url)

        cookie_store

    def make_cookie(self, name: bytes, value: bytes):
        cookie = QNetworkCookie()
        cookie.setName(name)
        cookie.setValue(value)
        cookie.setDomain(get_site_url().replace("https://", "").replace("http://", ""))
        cookie.setPath("/")
        cookie.setSecure(False)
        cookie.setExpirationDate(QDateTime.currentDateTime().addDays(1))
        return cookie

    def on_engine_url_changed(self, url: QUrl) -> None:
        query = QUrlQuery(url)
        value = query.queryItemValue("jwt")
        if value:
            logger.debug(f"Got JWT! Adding to config")
            config.auth_token = value
            app_state.update_subscription_state()

    def closeEvent(self, event) -> None:
        logger.debug("Webview dialog closed, updating subscription state")
        app_state.update_subscription_state()
        super().closeEvent(event)
