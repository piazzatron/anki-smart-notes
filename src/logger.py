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
import sys

from .config import config
from .utils import is_production


def _setup_logger() -> logging.Logger:
    logger = logging.getLogger("smart_notes")
    formatter = logging.Formatter("%(name)s/%(filename)s: [%(levelname)s] %(message)s")
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)

    if is_production() and not config.debug:
        logger.setLevel(logging.ERROR)
        logger.debug("Running in production / debug environment")
    else:
        logger.setLevel(logging.DEBUG)
        logger.debug("Running in development environment")
        file_handler = logging.FileHandler("smart_notes.log", mode="w")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # TODO: add a file handler sometime
    logger.addHandler(stream_handler)
    if config.debug:
        logger.debug("Starting app in debug mode")
    return logger


logger = _setup_logger()
