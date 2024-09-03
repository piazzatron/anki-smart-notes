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

from typing import Union

from anki.notes import Note

from .prompts import get_generate_automatically, get_prompts
from .utils import get_fields, to_lowercase_dict

"""Helpful functions for working with notes"""


def get_note_type(note: Note) -> str:
    """Gets the note type of a note."""
    t = note.note_type()
    if not t:
        raise Exception("Note type not found")
    return t["name"]  # type: ignore


def is_note_fully_processed(note: Note) -> bool:
    note_type = get_note_type(note)
    if not note_type:
        return True

    all_prompts = get_prompts()
    prompts = all_prompts.get(note_type, None)

    if not prompts:
        return True

    for field in prompts.keys():
        field_exists = field in note and note[field]
        is_automatic = get_generate_automatically(note_type, field)
        if (not field_exists) and is_automatic:
            return False

    return True


def is_ai_field(current_field_num: int, note: Note) -> Union[str, None]:
    """Helper to determine if the current field is an AI field. Returns the non-lowercased field name if it is."""
    if not note:
        return None

    # Sort dem fields and get their names
    note_type = get_note_type(note)
    sorted_fields = get_fields(note_type)
    sorted_fields_lower = [field.lower() for field in sorted_fields]

    # SNEAKY: current_field_num can be 0
    if current_field_num is None:
        return None

    current_field = sorted_fields_lower[current_field_num]

    prompts_for_card = to_lowercase_dict(get_prompts().get(get_note_type(note), {}))

    is_ai = bool(prompts_for_card.get(current_field, None))
    return sorted_fields[current_field_num] if is_ai else None
