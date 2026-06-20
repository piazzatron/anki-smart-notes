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

import logging
import os
import sys

from aqt import mw

from .utils import get_file_path


def setup_logger() -> None:
    if not mw:
        return

    formatter = logging.Formatter("%(name)s/%(filename)s: [%(levelname)s] %(message)s")
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)

    # Can't use config directly here to avoid cyclical import
    config = mw.addonManager.getConfig(__name__)
    if not config:
        return

    cleanup_logger()

    is_debug = bool(config.get("debug"))
    logger.setLevel(logging.DEBUG if is_debug else logging.INFO)
    logger.addHandler(stream_handler)

    if not os.getenv("IS_TEST"):
        try:
            # We've seen occasional reports of unwritable log files, 
            # so make sure this doesn't block startup. See Sentry issue
            # 7548235574 - something do with a shared Anki folder.
            file_handler = logging.FileHandler(
                get_file_path("smart-notes.log"), mode="w", encoding="utf-8"
            )
        except OSError as exc:
            logger.warning(
                "Could not open Smart Notes log file; "
                f"continuing with console logging only: {exc}"
            )
        else:
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        logger.info(
            "Starting app with debug logging enabled"
            if is_debug
            else "Starting app with info logging enabled"
        )


def cleanup_logger() -> None:
    # Windows refuses to replace/delete add-on files while a FileHandler keeps
    # smart-notes.log open, so cleanup must close handlers, not just drop them.
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()


logger = logging.getLogger("smart_notes")
