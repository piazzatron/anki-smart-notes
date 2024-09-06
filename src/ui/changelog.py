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

from typing import List, Tuple, Union

from aqt import QDialog, QDialogButtonBox, QFont, QLabel, QVBoxLayout, mw

from ..config import config
from ..logger import logger
from ..sentry import pinger
from ..tasks import run_async_in_background
from ..utils import get_version, load_file
from .v2_cta import V2CTA
from .webview_dialog import WebviewDialog


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
        logger.error(f"Error parsing changelog: {e}")
        return []


def get_versions(v: str) -> Tuple[int, int]:
    major = v.split(".")[0]
    minor = v.split(".")[1]
    return (int(major), int(minor))


def is_new_major_or_minor_version(v1: str, v2: str):
    (major1, minor1, _) = v1.split(".")
    (major2, minor2, _) = v2.split(".")
    return major1 != major2 or minor1 != minor2


def perform_update_check() -> None:
    """Checks if the version has changed and shows a dialog if it has. Also updates the last seen version in config."""
    try:
        current_version = get_version()
        # prior_version can be None if this is version 1.1.0 which introduces this config field or if this is a first run
        prior_version = config.last_seen_version

        # Always update the last seen version
        config.last_seen_version = current_version

        logger.info(
            f"current version: {current_version}, prior version: {prior_version}, is first use: {not prior_version}"
        )

        # Have to keep this crap around forever because v1 didn't have last_seen_version
        # Only show a dialog if (the major or minor has changed OR it's possibly an upgrade to v1.1.0) and it's not the first use

        if not mw:
            return

        # FIRST RUN
        if not prior_version:
            trial_cta = WebviewDialog(mw, "/trial")
            trial_cta.show()
            run_async_in_background(pinger("show_first_start_cta"))
            return

        if is_new_major_or_minor_version(current_version, prior_version):
            dialog: QDialog
            # Check about showing special v2 changelog
            # Only show the V2 CTA if the prior version was 1.x and the current version is 2.x
            # Don't show it if no prior version bc shouldn't show it on first run
            if (
                get_versions(prior_version)[0] == 1
                and get_versions(current_version)[0] == 2
            ):
                dialog = V2CTA(mw)
                dialog.show()
            else:
                dialog = ChangeLogDialog(prior_version)
                dialog.exec()
    except Exception as e:
        logger.error(f"Error checking for updates: {e}")


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
        cta = QLabel(
            '<a href="https://ankiweb.net/shared/info/1531888719">Help others find Smart Notes by rating it on AnkiWeb<👍a👍>'
        )
        cta.setFont(bold_font)
        cta.setOpenExternalLinks(True)
        layout.addWidget(cta)
        layout.addWidget(QLabel(""))

        for i, (version, changes) in enumerate(change_log):
            if self.prior_version and not is_new_major_or_minor_version(
                version, self.prior_version
            ):
                break
            version_label = QLabel(f"New in Version {version}:")
            version_label.setFont(bold_font)
            # Add spacer
            if i > 0:
                layout.addWidget(QLabel(""))
            layout.addWidget(version_label)
            for change in changes:
                layout.addWidget(QLabel(f"• {change}"))

        # Add standard OK button
        standard_buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        standard_buttons.accepted.connect(self.accept)
        layout.addWidget(standard_buttons)
