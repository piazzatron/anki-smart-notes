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
    QDialog,
    QDialogButtonBox,
    QFont,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..auth_flow import start_browser_signup
from ..sentry import pinger
from ..tasks import run_async_in_background


class V2CTA(QDialog):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        run_async_in_background(pinger("show_trial_cta"), use_collection=False)
        self.setWindowTitle("Smart Notes 2.0")
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout()
        self.setLayout(layout)

        header_font = QFont()
        header_font.setBold(True)
        header_font.setPointSize(18)

        title = QLabel("✨ Smart Notes 2.0 is here! ✨")
        title.setFont(header_font)
        layout.addWidget(title)

        body = QLabel(
            "Smart Notes has been rewritten with a brand new backend, new AI models, "
            "and a full subscription plan. Sign up to keep enjoying Smart Notes."
        )
        body.setWordWrap(True)
        layout.addWidget(body)

        cta = QPushButton("Sign up in your browser")
        cta.clicked.connect(lambda: start_browser_signup("/upgrade/sign-in"))
        layout.addWidget(cta)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setMinimumWidth(480)
