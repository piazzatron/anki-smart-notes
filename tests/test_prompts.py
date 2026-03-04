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

from copy import deepcopy
from typing import Any

import aqt  # noqa: F401
import pytest
from attr import dataclass


@dataclass
class MockNote:
    _data: dict[str, Any]

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value):
        self._data[key] = value

    def __contains__(self, key):
        return key in self._data

    def items(self):
        return self._data.items()


@dataclass
class MockConfig:
    prompts_map: Any = None
    allow_empty_fields: bool = False


DEFAULT_TTS_OPTIONS = {
    "tts_model": None,
    "tts_provider": None,
    "tts_voice": None,
    "tts_strip_html": None,
}

DEFAULT_CHAT_OPTIONS = {
    "chat_provider": None,
    "chat_model": None,
    "chat_temperature": None,
    "chat_markdown_to_html": None,
    "chat_web_search": None,
}

DEFAULT_IMAGE_OPTIONS = {
    "image_model": None,
    "image_provider": None,
}


def make_extras():
    return {
        "automatic": True,
        "type": "chat",
        "use_custom_model": False,
        "chat_model": None,
        "chat_provider": None,
        "chat_temperature": None,
        "chat_markdown_to_html": None,
        "chat_web_search": None,
        "tts_model": None,
        "tts_provider": None,
        "tts_voice": None,
        "tts_strip_html": None,
        "image_provider": None,
        "image_model": None,
    }


def make_prompts_map(note_type, deck_id, fields, extras):
    return {
        "note_types": {
            note_type: {
                str(deck_id): {
                    "fields": deepcopy(fields),
                    "extras": deepcopy(extras),
                }
            }
        }
    }


def setup_prompts(monkeypatch, prompts_map):
    import src.prompts

    c = MockConfig(prompts_map=prompts_map)
    monkeypatch.setattr(src.prompts, "config", c)
    monkeypatch.setattr(
        src.prompts,
        "deck_id_to_name_map",
        lambda: {1: "Default", 2: "Spanish"},
    )
    return c


@pytest.mark.parametrize(
    "prompt, expected",
    [
        ("{{Front}}", ["front"]),
        ("{{Front}} and {{Back}}", ["front", "back"]),
        ("{{c1::answer}}", []),
        ("{{c2::word::hint}}", []),
        ("{{c10::something}}", []),
        ("{{Front}} with {{c1::answer}}", ["front"]),
        (
            "Generate a sentence using {{Word}} where the answer is {{c1::hidden}}",
            ["word"],
        ),
        ("{{Front}} {{c1::cloze1}} {{Back}} {{c2::cloze2}}", ["front", "back"]),
        ("no fields here", []),
        ("{{Field With Spaces}}", ["field with spaces"]),
    ],
)
def test_get_prompt_fields(prompt, expected):
    from src.prompts import get_prompt_fields

    assert get_prompt_fields(prompt) == expected


@pytest.mark.parametrize(
    "prompt, expected",
    [
        ("{{Front}}", ["Front"]),
        ("{{c1::answer}}", []),
        ("{{Front}} {{c1::answer}}", ["Front"]),
    ],
)
def test_get_prompt_fields_no_lower(prompt, expected):
    from src.prompts import get_prompt_fields

    assert get_prompt_fields(prompt, lower=False) == expected


@pytest.mark.parametrize(
    "prompt, note_data, allow_empty, expected",
    [
        (
            "Define {{Front}}",
            {"Front": "hello"},
            False,
            "Define hello",
        ),
        (
            "{{Front}} with {{c1::cloze}}",
            {"Front": "hello"},
            False,
            "hello with {{c1::cloze}}",
        ),
        (
            "Use {{Word}} in a sentence: {{c1::answer}} and {{c2::another::hint}}",
            {"Word": "apple"},
            False,
            "Use apple in a sentence: {{c1::answer}} and {{c2::another::hint}}",
        ),
        (
            "{{c1::only cloze}}",
            {},
            False,
            "{{c1::only cloze}}",
        ),
        (
            "{{Front}} and {{Back}}",
            {"Front": "hello", "Back": "world"},
            False,
            "hello and world",
        ),
        (
            "{{Front}} and {{Back}}",
            {"Front": "hello", "Back": ""},
            False,
            None,
        ),
        (
            "{{Front}} and {{Back}}",
            {"Front": "hello", "Back": ""},
            True,
            "hello and ",
        ),
    ],
)
def test_interpolate_prompt(prompt, note_data, allow_empty, expected, monkeypatch):
    import src.prompts

    c = MockConfig(allow_empty_fields=allow_empty)
    monkeypatch.setattr(src.prompts, "config", c)

    from src.prompts import interpolate_prompt

    note = MockNote(data=note_data)
    result = interpolate_prompt(prompt, note)
    assert result == expected


class TestMoveSmartField:
    def test_move_field_removes_old_and_adds_new(self, monkeypatch):
        from src.prompts import add_or_update_prompts, remove_prompt

        extras = make_extras()
        prompts_map = make_prompts_map(
            "Basic", 1, {"Back": "{{Front}}"}, {"Back": extras}
        )
        setup_prompts(monkeypatch, prompts_map)

        removed = remove_prompt(prompts_map, "Basic", 1, "Back")
        result = add_or_update_prompts(
            prompts_map=removed,
            note_type="Basic",
            deck_id=1,
            field="Extra",
            prompt="{{Front}}",
            is_automatic=True,
            is_custom_model=False,
            type="chat",
            tts_options=DEFAULT_TTS_OPTIONS,
            chat_options=DEFAULT_CHAT_OPTIONS,
            image_options=DEFAULT_IMAGE_OPTIONS,
        )

        assert "Extra" in result["note_types"]["Basic"]["1"]["fields"]
        assert result["note_types"]["Basic"]["1"]["fields"]["Extra"] == "{{Front}}"
        assert "Back" not in result["note_types"]["Basic"]["1"]["fields"]

    def test_move_field_to_different_note_type(self, monkeypatch):
        from src.prompts import add_or_update_prompts, remove_prompt

        extras = make_extras()
        prompts_map = make_prompts_map(
            "Basic", 1, {"Back": "{{Front}}"}, {"Back": extras}
        )
        setup_prompts(monkeypatch, prompts_map)

        removed = remove_prompt(prompts_map, "Basic", 1, "Back")
        result = add_or_update_prompts(
            prompts_map=removed,
            note_type="Cloze",
            deck_id=1,
            field="Extra",
            prompt="{{Text}}",
            is_automatic=True,
            is_custom_model=False,
            type="chat",
            tts_options=DEFAULT_TTS_OPTIONS,
            chat_options=DEFAULT_CHAT_OPTIONS,
            image_options=DEFAULT_IMAGE_OPTIONS,
        )

        assert "Basic" not in result["note_types"]
        assert "Extra" in result["note_types"]["Cloze"]["1"]["fields"]

    def test_move_field_to_different_deck(self, monkeypatch):
        from src.prompts import add_or_update_prompts, remove_prompt

        extras = make_extras()
        prompts_map = make_prompts_map(
            "Basic", 1, {"Back": "{{Front}}"}, {"Back": extras}
        )
        setup_prompts(monkeypatch, prompts_map)

        removed = remove_prompt(prompts_map, "Basic", 1, "Back")
        result = add_or_update_prompts(
            prompts_map=removed,
            note_type="Basic",
            deck_id=2,
            field="Back",
            prompt="{{Front}}",
            is_automatic=True,
            is_custom_model=False,
            type="chat",
            tts_options=DEFAULT_TTS_OPTIONS,
            chat_options=DEFAULT_CHAT_OPTIONS,
            image_options=DEFAULT_IMAGE_OPTIONS,
        )

        assert "1" not in result["note_types"]["Basic"]
        assert "Back" in result["note_types"]["Basic"]["2"]["fields"]

    def test_overwrite_existing_field_rule(self, monkeypatch):
        from src.prompts import add_or_update_prompts, remove_prompt

        extras_back = make_extras()
        extras_extra = make_extras()
        prompts_map = {
            "note_types": {
                "Basic": {
                    "1": {
                        "fields": {
                            "Back": "{{Front}}",
                            "Extra": "old prompt",
                        },
                        "extras": {
                            "Back": extras_back,
                            "Extra": extras_extra,
                        },
                    }
                }
            }
        }
        setup_prompts(monkeypatch, prompts_map)

        removed = remove_prompt(prompts_map, "Basic", 1, "Back")
        result = add_or_update_prompts(
            prompts_map=removed,
            note_type="Basic",
            deck_id=1,
            field="Extra",
            prompt="new prompt for extra",
            is_automatic=True,
            is_custom_model=False,
            type="chat",
            tts_options=DEFAULT_TTS_OPTIONS,
            chat_options=DEFAULT_CHAT_OPTIONS,
            image_options=DEFAULT_IMAGE_OPTIONS,
        )

        assert "Back" not in result["note_types"]["Basic"]["1"]["fields"]
        assert (
            result["note_types"]["Basic"]["1"]["fields"]["Extra"]
            == "new prompt for extra"
        )

    def test_remove_prompt_cleans_up_empty_structures(self, monkeypatch):
        from src.prompts import remove_prompt

        extras = make_extras()
        prompts_map = make_prompts_map(
            "Basic", 1, {"Back": "{{Front}}"}, {"Back": extras}
        )
        setup_prompts(monkeypatch, prompts_map)

        removed = remove_prompt(prompts_map, "Basic", 1, "Back")
        assert "Basic" not in removed["note_types"]

    def test_save_to_same_field_no_removal_needed(self, monkeypatch):
        from src.prompts import add_or_update_prompts

        extras = make_extras()
        prompts_map = make_prompts_map(
            "Basic", 1, {"Back": "{{Front}}"}, {"Back": extras}
        )
        setup_prompts(monkeypatch, prompts_map)

        result = add_or_update_prompts(
            prompts_map=prompts_map,
            note_type="Basic",
            deck_id=1,
            field="Back",
            prompt="updated prompt {{Front}}",
            is_automatic=True,
            is_custom_model=False,
            type="chat",
            tts_options=DEFAULT_TTS_OPTIONS,
            chat_options=DEFAULT_CHAT_OPTIONS,
            image_options=DEFAULT_IMAGE_OPTIONS,
        )

        assert (
            result["note_types"]["Basic"]["1"]["fields"]["Back"]
            == "updated prompt {{Front}}"
        )
