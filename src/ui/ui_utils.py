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

from typing import Union
from aqt import QPushButton, QMessageBox


def show_message_box(
    message: str,
    details: Union[str, None] = None,
    custom_ok: Union[str, None] = None,
    show_cancel: bool = False,
):
    msg = QMessageBox()
    msg.setText(message)

    if details:
        msg.setInformativeText(details)

    # TODO: this custom_ok is getting put in the wrong position (left most), idk why
    ok_button = None
    if custom_ok:
        ok_button = QPushButton(custom_ok)
        msg.addButton(ok_button, QMessageBox.ButtonRole.ActionRole)

    else:
        msg.addButton(QMessageBox.StandardButton.Ok)

    if show_cancel:
        msg.addButton(QMessageBox.StandardButton.Cancel)

    val = msg.exec()
    return msg.clickedButton() == ok_button or val == QMessageBox.StandardButton.Ok
