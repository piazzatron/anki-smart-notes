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

from aqt.qt import (
    QDialog,
    QUrl,
    QVBoxLayout,
    QWebEnginePage,
    QWebEngineSettings,
    QWebEngineView,
    QWidget,
)
from aqt.utils import openLink


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
        app_url = QUrl(url)
        self._web_view = _SmartNotesWebView(app_url, self)
        # Media previews finish after an async provider request, outside the
        # original Run-button gesture. Allow the requested result to play.
        web_settings = self._web_view.settings()
        if web_settings is None:
            raise RuntimeError("Smart Notes webview settings are unavailable")
        web_settings.setAttribute(
            QWebEngineSettings.WebAttribute.PlaybackRequiresUserGesture,
            False,
        )
        self._web_view.setUrl(app_url)
        layout.addWidget(self._web_view)


class _SmartNotesWebPage(QWebEnginePage):
    """Keep Smart Notes navigation local and send external URLs to the OS."""

    def __init__(self, app_url: QUrl, parent: QWidget) -> None:
        super().__init__(parent)
        self._app_url = app_url

    def acceptNavigationRequest(
        self,
        url: QUrl,
        type: QWebEnginePage.NavigationType,
        isMainFrame: bool,
    ) -> bool:
        if (
            isMainFrame
            and url.scheme() in {"http", "https", "mailto"}
            and not self._is_app_url(url)
        ):
            openLink(url)
            return False

        return super().acceptNavigationRequest(url, type, isMainFrame)

    def _is_app_url(self, url: QUrl) -> bool:
        return (
            url.scheme() == self._app_url.scheme()
            and url.host() == self._app_url.host()
            and url.port() == self._app_url.port()
        )


class _SmartNotesWebView(QWebEngineView):
    """Create invisible child pages so target=_blank links reach our page policy."""

    def __init__(self, app_url: QUrl, parent: QWidget) -> None:
        super().__init__(parent)
        self._app_url = app_url
        self.setPage(_SmartNotesWebPage(app_url, self))

    def createWindow(self, type: QWebEnginePage.WebWindowType) -> QWebEngineView:
        return _SmartNotesWebView(self._app_url, self)
