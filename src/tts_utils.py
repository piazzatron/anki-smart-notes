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

from aqt import gui_hooks, mw, sound

from .logger import logger


def play_audio(audio: bytes):
    logger.debug("Successfully got audio!")
    if not mw or not mw.col or not mw.col.media:
        logger.error("No mw")
        return

    path = mw.col.media.write_data("smart-notes-test", audio)

    def on_end(_):
        if not mw or not mw.col or not mw.col.media:
            logger.error("No mw")
            return
        logger.debug("Finished playing audio, cleaning up file")
        mw.col.media.trash_files([path])
        gui_hooks.av_player_did_end_playing.remove(on_end)

    gui_hooks.av_player_did_end_playing.append(on_end)
    sound.av_player.play_file(path)
