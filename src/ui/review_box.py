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

from aqt import (
    QGraphicsOpacityEffect,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
)

from ..app_state import app_state
from ..config import config
from ..feature_flags import flags

STANDARD_TEXT = 'Enjoying Smart Notes? Consider <a href="https://ankiweb.net/shared/info/1531888719">leaving a review</a> to help other users find it.'
FREE_MONTH_TEXT = 'Get a free month of Smart Notes by <a href="https://ankiweb.net/shared/info/1531888719">leaving a review</a> and emailing <a href="mailto:support@smart-notes.xyz">support@smart-notes.xyz</a>.'


class ReviewBox(QGroupBox):
    """Dismissable "leave a review" prompt shown in the options dialog."""

    def __init__(self) -> None:
        super().__init__()

        layout = QHBoxLayout()
        self.setLayout(layout)

        label = QLabel(self._message_text())
        font = label.font()
        font.setItalic(True)
        label.setFont(font)
        label.setOpenExternalLinks(True)

        dismiss = QPushButton("\u2715")
        dismiss.setFixedSize(24, 24)
        dismiss.setFlat(True)
        dismiss.setStyleSheet(
            "QPushButton { border: none; font-size: 20px; opacity: 0.6; }"
        )
        opacity = QGraphicsOpacityEffect()
        opacity.setOpacity(0.6)
        dismiss.setGraphicsEffect(opacity)
        dismiss.clicked.connect(self._on_dismiss)

        layout.addStretch()
        layout.addWidget(label)
        layout.addStretch()
        layout.addWidget(dismiss)

    @staticmethod
    def should_show() -> bool:
        return not config.did_click_rate_link

    def _message_text(self) -> str:
        if flags.review_free_month and app_state.is_free_trial():
            return FREE_MONTH_TEXT
        return STANDARD_TEXT

    def _on_dismiss(self) -> None:
        config.did_click_rate_link = True
        self.hide()
