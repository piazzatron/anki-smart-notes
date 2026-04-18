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

from aqt import QDialog, QDialogButtonBox, QFont, QLabel, Qt, QVBoxLayout

from ..feature_flags import flags

STANDARD_MSG = "You've used Smart Notes 20 times! 🥳<br><br>If you're finding it useful and can spare a minute of your time, consider leaving a review on <a href='https://ankiweb.net/shared/info/1531888719'>AnkiWeb</a> to help other people find it."
FREE_MONTH_MSG = "You've used Smart Notes 20 times! 🥳<br><br> Enjoying the plugin? Leave a review on <a href='https://ankiweb.net/shared/info/1531888719'>AnkiWeb</a> and email <a href='mailto:support@smart-notes.xyz'>support@smart-notes.xyz</a> for a free month of the Lite plan, on us 🥂"


class RateDialog(QDialog):
    """For some reason QMessageBox doesn't support links (tried everything; it's supposed to) - maybe a PyQt issue or Anki issue. So, I'm using a custom dialog for this."""

    def __init__(self) -> None:
        super().__init__()
        # The popup is already gated to free-trial users in bump_usage_counter,
        # so is_free_trial() is implicit at this point — only the server flag needs checking.
        msg = FREE_MONTH_MSG if flags.review_free_month else STANDARD_MSG
        font = QFont()
        font.setBold(True)
        text = QLabel(msg)
        text.setWordWrap(True)
        text.setFont(font)
        text.setTextFormat(Qt.TextFormat.RichText)
        text.setOpenExternalLinks(True)
        layout = QVBoxLayout()
        layout.addWidget(text)

        self.setLayout(layout)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)
        self.setMinimumWidth(400)
