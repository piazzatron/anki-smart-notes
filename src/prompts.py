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
from typing import Dict, List, Literal, Union

from anki.notes import Note

from .config import FieldExtrasWithDefaults, PromptMap, config
from .logger import logger
from .utils import to_lowercase_dict

EXTRAS_DEFAULT_AUTOMATIC = True


def get_prompts(
    to_lower: bool = False, override_prompts_map: Union[PromptMap, None] = None
) -> Dict[str, Dict[str, str]]:
    """Gets the prompts map. Maps note_type -> {field -> prompt}"""
    prompts_map = {
        note_type: {k: v for k, v in m["fields"].items()}
        for note_type, m in (override_prompts_map or config.prompts_map)[
            "note_types"
        ].items()
    }
    if to_lower:
        prompts_map = {k: to_lowercase_dict(v) for k, v in prompts_map.items()}
    return prompts_map


def get_extras(
    note_type: str,
    note_field: str,
    prompts_map: Union[PromptMap, None] = None,
    type: Union[Literal["chat", "tts"], None] = None,
) -> FieldExtrasWithDefaults:

    # Lowercase the field names
    extras = to_lowercase_dict(
        (prompts_map or config.prompts_map)["note_types"]  # type: ignore
        .get(note_type, {"extras": {}})
        .get("extras", {})
    )

    default_extras: FieldExtrasWithDefaults = {
        "automatic": EXTRAS_DEFAULT_AUTOMATIC,
        "chat_provider": config.chat_provider,
        "chat_model": config.chat_model,
        "chat_temperature": config.chat_temperature,
        "use_custom_model": False,
        "type": type or "chat",
        "tts_model": config.tts_model,
        "tts_provider": config.tts_provider,
        "tts_voice": config.tts_voice,
    }

    # Base extras field might not exist at all
    if not extras:
        return default_extras

    field_extras = extras.get(note_field.lower(), default_extras)

    # Populate missing fields with defaults
    for k, v in default_extras.items():
        if k not in field_extras or field_extras[k] is None:
            field_extras[k] = v
    return field_extras  # type: ignore


def get_generate_automatically(
    note_type: str, note_field: str, prompts_map: Union[PromptMap, None] = None
) -> bool:
    extras = get_extras(note_type, note_field, prompts_map)
    return bool(extras.get("automatic", EXTRAS_DEFAULT_AUTOMATIC))


def get_prompt_fields(prompt: str, lower: bool = True) -> List[str]:
    pattern = r"\{\{(.+?)\}\}"
    fields = re.findall(pattern, prompt)
    return [(field.lower() if lower else field) for field in fields]


def interpolate_prompt(prompt: str, note: Note) -> Union[str, None]:
    """Interpolates a prompt. Returns none if all source field are empty, or if some are empty and we're not allowing empty fields."""
    # Bunch of extra logic to make this whole process case insensitive

    # Regex to pull out any words enclosed in double curly braces
    fields = get_prompt_fields(prompt)
    # For some reason, the user is using a prompt with no fields
    if not fields:
        return prompt
    pattern = r"\{\{(.+?)\}\}"

    # field.lower() -> value map
    all_note_fields = to_lowercase_dict(note)  # type: ignore[arg-type]

    # Lowercase the characters inside {{}} in the prompt
    prompt = re.sub(pattern, lambda x: "{{" + x.group(1).lower() + "}}", prompt)

    allow_empty = config.allow_empty_fields

    # Sub values in prompt
    values = [all_note_fields.get(field, "") for field in fields]

    if any(values) and (allow_empty or all(values)):
        for field, value in zip(fields, values):
            prompt = prompt.replace("{{" + field + "}}", value)
        return prompt

    logger.debug("Prompt has empty fields")
    return None
