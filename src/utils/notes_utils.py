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

from typing import Optional

from anki.cards import Card
from anki.decks import DeckId
from anki.notes import Note
from aqt import mw

from ..constants import GLOBAL_DECK_ID
from ..decks import deck_id_to_name_map
from ..models import PromptMap
from ..models.smart_fields import ChatSmartFieldSettings
from ..prompt_helpers import get_prompt_fields
from ..services.smart_field_service import smart_field_service
from ..ui.ui_utils import show_message_box
from . import get_fields

"""Helpful functions for working with notes"""


def get_note_type(note: Note) -> str:
    """Gets the note type of a note."""
    t = note.note_type()
    if not t:
        raise Exception("Note type not found")
    return t["name"]  # type: ignore


def get_note_type_id(note: Note) -> int:
    """Gets the note type id of a note."""
    t = note.note_type()
    if not t:
        raise Exception("Note type not found")
    return int(t["id"])


def get_note_type_id_from_name(note_type: str) -> Optional[int]:
    if not mw or not mw.col:
        return None
    model = mw.col.models.by_name(note_type)
    if not model:
        return None
    return int(model["id"])


def get_note_types() -> list[str]:
    if not mw or not mw.col:
        return []
    models = mw.col.models.all()
    return [model["name"] for model in models]


def is_card_fully_processed(card: Card) -> bool:
    note = card.note()
    note_type = get_note_type(note)
    if not note_type:
        return True

    smart_fields = smart_field_service.get_smart_fields_for_note(
        get_note_type_id(note), card.did, include_global=True
    )
    if not smart_fields:
        return True

    for smart_field in smart_fields:
        field = smart_field.target_field_name
        field_exists = field in note and note[field]
        if (not field_exists) and smart_field.enabled:
            return False

    return True


def get_field_from_index(note: Note, index: int) -> Optional[str]:
    """Gets the field name from the index of a note."""
    fields = get_fields(get_note_type(note))
    if index < 0 or index >= len(fields):
        return None
    return fields[index]


# TODO: make this work with get_field_from_index, taking in a field name
def is_ai_field(current_field_num: Optional[int], card: Card) -> Optional[str]:
    """Helper to determine if the current field is an AI field. Returns the non-lowercased field name if it is."""
    if not card:
        return None

    # Sort dem fields and get their names
    note_type = get_note_type(card.note())
    sorted_fields = get_fields(note_type)
    sorted_fields_lower = [field.lower() for field in sorted_fields]

    # SNEAKY: current_field_num can be 0
    if current_field_num is None:
        return None

    current_field = sorted_fields_lower[current_field_num]

    smart_fields = smart_field_service.get_smart_fields_for_note(
        get_note_type_id(card.note()), card.did, include_global=True
    )
    smart_field_names = {
        smart_field.target_field_name.lower() for smart_field in smart_fields
    }
    if not smart_field_names:
        return None

    is_ai = current_field in smart_field_names
    return sorted_fields[current_field_num] if is_ai else None


def get_chained_ai_fields(note_type: str, deck_id: DeckId) -> set[str]:
    """Check if a note has any AI fields that depend on other AI fields."""
    res: set[str] = set()
    if not mw or not mw.col:
        return res
    note_type_id = get_note_type_id_from_name(note_type)
    if note_type_id is None:
        return res

    smart_fields = smart_field_service.get_smart_fields_for_note(
        note_type_id, deck_id, include_global=True
    )
    if not smart_fields:
        return res

    smart_field_names = {
        smart_field.target_field_name.lower() for smart_field in smart_fields
    }
    for smart_field in smart_fields:
        if not isinstance(smart_field.settings, ChatSmartFieldSettings):
            continue
        field = smart_field.target_field_name.lower()
        other_smart_fields = smart_field_names - {field}
        input_fields = get_prompt_fields(smart_field.settings.prompt_text)

        for input_field in input_fields:
            if input_field in other_smart_fields:
                res.add(field)
                break

    return res


def get_random_note(note_type: str, deck_id: DeckId) -> Optional[Note]:
    if not mw or not mw.col:
        return None

    # Try finding in custom deck first, and then fall back if not
    if deck_id != GLOBAL_DECK_ID:
        deck_name = deck_id_to_name_map().get(deck_id, None)
        # Need to handle the possibility that the deck is top level or leaf level
        query = f'note:"{note_type}" (deck:"*::{deck_name}" or deck:"{deck_name}")'
        sample_note_ids = mw.col.find_notes(query)
        if sample_note_ids:
            return mw.col.get_note(sample_note_ids[0])

    query = f'note:"{note_type}"'
    sample_note_ids = mw.col.find_notes(query)

    if not sample_note_ids:
        show_message_box("No cards found for this note type.")
        return None

    return mw.col.get_note(sample_note_ids[0])


def get_valid_fields_for_prompt(
    selected_note_type: str,
    deck_id: DeckId,
    selected_note_field: Optional[str] = None,
    prompts_map: Optional[PromptMap] = None,
) -> list[str]:
    """Gets all fields excluding the selected one, if one is selected"""
    fields = get_fields(selected_note_type)
    note_type_id = get_note_type_id_from_name(selected_note_type)
    if note_type_id is None:
        return [field for field in fields if field != selected_note_field]

    non_chat_fields = {
        smart_field.target_field_name
        for smart_field in smart_field_service.get_smart_fields_for_note(
            note_type_id,
            deck_id,
            include_global=False,
        )
        if not isinstance(smart_field.settings, ChatSmartFieldSettings)
    }

    return [
        field
        for field in fields
        if field != selected_note_field and field not in non_chat_fields
    ]
