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
