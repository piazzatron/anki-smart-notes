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

from anki.sound import play  # type: ignore
from aqt import mw

from .logger import logger


def play_audio(audio: bytes):
    logger.debug("Successfully got audio!")
    if not mw or not mw.col.media:
        logger.error("No mw")
        return
    path = mw.col.media.write_data("smart-notes-test", audio)
    play(path)

    # Cleanup
    mw.col.media.trash_files([path])
