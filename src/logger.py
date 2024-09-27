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

from .utils import get_file_path, is_production


def setup_logger() -> None:
    global logger

    if not mw:
        return

    formatter = logging.Formatter("%(name)s/%(filename)s: [%(levelname)s] %(message)s")
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)

    # Can't use config directly here to avoid cyclical import
    config = mw.addonManager.getConfig(__name__)
    if not config:
        return

    is_debug = config.get("debug")

    if is_production() and not is_debug:
        logger.setLevel(logging.ERROR)
    else:
        logger.setLevel(logging.DEBUG)

        if not os.getenv("IS_TEST"):
            file_handler = logging.FileHandler(
                get_file_path("smart-notes.log"), mode="w", encoding="utf-8"
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

            if is_debug:
                logger.debug("Starting app in debug mode")

    logger.addHandler(stream_handler)


logger = logging.getLogger("smart_notes")
