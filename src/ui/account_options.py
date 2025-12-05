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
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from ..app_state import AppState, app_state
from ..config import config
from .manage_subscription import ManageSubscription
from .ui_utils import default_form_layout


class AccountOptions(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._setup_ui()
        app_state.bind(self)

    def _setup_ui(self) -> None:
        self.logoutButton = QPushButton("Logout")
        self.logoutButton.clicked.connect(self.logout)
        layout = QVBoxLayout()

        self.sub_box = QGroupBox("Subscription Info")
        self.sub_type = QLabel()
        self.credits_progress = QProgressBar()
        self.credits_progress.setMinimum(0)
        self.credits_progress.setMaximum(100)
        self.credits_progress.setMinimumWidth(200)
        self.credits_progress.setTextVisible(False)
        self.credits_percent_label = QLabel()
        credits_row = QHBoxLayout()
        credits_row.addWidget(self.credits_progress)
        credits_row.addWidget(self.credits_percent_label)
        credits_row.setContentsMargins(0, 0, 0, 0)
        credits_widget = QWidget()
        credits_widget.setLayout(credits_row)
        self.credits_breakdown = QLabel()
        self.days_remaining = QLabel()
        self.cards_remaining = QLabel()

        sub_box_layout = default_form_layout()
        sub_box_layout.addRow("Subscription Type:", self.sub_type)
        sub_box_layout.addRow("Credits Usage:", credits_widget)
        sub_box_layout.addRow("Usage Breakdown:", self.credits_breakdown)
        sub_box_layout.addRow("Days Remaining:", self.days_remaining)
        sub_box_layout.addRow("Notes Used:", self.cards_remaining)
        sub_box_layout.addItem(QSpacerItem(0, 12))
        sub_box_layout.addRow(ManageSubscription(), QLabel(""))

        self.no_sub = QLabel("Nothing to see here...")
        layout.addWidget(self.sub_box)
        layout.addWidget(self.no_sub)

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
            # Enable logout if user is authenticated (has auth token), even if plan data failed to load
            self.logoutButton.setEnabled(bool(config.auth_token))
        else:
            self.sub_box.show()
            self.no_sub.hide()
            self.logoutButton.setEnabled(True)

            plan = state["plan"]
            sub_type = plan["planName"]

            total_used = plan["totalCreditsUsed"]
            total_capacity = plan["totalCreditsCapacity"]
            usage_percent = (
                int((total_used / total_capacity) * 100) if total_capacity > 0 else 0
            )

            text_credits = plan["textCreditsUsed"]
            voice_credits = plan["voiceCreditsUsed"]

            if total_used > 0:
                text_percent = int((text_credits / total_used) * 100)
                voice_percent = int((voice_credits / total_used) * 100)
                image_percent = 100 - text_percent - voice_percent
            else:
                text_percent = voice_percent = image_percent = 0

            credits_breakdown = f"Text 💬: {text_percent}%  |  Voice 🎤: {voice_percent}%  |  Image 🖼️: {image_percent}%"

            days = plan["daysLeft"]
            days_remaining = f"{days} day{'s' if days > 1 else ''} left{' in cycle' if plan['planId'] == 'free' else ''}."

            if plan["notesLimit"]:
                notes_limit = f"{plan['notesUsed']}/{plan['notesLimit']}"
            else:
                notes_limit = "Unlimited"

            self.sub_type.setText(sub_type)
            self.credits_progress.setValue(usage_percent)

            if usage_percent > 80:
                color = "#e53935"
            elif usage_percent > 50:
                color = "#fb8c00"
            else:
                color = "#43a047"
            self.credits_percent_label.setText(f"{usage_percent}% used")
            self.credits_percent_label.setStyleSheet(f"color: {color};")

            self.credits_breakdown.setText(credits_breakdown)
            self.days_remaining.setText(days_remaining)
            self.cards_remaining.setText(notes_limit)

    def logout(self):
        config.auth_token = None
        self.logoutButton.setEnabled(False)
        app_state.update_subscription_state()
