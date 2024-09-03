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

from .prompts import get_generate_automatically, get_prompt_fields, get_prompts
from .ui.ui_utils import show_message_box
from .utils import get_fields, to_lowercase_dict

"""Helpful functions for working with notes"""


def get_note_type(note: Note) -> str:
    """Gets the note type of a note."""
    t = note.note_type()
    if not t:
        raise Exception("Note type not found")
    return t["name"]  # type: ignore


def get_note_types() -> List[str]:
    if not mw or not mw.col:
        return []
    models = mw.col.models.all()
    return [model["name"] for model in models]


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


def has_chained_ai_fields(note_type: str) -> bool:
    """Check if a note has any AI fields that depend on other AI fields."""
    return bool(get_chained_ai_fields(note_type))


def get_chained_ai_fields(note_type: str) -> set[str]:
    """Check if a note has any AI fields that depend on other AI fields."""
    res: set[str] = set()
    prompts = get_prompts(to_lower=True).get(note_type, None)

    if not prompts:
        return res

    for field, prompt in prompts.items():
        smart_fields = prompts.keys() - {field.lower()}
        input_fields = get_prompt_fields(prompt)

        for input_field in input_fields:
            if input_field in smart_fields:
                res.add(field)
                break

    return res


def get_random_note(note_type: str) -> Union[Note, None]:
    if not mw or not mw.col:
        return None

    sample_note_ids = mw.col.find_notes(f'note:"{note_type}"')

    if not sample_note_ids:
        show_message_box("No cards found for this note type.")
        return None

    return mw.col.get_note(sample_note_ids[0])
