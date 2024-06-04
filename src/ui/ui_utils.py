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
