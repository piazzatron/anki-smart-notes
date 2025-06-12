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

from typing import List, Union

from anki.notes import Note
from aqt import mw

from .notes import get_note_type


def get_media_path(note: Note, field: str, format: str) -> str:
    return f"{get_note_type(note)}-{field}-{note.id}.{format}"


def write_media(file_name: str, file: bytes) -> Union[str, None]:
    if not mw or not mw.col:
        return None
    media = mw.col.media
    if not media:
        return None
    return media.write_data(file_name, file)


def trash_files(file_names: List[str]) -> None:
    if not mw or not mw.col:
        return
    media = mw.col.media
    if not media:
        return
    media.trash_files(file_names)
