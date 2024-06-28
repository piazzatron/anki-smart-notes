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

from .. import env


def _setup_logger() -> logging.Logger:
    logger = logging.getLogger("smart_notes")

    if env.environment == "DEV":
        logger.setLevel(logging.DEBUG)
        logger.debug("Running in development environment")
    else:
        logger.setLevel(logging.ERROR)
        logger.debug("Running in production environment")

    formatter = logging.Formatter("%(name)s/%(filename)s: [%(levelname)s] %(message)s")
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    # TODO: add a file handler sometime
    logger.addHandler(stream_handler)

    return logger


logger = _setup_logger()
