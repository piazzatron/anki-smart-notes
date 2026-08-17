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
from typing import Optional

from anki.notes import Note

from .config import config
from .logger import logger
from .prompt_fields import FIELD_PATTERN, get_prompt_fields
from .utils import to_lowercase_dict


def interpolate_prompt(prompt: str, note: Note) -> Optional[str]:
    """Interpolates a prompt. Returns none if required source fields are empty."""
    fields = get_prompt_fields(prompt)
    if not fields:
        return prompt

    all_note_fields = to_lowercase_dict(note)  # type: ignore[arg-type]

    # Lowercase field references inside {{}} while preserving cloze deletions.
    prompt = re.sub(FIELD_PATTERN, lambda x: "{{" + x.group(1).lower() + "}}", prompt)

    values = [all_note_fields.get(field, "") for field in fields]
    if any(values) and (config.allow_empty_fields or all(values)):
        for field, value in zip(fields, values):
            prompt = prompt.replace("{{" + field + "}}", value)
        return prompt

    logger.debug("Prompt has empty fields")
    return None
