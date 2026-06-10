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

# The web UI wire format, defined in one place (see specs/web-ui-architecture.md
# in the top-level repo). Pure functions mapping domain objects to JSON-ready
# dicts. Builders that read Anki/domain state must be called on the main thread.

import dataclasses
from typing import Any, Optional

from anki.notes import Note

from ..models.smart_fields import SmartField
from ..services.smart_field_service import smart_field_service

SCHEMA_VERSION = 1


def build_state() -> dict[str, Any]:
    """The full `state` event payload. Whole-state push: every state event
    carries everything, so consumers replace their model wholesale."""
    return {
        "schemaVersion": SCHEMA_VERSION,
        "smartFields": [
            _smart_field_dto(field)
            for field in smart_field_service.get_all_smart_fields()
        ],
    }


def build_selection_changed(note: Note, deck_id: Optional[int]) -> dict[str, Any]:
    """`anki.browserSelectionChanged` payload for a single selected note."""
    return {
        "note": {
            "id": note.id,
            "noteTypeId": note.mid,
            "deckId": deck_id,
            "fields": {name: note[name] for name in note.keys()},  # noqa: SIM118
        }
    }


def build_selection_cleared(count: int) -> dict[str, Any]:
    """`anki.browserSelectionChanged` payload when not exactly one note is
    selected — note contents only ship for single selection."""
    return {"note": None, "count": count}


def _smart_field_dto(field: SmartField) -> dict[str, Any]:
    return {
        "id": field.id,
        "noteTypeId": field.note_type_id,
        "deckId": field.deck_id,
        "targetFieldName": field.target_field_name,
        "fieldType": field.field_type,
        "enabled": field.enabled,
        "settings": _camelize_keys(dataclasses.asdict(field.settings)),
    }


def _camelize_keys(data: dict[str, Any]) -> dict[str, Any]:
    return {_camelize(key): value for key, value in data.items()}


def _camelize(snake: str) -> str:
    head, *rest = snake.split("_")
    return head + "".join(part.title() for part in rest)
