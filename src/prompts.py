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
from copy import deepcopy
from typing import Any, Dict, List, Optional, Union, cast

from anki.decks import DeckId
from anki.notes import Note

from .config import config
from .constants import GLOBAL_DECK_ID
from .decks import deck_id_to_name_map
from .logger import logger
from .models import (
    DEFAULT_EXTRAS,
    FieldExtras,
    OverridableChatOptions,
    OverridableChatOptionsDict,
    OverridableImageOptions,
    OverridableImageOptionsDict,
    OverrideableTTSOptionsDict,
    PromptMap,
    SmartFieldType,
    overridable_chat_options,
    overridable_image_options,
    overridable_tts_options,
)
from .utils import to_lowercase_dict

EXTRAS_DEFAULT_AUTOMATIC = True


def get_prompts_for_note(
    note_type: str,
    deck_id: DeckId,
    to_lower: bool = False,
    override_prompts_map: Union[PromptMap, None] = None,
    fallback_to_global_deck=True,
) -> Union[Dict[str, str], None]:
    all_prompts = get_all_prompts(to_lower, override_prompts_map)
    prompts_for_note_type = all_prompts.get(note_type, {})
    deck_prompts = deepcopy(prompts_for_note_type.get(deck_id, {}))
    global_prompts = deepcopy(prompts_for_note_type.get(GLOBAL_DECK_ID, {}))

    # Add any missing global prompts
    if fallback_to_global_deck:
        for field, prompt in global_prompts.items():
            if not field in deck_prompts:
                deck_prompts[field] = prompt

    return deck_prompts


# If for some reason extras don't exist for this note type, return None
def get_extras(
    note_type: str,
    field: str,
    deck_id: DeckId,
    prompts: Union[PromptMap, None] = None,
    fallback_to_global_deck: bool = True,
) -> Optional[FieldExtras]:

    # Lowercase the field names
    deck_extras = to_lowercase_dict(
        (prompts or config.prompts_map)["note_types"]  # type: ignore
        .get(note_type, {})
        .get(str(deck_id), {})
        .get("extras", {})
    )

    global_extras = to_lowercase_dict(
        (prompts or config.prompts_map)["note_types"]  # type: ignore
        .get(note_type, {})
        .get(str(GLOBAL_DECK_ID), {})
        .get("extras", {})
    )

    return deck_extras.get(field.lower()) or (
        global_extras.get(field.lower()) if fallback_to_global_deck else None
    )


def get_all_prompts(
    to_lower: bool = False, override_prompts_map: Union[PromptMap, None] = None
) -> Dict[str, Dict[DeckId, Dict[str, str]]]:
    """Gets the prompts map. Maps note_type -> deck -> {field -> prompt}"""
    prompts_map = {
        note_type: {
            # Tricky str -> int convert here
            cast(DeckId, int(deck)): {
                field: prompt
                for field, prompt in note_type_map.get("fields", {}).items()
            }
            for deck, note_type_map in decks_dict.items()
        }
        for note_type, decks_dict in (override_prompts_map or config.prompts_map)[
            "note_types"
        ].items()
    }

    # Lowercase just the field names
    if to_lower:
        prompts_map = {
            note_type: {
                deck: to_lowercase_dict(fields) for deck, fields in deck.items()
            }
            for note_type, deck in prompts_map.items()
        }

    return prompts_map


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


def add_or_update_prompts(
    prompts_map: PromptMap,
    note_type: str,
    deck_id: DeckId,
    field: str,
    prompt: str,
    is_automatic: bool,
    is_custom_model: bool,
    type: SmartFieldType,
    tts_options: OverrideableTTSOptionsDict,
    chat_options: Dict[OverridableChatOptions, Any],
    image_options: Dict[OverridableImageOptions, Any],
) -> PromptMap:
    new_prompts_map = deepcopy(prompts_map)

    logger.debug(f"Trying to set prompt for {note_type}, {field}, {prompt}")

    # If note type does not exist, add
    if not new_prompts_map["note_types"].get(note_type):
        new_prompts_map["note_types"][note_type] = {}

    # If deck type does not exist within the note type, add
    if not new_prompts_map["note_types"][note_type].get(str(deck_id)):
        new_prompts_map["note_types"][note_type][str(deck_id)] = {
            "fields": {},
            "extras": {},
        }

    new_prompts_map["note_types"][note_type][str(deck_id)]["fields"][field] = prompt

    # Write out extras
    extras = (
        get_extras(
            prompts=new_prompts_map,
            note_type=note_type,
            field=field,
            deck_id=deck_id,
            fallback_to_global_deck=False,
        )
        or DEFAULT_EXTRAS
    )

    # Set common fields
    extras["type"] = type
    extras["automatic"] = is_automatic
    extras["use_custom_model"] = is_custom_model

    # If we're doing custom settings, write out extra config
    if is_custom_model:
        overrideable_options: Union[OverridableChatOptionsDict, OverridableImageOptionsDict, OverrideableTTSOptionsDict] = {  # type: ignore
            "chat": chat_options,
            "tts": tts_options,
            "image": image_options,
        }[
            type
        ]

        # Overwrite any extras fields if they have been passed in
        for k, v in overrideable_options.items():
            extras[k] = v if v is not None else extras[k]  # type: ignore

    # Otherwise need to delete any custom config if it's not being used
    else:
        for k in (
            overridable_chat_options
            + overridable_tts_options
            + overridable_image_options
        ):
            extras[k] = None

    # Write em out
    new_prompts_map["note_types"][note_type][str(deck_id)]["extras"][field] = extras
    return new_prompts_map


def remove_prompt(
    prompts_map: PromptMap, note_type: str, deck_id: DeckId, field: str
) -> PromptMap:
    removed_map = deepcopy(prompts_map)

    logger.debug(f"Removing {note_type}, {field}, {deck_id_to_name_map()[deck_id]}")

    removed_map["note_types"][note_type][str(deck_id)]["fields"].pop(field)
    removed_map["note_types"][note_type][str(deck_id)]["extras"].pop(field)

    # If there are no more fields for this deck, pop the deck
    if not len(removed_map["note_types"][note_type][str(deck_id)]["fields"]):
        removed_map["note_types"][note_type].pop(str(deck_id))

    # If no more decks for this note, pop the note
    if not len(removed_map["note_types"][note_type]):
        removed_map["note_types"].pop(note_type)

    return removed_map
