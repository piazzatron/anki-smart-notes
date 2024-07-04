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

"""Helpful functions for working with prompts and cards"""

import re
from typing import Dict, Union

from anki.notes import Note

from .config import config
from .utils import get_fields, to_lowercase_dict


def get_prompts() -> Dict[str, Dict[str, str]]:
    """Gets the prompts map. Does not lowercase anything."""
    return {
        note_type: {k: v for k, v in m["fields"].items()}
        for note_type, m in config.prompts_map["note_types"].items()
    }


def get_prompt_fields_lower(prompt: str):
    pattern = r"\{\{(.+?)\}\}"
    fields = re.findall(pattern, prompt)
    return [field.lower() for field in fields]


def prompt_has_error(
    prompt: str, note_type: str, target_field: Union[str, None] = None
) -> Union[str, None]:
    """Checks if a prompt has an error. Returns the error message if there is one."""
    note_fields = {field.lower() for field in get_fields(note_type)}
    prompt_fields = get_prompt_fields_lower(prompt)
    existing_fields = to_lowercase_dict(get_prompts().get(note_type, {}))

    # Check for fields that aren't in the card
    for prompt_field in prompt_fields:
        if prompt_field not in note_fields:
            return f"Invalid field in prompt: {prompt_field}"
        if prompt_field in existing_fields:
            return f"Can't reference other smart fields ({prompt_field}) in the prompt. (...yet 😈)"

    # Can't reference itself
    if target_field and target_field.lower() in prompt_fields:
        return "Cannot reference the target field in the prompt."

    return None


def interpolate_prompt(prompt: str, note: Note) -> Union[str, None]:
    """Interpolates a prompt. Returns none if a source field is empty."""
    # Bunch of extra logic to make this whole process case insensitive

    # Regex to pull out any words enclosed in double curly braces
    fields = get_prompt_fields_lower(prompt)
    pattern = r"\{\{(.+?)\}\}"

    # field.lower() -> value map
    all_note_fields = to_lowercase_dict(note)  # type: ignore[arg-type]

    # Lowercase the characters inside {{}} in the prompt
    prompt = re.sub(pattern, lambda x: "{{" + x.group(1).lower() + "}}", prompt)

    # Sub values in prompt
    for field in fields:
        value = all_note_fields.get(field, "")
        if not value:
            return None
        prompt = prompt.replace("{{" + field + "}}", value)

    return prompt
