"""Helpful functions for working with prompts and cards"""

from .config import config
import re
from .utils import get_fields, to_lowercase_dict
from anki.notes import Note
from typing import Union


def is_ai_field(current_field_num: int, note: Note):
    """Helper to determine if the current field is an AI field. Returns the non-lowercased field name if it is."""
    if not note:
        return None
    note_type = note.note_type()
    # Sort dem fields and get their names
    sorted_fields = [
        field["name"] for field in sorted(note_type["flds"], key=lambda x: x["ord"])  # type: ignore[index]
    ]
    sorted_fields_lower = [field.lower() for field in sorted_fields]

    if not note_type or not current_field_num:
        return None

    current_field = sorted_fields_lower[current_field_num]
    print(current_field)

    prompts = config.prompts_map
    print(prompts)

    # TODO: some methods to work with this stupid note_types map
    prompts_for_card = to_lowercase_dict(
        (prompts["note_types"].get(note_type["name"], {"fields": {}}).get("fields", {}))
    )

    print(prompts_for_card)

    is_ai = bool(prompts_for_card.get(current_field, None))
    return sorted_fields[current_field_num] if is_ai else None


def get_prompt_fields_lower(prompt: str):
    pattern = r"\{\{(.+?)\}\}"
    fields = re.findall(pattern, prompt)
    return [field.lower() for field in fields]


def validate_prompt(prompt: str, note_type: str, target_field: Union[str, None] = None):
    fields = {field.lower() for field in get_fields(note_type)}
    prompt_fields = get_prompt_fields_lower(prompt)

    # Check for fields that aren't in the card
    for prompt_field in prompt_fields:
        if prompt_field not in fields:
            return False

    # Can't reference itself
    if target_field and target_field.lower() in prompt_fields:
        return False

    return True


def interpolate_prompt(prompt: str, note: Note):
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
        prompt = prompt.replace("{{" + field + "}}", value)

    print("Processed prompt: ", prompt)
    return prompt
