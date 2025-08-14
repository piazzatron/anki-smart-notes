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

from anki.cards import Card
from anki.decks import DeckId
from anki.notes import Note
from aqt import mw

from .constants import GLOBAL_DECK_ID
from .decks import deck_id_to_name_map
from .models import DEFAULT_EXTRAS, PromptMap
from .prompts import get_extras, get_prompt_fields, get_prompts_for_note
from .ui.ui_utils import show_message_box
from .utils import get_fields

"""Helpful functions for working with notes"""


def get_note_type(note: Note) -> str:
    """Gets the note type of a note."""
    t = note.note_type()
    if not t:
        raise Exception("Note type not found")
    return t["name"]  # type: ignore


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

    prompts = get_prompts_for_note(note_type, card.did)

    if not prompts:
        return True

    for field in prompts:
        field_exists = field in note and note[field]
        is_automatic = (
            get_extras(note_type=note_type, field=field, deck_id=card.did)
            or DEFAULT_EXTRAS
        )["automatic"]
        if (not field_exists) and is_automatic:
            return False

    return True


def get_field_from_index(note: Note, index: int) -> str | None:
    """Gets the field name from the index of a note."""
    fields = get_fields(get_note_type(note))
    if index < 0 or index >= len(fields):
        return None
    return fields[index]


# TODO: make this work with get_field_from_index, taking in a field name
def is_ai_field(current_field_num: int | None, card: Card) -> str | None:
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

    prompts_for_card = get_prompts_for_note(note_type, card.did, to_lower=True)

    if not prompts_for_card:
        return None

    is_ai = bool(prompts_for_card.get(current_field, None))
    return sorted_fields[current_field_num] if is_ai else None


def has_chained_ai_fields(card: Card) -> bool:
    """Check if a card has any AI fields that depend on other AI fields."""
    return bool(get_chained_ai_fields(get_note_type(card.note()), card.did))


def get_chained_ai_fields(note_type: str, deck_id: DeckId) -> set[str]:
    """Check if a note has any AI fields that depend on other AI fields."""
    res: set[str] = set()
    prompts = get_prompts_for_note(note_type, deck_id, to_lower=True)

    if not prompts:
        return res

    for field, prompt in prompts.items():
        smart_fields = prompts.keys() - {field.lower()}
        input_fields = get_prompt_fields(prompt)

        for input_field in input_fields:
            if input_field in smart_fields:
                res.add(field)
                break

    return res


def get_random_note(note_type: str, deck_id: DeckId) -> Note | None:
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
    selected_note_field: str | None = None,
    prompts_map: PromptMap | None = None,
) -> list[str]:
    """Gets all fields excluding the selected one, if one is selected"""
    fields = get_fields(selected_note_type)
    return [
        field
        for field in fields
        if field != selected_note_field
        and (
            get_extras(
                note_type=selected_note_type,
                field=field,
                prompts=prompts_map,
                deck_id=deck_id,
                fallback_to_global_deck=False,
            )
            or {"type": "chat"}  # Should never happen
        )["type"]
        == "chat"
    ]
