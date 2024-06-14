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

from aqt import QDialog, QLabel, QVBoxLayout, QFont, QDialogButtonBox
from typing import List, Tuple, Union
import json

from ..utils import load_file

from .ui_utils import show_message_box
from ..config import config


def get_version() -> str:
    manifest = load_file("manifest.json")
    return json.loads(manifest)["human_version"]  # type: ignore


def parse_changelog() -> List[Tuple[str, List[str]]]:
    changelog = load_file("changelog.md")
    versions: List[Tuple[str, List[str]]] = []

    try:
        for line in changelog.split("\n"):
            line = line.strip()

            if not line:
                continue
            if line.startswith("# "):
                # trim out starting # and whitespace and v
                version = line[3:]
                versions.append((version, []))
            else:
                versions[-1][1].append(line[2:])
        return versions

    # TODO: we shouldn't really need a try/catch here since this is programmer
    # error if the changelog is unparseable, but this code is still a bit brittle so better safe than sorry
    except Exception as e:
        print(f"Error parsing changelog: {e}")
        return []


def perform_update_check() -> None:
    """Checks if the version has changed and shows a dialog if it has. Also updates the last seen version in config."""
    current_version = get_version()
    prior_version = config.last_seen_version
    is_first_use = config.times_used == 0

    # Always update the last seen version
    config.last_seen_version = current_version

    print(
        f"SmartNotes version check: current version: {current_version}, prior version: {prior_version}, is first use: {is_first_use}"
    )

    # Only show a dialog if the version has changed and it's not the first use
    if current_version != prior_version and not is_first_use:
        dialog = ChangeLogDialog(prior_version)
        dialog.exec()


class ChangeLogDialog(QDialog):
    """Fancy version dialog that shows the changelog since the last version."""

    prior_version: Union[str, None]

    def __init__(self, prior_version: Union[str, None]) -> None:
        super().__init__()
        self.prior_version = prior_version
        self.setup_ui()

    def setup_ui(self) -> None:
        current_version = get_version()
        change_log = parse_changelog()

        layout = QVBoxLayout()
        self.setLayout(layout)
        header_font = QFont()
        header_font.setBold(True)
        header_font.setPointSize(16)
        bold_font = QFont()
        bold_font.setBold(True)

        header = QLabel(f"Smart Notes has updated to version {current_version}! 🥳")
        header.setFont(header_font)

        self.setWindowTitle(f"Smart Notes Changelog")

        layout.addWidget(header)
        layout.addWidget(
            QLabel("We've added shiny new features since you were last here.")
        )
        layout.addWidget(QLabel(""))

        for i, (version, changes) in enumerate(change_log):
            if version == self.prior_version:
                break
            version_label = QLabel(f"New in Version {version}:")
            version_label.setFont(bold_font)
            # Add spacer
            if i > 0:
                layout.addWidget(QLabel(""))
            layout.addWidget(version_label)
            for change in changes:
                layout.addWidget(QLabel(f"• {change}"))

        cta = QLabel(
            '<a href="https://ankiweb.net/shared/info/1531888719">Help others find Smart Notes by rating it on AnkiWeb! 🌟</a>'
        )
        cta.setFont(bold_font)
        cta.setOpenExternalLinks(True)

        layout.addWidget(QLabel(""))
        layout.addWidget(cta)
        layout.addWidget(QLabel(""))

        # Add standard OK button
        standard_buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        standard_buttons.accepted.connect(self.accept)
        layout.addWidget(standard_buttons)
