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
    QGroupBox,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from ..app_state import AppState, app_state
from ..config import config
from .ui_utils import default_form_layout


class AccountOptions(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._setup_ui()
        app_state._state.bind(self)

    def _setup_ui(self) -> None:
        self.logoutButton = QPushButton("Logout")
        self.logoutButton.clicked.connect(self.logout)
        layout = QVBoxLayout()

        self.sub_box = QGroupBox("Subscription Info")
        self.sub_type = QLabel()
        self.tokens_used = QLabel()
        self.days_remaining = QLabel()
        self.cards_remaining = QLabel()

        sub_box_layout = default_form_layout()
        sub_box_layout.addRow("Subscription Type:", self.sub_type)
        # TODO: credits
        sub_box_layout.addRow("Tokens Usage:", self.tokens_used)
        sub_box_layout.addRow("Days Remaining:", self.days_remaining)
        # TODO: how to handle this one
        sub_box_layout.addRow("Note Usage:", self.cards_remaining)

        self.no_sub = QLabel("Nothing to see here...")
        layout.addWidget(self.sub_box)
        layout.addWidget(self.no_sub)

        layout.addWidget
        self.sub_box.setLayout(sub_box_layout)
        self.sub_box.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )
        layout.addItem(
            QSpacerItem(0, 24, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )
        layout.addWidget(self.logoutButton)
        self.setLayout(layout)

    def update_from_state(self, state: AppState) -> None:

        if not state["plan"]:
            self.sub_box.hide()
            self.no_sub.show()
            self.logoutButton.setEnabled(False)
        else:
            self.sub_box.show()
            self.no_sub.hide()
            self.logoutButton.setEnabled(True)

            sub_type = state["plan"]["planName"]
            tokens_used = (
                f'{state["plan"]["tokensUsed"]} / {state["plan"]["tokenCapacity"]}'
            )
            days = state["plan"]["daysLeft"]
            days_remaining = f'{days} day{"s" if days > 1 else ""} left {"in cycle" if state["plan"]["planId"] == "free" else ""}.'

            if state["plan"]["notesLimit"]:
                notes_limit = (
                    f'{state["plan"]["notesUsed"]}/{state["plan"]["notesLimit"]}'
                )
            else:
                notes_limit = "Unlimited"
            self.cards_remaining.setText(notes_limit)
            self.sub_type.setText(sub_type)
            self.tokens_used.setText(tokens_used)
            self.days_remaining.setText(days_remaining)

    def logout(self):
        config.auth_token = None
        self.logoutButton.setEnabled(False)
        app_state.update_subscription_state()
