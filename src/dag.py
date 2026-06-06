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

import traceback
from typing import Optional, Union

from anki.decks import DeckId
from anki.notes import Note

from .logger import logger
from .models import DEFAULT_EXTRAS, FieldExtras, PromptMap
from .models.smart_fields import (
    ChatSmartFieldSettings,
    ImageSmartFieldSettings,
    SmartField,
    TTSSmartFieldSettings,
)
from .nodes import FieldNode
from .prompt_helpers import get_extras, get_prompt_fields
from .services.smart_field_service import get_current_profile_name, smart_field_service
from .utils import get_fields
from .utils.notes_utils import get_note_type


def generate_fields_dag(
    note: Note,
    smart_fields: list[SmartField],
    overwrite_fields: bool,
    target_field: Optional[str] = None,
) -> dict[str, FieldNode]:
    """Generates a directed acyclic graph of prompts for a note, or a subset of that graph if a target_fields list is passed. Returns a mapping of field -> PromptNode"""
    # - Generates all nodes
    # - Connects them
    # - Optionally trims them if it's target_field mode

    try:
        note_type = get_note_type(note)
        smart_fields_by_target = {
            smart_field.target_field_name.lower(): smart_field
            for smart_field in smart_fields
        }

        if not smart_fields_by_target:
            logger.debug("generate_fields_dag: no prompts found for note type")
            return {}

        dag: dict[str, FieldNode] = {}
        note_fields = get_fields(note_type)

        # Have to iterate over fields to get the canonical capitalization lol
        for field in note_fields:
            field_lower = field.lower()
            smart_field = smart_fields_by_target.get(field_lower)
            if not smart_field:
                continue

            dag[field_lower] = FieldNode(
                field=field_lower,
                field_upper=field,
                out_nodes=[],
                in_nodes=[],
                existing_value=note[field],
                overwrite=overwrite_fields,
                manual=not smart_field.enabled,
                is_target=bool(target_field and field_lower == target_field.lower()),
                smart_field=smart_field,
            )

        if not len(dag):
            logger.debug("Unexpectedly empty dag!")
            return dag

        for field_name, smart_field in smart_fields_by_target.items():
            if field_name not in dag:
                continue

            # TTS stores its source field directly; text/image fields store
            # dependencies as {{field}} references inside their prompts.
            settings = smart_field.settings
            if isinstance(settings, TTSSmartFieldSettings):
                in_fields = [settings.source_field_name.lower()]
            elif isinstance(settings, ChatSmartFieldSettings):
                in_fields = get_prompt_fields(settings.prompt_text)
            else:
                in_fields = get_prompt_fields(settings.prompt_text)

            for in_field in in_fields:
                if in_field in dag:
                    this_node = dag[field_name]
                    depends_on = dag[in_field]
                    this_node.in_nodes.append(depends_on)
                    depends_on.out_nodes.append(this_node)

        # If there's a target field, trim
        # the dag to only the input of the target field
        if target_field:
            if target_field.lower() not in dag:
                return {}
            target_node = dag[target_field.lower()]
            trimmed: dict[str, FieldNode] = {target_field.lower(): target_node}

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

        return dag
    except Exception as e:
        logger.error(f"Error creating dag: {e}")
        logger.error(traceback.format_exc())
        return {}


def has_cycle(dag: dict[str, FieldNode]) -> bool:
    """Tests for cycles in a DAG. Returns True if there are cycles, False if there are not."""
    dag = dag.copy()
    for start in dag.values():
        # track both current node and path taken to get there
        explore = [(start, set())]
        while len(explore):
            cur, path = explore.pop()
            if cur.field in path:
                return True
            new_path = path.copy()
            new_path.add(cur.field)
            explore.extend((node, new_path) for node in cur.out_nodes)

    return False


# Lives in here bc there is cycle detection. Not the best place but meh
def prompt_has_error(
    prompt: str,
    note: Note,
    deck_id: DeckId,
    target_field: Optional[str] = None,
    prompts_map: Optional[PromptMap] = None,
) -> Optional[str]:
    """Checks if a prompt has an error. Returns the error message if there is one."""
    note_type = get_note_type(note)
    note_fields = {field.lower() for field in get_fields(note_type)}
    prompt_fields = get_prompt_fields(prompt)

    # Check for referencing invalid fields
    for prompt_field in prompt_fields:
        if prompt_field not in note_fields:
            return f"Invalid field in prompt: {prompt_field}"

        extras = get_extras(note_type, prompt_field, deck_id, prompts_map)
        if extras and extras["type"] in ["tts", "image"]:
            return "Cannot reference TTS or image fields in prompts"

    # Can't reference itself
    if target_field and target_field.lower() in prompt_fields:
        return "Cannot reference the target field in the prompt."

    if prompts_map:
        note_type_model = note.note_type()
        note_type_id = int(note_type_model["id"]) if note_type_model else -1
        dag = generate_fields_dag(
            note,
            smart_fields=smart_fields_from_prompt_map(
                note_type, note_type_id, deck_id, prompts_map
            ),
            overwrite_fields=False,
        )
        if has_cycle(dag):
            return (
                "Smart fields referencing other smart fields cannot make a cycle!! 🔁"
            )

    return None


# TODO: Delete these prompt-map conversion helpers during the smart fields UI
# rewrite. They only exist so the legacy PromptDialog can validate unsaved edits
# before those edits are written to SQLite.
def smart_fields_from_prompt_map(
    note_type: str, note_type_id: int, deck_id: DeckId, prompts_map: PromptMap
) -> list[SmartField]:
    note_type_map = prompts_map["note_types"].get(note_type, {})
    deck_map = note_type_map.get(str(deck_id), {})
    fields = deck_map.get("fields", {})
    extras_by_field = deck_map.get("extras", {})
    profile_name = get_current_profile_name()

    return [
        SmartField(
            id=f"prompt-map:{field}",
            profile_name=profile_name,
            note_type_id=note_type_id,
            deck_id=deck_id,
            target_field_name=field,
            enabled=(extras_by_field.get(field) or DEFAULT_EXTRAS)["automatic"],
            settings=smart_field_settings_from_prompt_parts(
                prompt=prompt,
                extras=extras_by_field.get(field) or DEFAULT_EXTRAS,
            ),
        )
        for field, prompt in fields.items()
    ]


def smart_field_settings_from_prompt_parts(
    prompt: str, extras: FieldExtras
) -> Union[ChatSmartFieldSettings, TTSSmartFieldSettings, ImageSmartFieldSettings]:
    field_type = extras["type"]
    if field_type == "tts":
        source_fields = get_prompt_fields(prompt, lower=False)
        defaults = smart_field_service.get_tts_defaults()
        return TTSSmartFieldSettings(
            source_field_name=source_fields[0] if source_fields else "",
            provider=extras.get("tts_provider") or defaults.provider,
            model=extras.get("tts_model") or defaults.model,
            voice_id=extras.get("tts_voice") or defaults.voice_id,
            uses_default_generation_settings=not extras.get("use_custom_model"),
        )
    if field_type == "image":
        defaults = smart_field_service.get_image_defaults()
        return ImageSmartFieldSettings(
            prompt_text=prompt,
            provider=extras.get("image_provider") or defaults.provider,
            model=extras.get("image_model") or defaults.model,
            uses_default_generation_settings=not extras.get("use_custom_model"),
        )
    defaults = smart_field_service.get_chat_defaults()
    return ChatSmartFieldSettings(
        prompt_text=prompt,
        provider=extras.get("chat_provider") or defaults.provider,
        model=extras.get("chat_model") or defaults.model,
        web_search_enabled=extras.get("chat_web_search") or False,
        reasoning_level=extras.get("chat_reasoning_level") or defaults.reasoning_level,
        uses_default_generation_settings=not extras.get("use_custom_model"),
    )
