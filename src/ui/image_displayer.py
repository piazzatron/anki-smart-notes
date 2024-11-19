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

import base64
from typing import Union

from aqt import QHBoxLayout, QWebEngineView, QWidget
from PyQt6.QtCore import Qt


class ImageDisplayer(QWidget):
    webview: QWebEngineView

    def __init__(
        self,
        image: Union[bytes, None] = None,
        height: int = 500,
        width: int = 500,
        parent: Union[QWidget, None] = None,
    ) -> None:
        super().__init__(parent)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)  # Remove padding
        self.setContentsMargins(0, 0, 0, 0)  # Remove padding
        self.setLayout(layout)
        self.webview = QWebEngineView()
        self.webview.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # No focus
        layout.addWidget(self.webview)
        self.setFixedHeight(height)
        self.setFixedWidth(width)
        self.webview.setContentsMargins(0, 0, 0, 0)  # Remove padding
        # self.webview.show()
        if image:
            self.set_image(image)

    def set_image(self, image: bytes) -> None:
        b64_image = base64.b64encode(image).decode("utf-8")
        html = f'<img src="data:image/png;base64,{b64_image}" height="100%" width="100%" />'
        self.webview.setHtml(html)
        self.webview.show()
