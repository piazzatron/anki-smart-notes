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

from typing import Dict, Union

from anki.notes import Note

from .config import PromptMap, config
from .logger import logger
from .nodes import ChatPayload, FieldNode, TTSPayload
from .notes import get_note_type
from .prompts import get_extras, get_prompt_fields, get_prompts
from .utils import get_fields


def generate_fields_dag(
    note: Note,
    overwrite_fields: bool,
    target_field: Union[str, None] = None,
    override_prompts_map: Union[PromptMap, None] = None,
) -> Dict[str, FieldNode]:
    """Generates a directed acyclic graph of prompts for a note, or a subset of that graph if a target_fields list is passed. Returns a mapping of field -> PromptNode"""
    # - Generates all nodes
    # - Connects them
    # - Optionally trims them if it's target_field mode

    try:
        logger.debug("Generating dag...")
        note_type = get_note_type(note)

        prompts = get_prompts(
            to_lower=True, override_prompts_map=override_prompts_map
        ).get(note_type, None)
        if not prompts:
            logger.debug("generate_fields_dag: no prompts found for note type")
            return {}

        dag: Dict[str, FieldNode] = {}
        fields = get_fields(note_type)

        # Have to iterate over fields to get the canonical capitalization lol
        for field in fields:

            field_lower = field.lower()
            prompt = prompts.get(field_lower)
            if not prompt:
                continue

            extras = get_extras(note_type, field)
            is_custom = extras["use_custom_model"]
            type = extras["type"]
            should_generate_automatically = extras["automatic"]

            payload: Union[ChatPayload, TTSPayload]
            if type == "chat":

                payload = ChatPayload(
                    provider=(
                        extras["chat_provider"] if is_custom else config.chat_provider
                    ),
                    model=extras["chat_model"] if is_custom else config.chat_model,
                    temperature=(
                        extras["chat_temperature"]
                        if is_custom
                        else config.chat_temperature
                    ),
                    prompt=prompt,
                )
            elif type == "tts":
                payload = TTSPayload(
                    provider=(
                        extras["tts_provider"] if is_custom else config.tts_provider
                    ),
                    model=extras["tts_model"] if is_custom else config.tts_model,
                    voice=extras["tts_voice"] if is_custom else config.tts_voice,
                    input=prompt,
                    options={},
                )

            dag[field_lower] = FieldNode(
                field=field_lower,
                field_upper=field,
                out_nodes=[],
                in_nodes=[],
                existing_value=note[field],
                overwrite=overwrite_fields,
                manual=not should_generate_automatically,
                is_target=bool(target_field and field_lower == target_field.lower()),
                payload=payload,
            )

        if not len(dag):
            logger.debug("Unexpectedly empty dag!")
            return dag

        for field, prompt in prompts.items():
            in_fields = get_prompt_fields(prompt)

            for in_field in in_fields:
                if in_field in dag:
                    this_node = dag[field]
                    depends_on = dag[in_field]
                    this_node.in_nodes.append(depends_on)
                    depends_on.out_nodes.append(this_node)

        # If there's a target field, trim
        # the dag to only the input of the target field
        if target_field:
            target_node = dag[target_field.lower()]
            trimmed: Dict[str, FieldNode] = {target_field.lower(): target_node}

            # Add pre
            explore = target_node.in_nodes.copy()
            while len(explore):
                cur = explore.pop()
                cur.generate_despite_manual = True
                trimmed[cur.field] = cur
                explore.extend(cur.in_nodes.copy())

            logger.debug("Generated target fields dag")
            logger.debug(trimmed)
            return trimmed

        logger.debug("Generated dag")
        logger.debug(dag)
        return dag
    except Exception as e:
        logger.error(f"Error creating dag: {e}")
        return {}


def has_cycle(dag: Dict[str, FieldNode]) -> bool:
    """Tests for cycles in a DAG. Returns True if there are cycles, False if there are not."""
    dag = dag.copy()
    for start in dag.values():
        seen = set()
        explore = [start]
        while len(explore):
            cur = explore.pop()
            if cur.field in seen:
                return True
            seen.add(cur.field)
            explore.extend(cur.out_nodes.copy())

    return False


# Lives in here bc there is cycle detection. Not the best place but meh
def prompt_has_error(
    prompt: str,
    note: Note,
    target_field: Union[str, None] = None,
    prompts_map: Union[PromptMap, None] = None,
) -> Union[str, None]:
    """Checks if a prompt has an error. Returns the error message if there is one."""
    note_type = get_note_type(note)
    note_fields = {field.lower() for field in get_fields(note_type)}
    prompt_fields = get_prompt_fields(prompt)

    # Check for referencing invalid fields
    for prompt_field in prompt_fields:
        # Doesn't exist
        if prompt_field not in note_fields:
            return f"Invalid field in prompt: {prompt_field}"
        # Is TTS
        elif get_extras(note_type, prompt_field, prompts_map)["type"] == "tts":
            return "Cannot reference TTS fields in prompts"

    # Can't reference itself
    if target_field and target_field.lower() in prompt_fields:
        return "Cannot reference the target field in the prompt."

    dag = generate_fields_dag(
        note, overwrite_fields=False, override_prompts_map=prompts_map
    )

    if has_cycle(dag):
        return "Smart fields referencing other smart fields cannot make a cycle!! 🔁"

    return None
