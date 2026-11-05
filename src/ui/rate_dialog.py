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
    QHBoxLayout,
    QLabel,
    QPushButton,
    Qt,
    QVBoxLayout,
)
from aqt.utils import openLink

from ..app_state import app_state, is_free_plan
from ..feature_flags import flags
from ..logger import logger
from ..review_claim import ANKIWEB_REVIEW_URL, ReviewClaimState, send_review_claim
from ..tasks import run_async_in_background
from ..telemetry import track_event

STANDARD_MSG = "You've used Smart Notes 20 times! 🥳<br><br>If you're finding it useful and can spare a minute of your time, consider leaving a review on <a href='https://ankiweb.net/shared/info/1531888719'>AnkiWeb</a> to help other people find it."
FREE_MONTH_MSG = "You've used Smart Notes 20 times! 🥳<br><br>Enjoying the plugin? Leave a review on AnkiWeb and get a free month of the Lite plan, on us 🥂"
CLAIMED_MSG = "Thanks! Your free month should be granted in a few minutes."
UNAVAILABLE_MSG = "Thanks for the review! This account has already had its free month."


class RateDialog(QDialog):
    """For some reason QMessageBox doesn't support links (tried everything; it's supposed to) - maybe a PyQt issue or Anki issue. So, I'm using a custom dialog for this."""

    def __init__(self) -> None:
        super().__init__()
        # The free month is for users who haven't paid: trials and the free
        # plan. Paid users see the standard review message.
        free_month = flags.review_free_month and (
            app_state.is_free_trial() or is_free_plan()
        )
        font = QFont()
        font.setBold(True)
        self.text = QLabel(FREE_MONTH_MSG if free_month else STANDARD_MSG)
        self.text.setWordWrap(True)
        self.text.setFont(font)
        self.text.setTextFormat(Qt.TextFormat.RichText)
        self.text.setOpenExternalLinks(True)
        layout = QVBoxLayout()
        layout.addWidget(self.text)

        # The same two steps as the web UI's offer: the server takes the review
        # count at the first click and grants the month once it rises.
        if free_month:
            self.write_button = QPushButton("Write a review")
            self.write_button.clicked.connect(self._write_review)
            self.claim_button = QPushButton("I left a review")
            self.claim_button.clicked.connect(self._claim)
            steps = QHBoxLayout()
            steps.addWidget(self.write_button)
            steps.addWidget(self.claim_button)
            layout.addLayout(steps)

        self.setLayout(layout)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)
        self.setMinimumWidth(400)

    def _write_review(self) -> None:
        openLink(ANKIWEB_REVIEW_URL)
        track_event("clicked_write_review")
        run_async_in_background(
            lambda: send_review_claim("write"),
            on_failure=lambda e: logger.info(f"Review claim write step failed: {e}"),
        )

    def _claim(self) -> None:
        track_event("clicked_left_review")
        self.claim_button.setEnabled(False)
        run_async_in_background(
            lambda: send_review_claim("claim"),
            on_success=self._on_claimed,
            on_failure=self._on_claim_failed,
        )

    def _on_claimed(self, state: ReviewClaimState) -> None:
        self.text.setText(CLAIMED_MSG if state != "unavailable" else UNAVAILABLE_MSG)
        self.write_button.hide()
        self.claim_button.hide()

    def _on_claim_failed(self, e: Exception) -> None:
        logger.info(f"Review claim failed: {e}")
        self.claim_button.setEnabled(True)
