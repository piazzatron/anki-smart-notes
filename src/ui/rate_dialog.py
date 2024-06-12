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

from aqt import QDialog, QLabel, QVBoxLayout, Qt, QFont, QDialogButtonBox


class RateDialog(QDialog):
    """For some reason QMessageBox doesn't support links (tried everything; it's supposed to) - maybe a PyQt issue or Anki issue. So, I'm using a custom dialog for this."""

    def __init__(self) -> None:
        super().__init__()
        msg = 'Thanks for using ✨Smart Notes ✨!<br><br> If you\'ve found it useful, please help others find it by <a href="https://ankiweb.net/shared/info/1531888719">leaving a rating on AnkiWeb</a> 👍'
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
