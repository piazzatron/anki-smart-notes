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

from typing import Literal, TypedDict

from aqt import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    Qt,
    QVBoxLayout,
    QWidget,
    Union,
)

from ..app_state import AppState, app_state
from ..constants import get_site_url
from ..subscription_provider import SubscriptionState
from .state_manager import StateManager
from .ui_utils import font_bold
from .webview_dialog import WebviewDialog


class State(TypedDict):
    subscription: Union[SubscriptionState, Literal["Loading"]]


start_trial_style = """
            QPushButton {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #4dfa9d, stop: 1 #5cdb97
                ); /* Gradient background */
                color: white; /* White text */
                border: none; /* No border */
                padding: 0px 32px; /* Padding */
                text-align: center; /* Centered text */
                text-decoration: none; /* No underline */
                font-size: 24px; /* Font size */
                margin: 4px 2px; /* Margin */
                border-radius: 12px; /* Rounded corners */
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #5cdb97, stop: 1 #4dfa9d
                ); /* Reverse gradient on hover */
            }
        """

upgrade_now_style = """
            QPushButton {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #4dfa9d, stop: 1 #5cdb97
                ); /* Gradient background */
                color: white; /* White text */
                border: none; /* No border */
                padding: 0px 32px; /* Padding */
                text-align: center; /* Centered text */
                text-decoration: none; /* No underline */
                font-size: 18px; /* Font size */
                margin: 4px 2px; /* Margin */
                border-radius: 12px; /* Rounded corners */
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #5cdb97, stop: 1 #4dfa9d
                ); /* Reverse gradient on hover */
            }
        """


class SubscriptionBox(QWidget):
    _state: StateManager[State]

    def __init__(self) -> None:
        super().__init__()
        self._state = StateManager[State]({"subscription": "Loading"})
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.container = QGroupBox("Subscription")

        # Free Trial active
        self.trial_label = QLabel("Status: ✅ Free trial active")
        self.upgrade_now_button = QPushButton("Upgrade Now")
        self.upgrade_now_button.setStyleSheet(upgrade_now_style)
        self.upgrade_now_button.setFixedHeight(50)

        self.upgrade_now_button.clicked.connect(self.upgrade_now_clicked)
        self.free_trial_active_layout = QHBoxLayout()
        self.free_trial_active_layout.addWidget(
            self.trial_label, alignment=Qt.AlignmentFlag.AlignLeft
        )
        self.free_trial_active_layout.addWidget(
            self.upgrade_now_button, alignment=Qt.AlignmentFlag.AlignRight
        )

        # Free trial CTA
        self.start_trial_button = QPushButton("✨ Start Free Trial ✨")
        self.start_trial_button.setStyleSheet(start_trial_style)
        self.start_trial_button.setFont(font_bold)
        self.start_trial_button.clicked.connect(self.start_free_trial_clicked)
        self.start_trial_button.setFixedHeight(100)

        self.trial_description = QLabel(
            "👉 Access all features, including Claude, advanced text-to-speech, and chained smart fields. No credit card required!"
        )
        self.trial_description.setFont(font_bold)

        self.free_trial_layout = QVBoxLayout()
        self.free_trial_layout.addWidget(self.start_trial_button)
        self.free_trial_layout.addWidget(self.trial_description)

        layout = QVBoxLayout()
        layout.addWidget(self.container)
        self.setLayout(layout)

        app_state._state.bind(self)

    # Remove widgets on each state update
    def _teardown_ui(self) -> None:
        pass
        # self.substate.hide()
        # self.start_trial_button.hide()

    def start_free_trial_clicked(self) -> None:
        webview = WebviewDialog(self)
        webview.show()

    def upgrade_now_clicked(self) -> None:
        webview = WebviewDialog(self, "/upgrade")
        webview.show()

    def update_from_state(self, state: AppState) -> None:
        self._teardown_ui()
        fn_map = {
            "Loading": self._render_loading,
            "UNAUTHENTICATED": self._render_start_trial,
            "NO_SUBSCRIPTION": self._render_start_trial,
            "FREE_TRIAL_ACTIVE": self._render_free_trial_active,
            "FREE_TRIAL_EXPIRED": self._render_upgrade_trial,
            "FREE_TRIAL_CAPACITY": self._render_upgrade_trial,
            "PAID_PLAN_ACTIVE": self._render_active,
            "PAID_PLAN_CAPACITY": self._render_paid_capacity,
            "PAID_PLAN_EXPIRED": self._render_paid_lapsed,
        }
        render_fn = fn_map.get(state["subscription"])
        # Shouldn't happen
        if not render_fn:
            return
        render_fn()

    def _render_loading(self) -> None:
        print("rendering loading")
        layout = QVBoxLayout()
        label = QLabel("Loading...")
        layout.addWidget(label)
        self.container.setLayout(layout)

    def _render_start_trial(self) -> None:
        print("rendering free trial")
        self.container.setLayout(self.free_trial_layout)
        # self.start_trial_button.show()

    def _render_free_trial_active(self) -> None:
        print("rendering free trial active")
        self.container.setLayout(self.free_trial_active_layout)

    def _render_active(self) -> None:
        layout = QHBoxLayout()
        label = QLabel("✅ Subscription Active")
        manage_link = f"{get_site_url()}/account"
        manage_label = QLabel(f"<a href={manage_link}>Manage Subscription</a>")
        manage_label.setOpenExternalLinks(True)
        layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(manage_label, alignment=Qt.AlignmentFlag.AlignRight)
        # Add spacer
        self.container.setLayout(layout)

    def _render_upgrade_trial(self) -> None:
        layout = QHBoxLayout()
        label = QLabel("🚨 Trial Expired!")
        label.setFont(font_bold)
        layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.upgrade_now_button, alignment=Qt.AlignmentFlag.AlignRight)

        # Add spacer
        self.container.setLayout(layout)

    def _render_paid_capacity(self) -> None:
        layout = QHBoxLayout()
        label = QLabel("🚨 You've used up your plan for this month!")
        label.setFont(font_bold)
        layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.upgrade_now_button, alignment=Qt.AlignmentFlag.AlignRight)

        # Add spacer
        self.container.setLayout(layout)

    def _render_paid_lapsed(self) -> None:
        layout = QHBoxLayout()
        label = QLabel("🚨 There's something wrong with your subscription!")
        label.setFont(font_bold)

        manage_link = f"{get_site_url()}/account"
        manage_label = QLabel(f"<a href={manage_link}>Manage Subscription</a>")
        manage_label.setOpenExternalLinks(True)
        layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(manage_label, alignment=Qt.AlignmentFlag.AlignRight)
        # Add spacer
        self.container.setLayout(layout)
