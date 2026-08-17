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
from typing import Optional

from anki.notes import Note

from .logger import logger
from .models.smart_fields import (
    ChatSmartFieldSettings,
    SmartField,
    TTSSmartFieldSettings,
)
from .nodes import FieldNode
from .prompt_fields import get_prompt_fields
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
