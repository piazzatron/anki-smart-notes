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

import re

# Matches {{field}} references but skips Anki cloze deletions like {{c1::answer}}
FIELD_PATTERN = r"\{\{(?!c\d+::)(.+?)\}\}"


def get_prompt_fields(prompt: str, lower: bool = True) -> list[str]:
    fields = re.findall(FIELD_PATTERN, prompt)
    return [(field.lower() if lower else field) for field in fields]
