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
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    Qt,
    QVBoxLayout,
    QWidget,
    Union,
    pyqtSignal,
)

from ..app_state import AppState, app_state
from ..constants import get_site_url
from ..subscription_provider import SubscriptionState
from .ui_utils import font_bold, font_small
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


class ClickableLabel(QLabel):
    clicked = pyqtSignal()

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class SubscriptionBox(QWidget):

    def __init__(self) -> None:
        super().__init__()

        self.ui_map = {
            "Loading": self._render_loading(),
            "UNAUTHENTICATED": self._render_start_trial(),
            "NO_SUBSCRIPTION": self._render_start_trial(),
            "FREE_TRIAL_ACTIVE": self._render_free_trial_active(),
            "FREE_TRIAL_EXPIRED": self._render_upgrade_trial(),
            "FREE_TRIAL_CAPACITY": self._render_upgrade_trial(),
            "PAID_PLAN_ACTIVE": self._render_active(),
            "PAID_PLAN_CAPACITY": self._render_paid_capacity(),
            "PAID_PLAN_EXPIRED": self._render_paid_lapsed(),
        }

        self._setup_ui()

    def _setup_ui(self) -> None:
        self.container = QGroupBox("Subscription")

        layout = QVBoxLayout()
        layout.addWidget(self.container)
        layout.setContentsMargins(0, 0, 0, 0)
        self.group_box_layout = QVBoxLayout()
        self.container.setLayout(self.group_box_layout)
        self.group_box_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        for v in self.ui_map.values():
            self.group_box_layout.addWidget(v)
            v.hide()

        # Helpful combo picker to try out different states
        combo_picker = QComboBox()
        combo_picker.addItems(
            [
                "Loading",
                "UNAUTHENTICATED",
                "NO_SUBSCRIPTION",
                "FREE_TRIAL_ACTIVE",
                "FREE_TRIAL_EXPIRED",
                "FREE_TRIAL_CAPACITY",
                "PAID_PLAN_ACTIVE",
                "PAID_PLAN_CAPACITY",
                "PAID_PLAN_EXPIRED",
            ]
        )
        combo_picker.currentIndexChanged.connect(
            lambda _: app_state._state.update(
                {"subscription": combo_picker.currentText()}
            )
        )
        layout.addWidget(combo_picker)
        app_state._state.bind(self)

    def start_free_trial_clicked(self) -> None:
        webview = WebviewDialog(self)
        webview.show()

    def upgrade_now_clicked(self) -> None:
        webview = WebviewDialog(self, "/upgrade")
        webview.show()

    def login_clicked(self) -> None:
        webview = WebviewDialog(self, "/login")
        webview.show()

    def update_from_state(self, state: AppState) -> None:
        for k, v in self.ui_map.items():
            self.group_box_layout.addWidget(v)
            if k == state["subscription"]:
                v.show()
            else:
                v.hide()

    def _render_loading(self) -> QWidget:
        layout = QVBoxLayout()
        label = QLabel("Loading...")
        layout.addWidget(label)

        container = QWidget()
        container.setLayout(layout)
        return container

    def _render_start_trial(self) -> QWidget:
        self.start_trial_button = QPushButton("✨ Start Free Trial ✨")
        self.start_trial_button.setStyleSheet(start_trial_style)
        self.start_trial_button.setFont(font_bold)
        self.start_trial_button.clicked.connect(self.start_free_trial_clicked)
        self.start_trial_button.setFixedHeight(100)

        self.trial_description = QLabel(
            "👉 Access all features, including Claude, advanced text-to-speech, and chained smart fields. No credit card required!"
        )
        self.trial_description.setFont(font_bold)

        login_link = f"{get_site_url()}/login"
        login = ClickableLabel(
            f"<a href={login_link}>Already have an account? Sign in.</>"
        )
        login.clicked.connect(self.login_clicked)
        login.setFont(font_small)

        free_trial_layout = QVBoxLayout()
        free_trial_layout.addWidget(self.start_trial_button)
        free_trial_layout.addWidget(self.trial_description)
        free_trial_layout.addWidget(login)
        free_trial_layout.setContentsMargins(24, 24, 24, 24)
        container = QWidget()
        container.setLayout(free_trial_layout)
        return container

    def _render_free_trial_active(self) -> QWidget:
        self.trial_label = QLabel("Status: ✅ Free trial active")

        layout = QHBoxLayout()
        layout.addWidget(self.trial_label, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(
            self._render_upgrade_now_button(), alignment=Qt.AlignmentFlag.AlignRight
        )

        container = QWidget()
        container.setLayout(layout)
        return container

    def _render_active(self) -> QWidget:
        layout = QHBoxLayout()
        label = QLabel("✅ Subscription Active")
        manage_link = f"{get_site_url()}/account"
        manage_label = QLabel(f"<a href={manage_link}>Manage Subscription</a>")
        manage_label.setOpenExternalLinks(True)
        layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(manage_label, alignment=Qt.AlignmentFlag.AlignRight)

        container = QWidget()
        container.setLayout(layout)

        return container

    def _render_upgrade_now_button(self) -> QWidget:
        # Shared by a bunch of the states
        upgrade_now_button = QPushButton("Upgrade Now")
        upgrade_now_button.setStyleSheet(upgrade_now_style)
        upgrade_now_button.setFixedHeight(50)
        upgrade_now_button.clicked.connect(self.upgrade_now_clicked)

        return upgrade_now_button

    def _render_upgrade_trial(self) -> QWidget:
        layout = QHBoxLayout()
        label = QLabel("🚨 Trial Expired!")
        label.setFont(font_bold)

        layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(
            self._render_upgrade_now_button(), alignment=Qt.AlignmentFlag.AlignRight
        )

        container = QWidget()
        container.setLayout(layout)
        return container

    def _render_paid_capacity(self) -> QWidget:
        layout = QHBoxLayout()
        label = QLabel("🚨 You've used up your plan for this month!")
        label.setFont(font_bold)
        layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(
            self._render_upgrade_now_button(), alignment=Qt.AlignmentFlag.AlignRight
        )

        container = QWidget()
        container.setLayout(layout)
        return container

    def _render_paid_lapsed(self) -> QWidget:
        layout = QHBoxLayout()
        label = QLabel("🚨 There's something wrong with your subscription!")
        label.setFont(font_bold)

        manage_link = f"{get_site_url()}/account"
        manage_label = QLabel(f"<a href={manage_link}>Manage Subscription</a>")
        manage_label.setOpenExternalLinks(True)
        layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(manage_label, alignment=Qt.AlignmentFlag.AlignRight)
        # Add spacer

        container = QWidget()
        container.setLayout(layout)
        return container
