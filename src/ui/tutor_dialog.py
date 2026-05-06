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
import os

from aqt import QDialog, QVBoxLayout
from PyQt6.QtCore import QUrl
from PyQt6.QtWebEngineWidgets import QWebEngineView

from ..config import config
from ..constants import get_server_url
from ..logger import logger

TUTOR_DIST_PATH = os.path.normpath(
    os.path.join(
        os.path.dirname(__file__), "..", "..", "web", "tutor", "dist", "index.html"
    )
)


class TutorDialog(QDialog):
    """Prototype AI Tutor dialog. Webview loads the built React app from
    web/tutor/dist/index.html and the dialog injects auth/server config
    via window.__TUTOR_CONFIG__."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Smart Notes — AI Tutor (alpha)")
        self.resize(720, 720)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self._web = QWebEngineView(self)
        layout.addWidget(self._web)

        html = self._load_html()
        # baseUrl = server origin so fetch() to /api/tutor is same-origin and
        # skips CORS preflight.
        self._web.setHtml(html, QUrl(get_server_url() + "/"))

    def _load_html(self) -> str:
        if not os.path.exists(TUTOR_DIST_PATH):
            logger.error(f"Tutor dist not found at {TUTOR_DIST_PATH}")
            return MISSING_BUILD_HTML.replace("__PATH__", TUTOR_DIST_PATH)

        with open(TUTOR_DIST_PATH, encoding="utf-8") as f:
            html = f.read()

        config_json = json.dumps(
            {"serverUrl": get_server_url(), "jwt": config.auth_token or ""}
        )
        # Inject config before any bundled script runs.
        return html.replace(
            "<head>",
            f"<head><script>window.__TUTOR_CONFIG__={config_json};</script>",
            1,
        )


MISSING_BUILD_HTML = """<!doctype html><html><body style="font-family:-apple-system,sans-serif;padding:24px;color:#333">
<h2>AI Tutor build not found</h2>
<p>Run <code>bun install &amp;&amp; bun run build</code> in <code>web/tutor</code>.</p>
<p>Expected: <code>__PATH__</code></p>
</body></html>"""
