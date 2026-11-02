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

import html
import re
from typing import Optional

from anki.notes import Note

from .config import config
from .logger import logger
from .prompt_fields import FIELD_PATTERN, get_prompt_fields
from .utils import to_lowercase_dict

# Keep in sync with web/src/features/prompt-tester/htmlToText.ts, which previews it.
_HIDDEN_CONTENT = re.compile(r"<(style|script)\b.*?</\1\s*>|<!--.*?-->", re.I | re.S)
_LINE_BREAK = re.compile(r"</?(?:br|div|p|li|ul|ol|tr|h[1-6])\b[^>]*>", re.I)
_TAG = re.compile(r"<[^>]*>")


def html_to_text(value: str) -> str:
    """Field HTML as the text a reader sees: tags gone, entities decoded, one line per
    block, so list items and divs don't run together."""
    text = _HIDDEN_CONTENT.sub("", value)
    text = _LINE_BREAK.sub("\n", text)
    # Anki's editor writes &nbsp; for ordinary spaces.
    text = html.unescape(_TAG.sub("", text)).replace("\xa0", " ")
    lines = (line.strip() for line in text.splitlines())
    return "\n".join(line for line in lines if line)


def interpolate_prompt(prompt: str, note: Note, strip_html: bool) -> Optional[str]:
    """Interpolates a prompt. Returns none if required source fields are empty.
    With strip_html, field values go in as plain text (`html_to_text`)."""
    fields = get_prompt_fields(prompt)
    if not fields:
        return prompt

    all_note_fields = to_lowercase_dict(note)  # type: ignore[arg-type]
    if strip_html:
        all_note_fields = {
            name: html_to_text(value) for name, value in all_note_fields.items()
        }

    # Lowercase field references inside {{}} while preserving cloze deletions.
    prompt = re.sub(FIELD_PATTERN, lambda x: "{{" + x.group(1).lower() + "}}", prompt)

    values = [all_note_fields.get(field, "") for field in fields]
    if any(values) and (config.allow_empty_fields or all(values)):
        for field, value in zip(fields, values):
            prompt = prompt.replace("{{" + field + "}}", value)
        return prompt

    logger.debug("Prompt has empty fields")
    return None
