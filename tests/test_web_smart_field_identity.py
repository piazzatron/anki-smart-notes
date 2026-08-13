# type: ignore

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

import pytest

from src.web import dto
from tests.fixtures import DECK_ID, NOTE_TYPE_ID


def test_parse_smart_field_update_includes_existing_id():
    update = dto.parse_smart_field_update(
        {
            "id": "existing-smart-field-id",
            "noteTypeId": NOTE_TYPE_ID,
            "deckId": int(DECK_ID),
            "targetFieldName": "Back",
            "fieldType": "chat",
            "enabled": True,
            "settings": {
                "promptText": "Define {{Front}}",
                "provider": "openai",
                "model": "gpt-5",
                "reasoningLevel": "off",
                "webSearchEnabled": False,
                "usesDefaultGenerationSettings": True,
            },
        }
    )

    assert update.id == "existing-smart-field-id"
    assert update.note_type_id == NOTE_TYPE_ID
    assert update.deck_id == DECK_ID
    assert update.target_field_name == "Back"


def test_parse_smart_field_update_requires_id():
    with pytest.raises(ValueError, match="id"):
        dto.parse_smart_field_update(
            {
                "noteTypeId": NOTE_TYPE_ID,
                "deckId": int(DECK_ID),
                "targetFieldName": "Back",
                "fieldType": "chat",
                "enabled": True,
                "settings": {
                    "promptText": "Define {{Front}}",
                    "provider": "openai",
                    "model": "gpt-5",
                    "reasoningLevel": "off",
                    "webSearchEnabled": False,
                    "usesDefaultGenerationSettings": True,
                },
            }
        )


def test_parse_smart_field_update_requires_string_id():
    with pytest.raises(ValueError, match="id must be a string"):
        dto.parse_smart_field_update(
            {
                "id": 123,
                "noteTypeId": NOTE_TYPE_ID,
                "deckId": int(DECK_ID),
                "targetFieldName": "Back",
                "fieldType": "chat",
                "enabled": True,
                "settings": {
                    "promptText": "Define {{Front}}",
                    "provider": "openai",
                    "model": "gpt-5",
                    "reasoningLevel": "off",
                    "webSearchEnabled": False,
                    "usesDefaultGenerationSettings": True,
                },
            }
        )


def test_parse_smart_field_id_requires_id():
    with pytest.raises(ValueError, match="id"):
        dto.parse_smart_field_id({})


def test_parse_smart_field_id_returns_existing_id():
    assert dto.parse_smart_field_id({"id": "existing-smart-field-id"}) == (
        "existing-smart-field-id"
    )
