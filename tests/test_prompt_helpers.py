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

import aqt  # noqa: F401
import pytest
from fixtures import MockConfig, MockNote


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
    from src.prompt_fields import get_prompt_fields

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
    from src.prompt_fields import get_prompt_fields

    assert get_prompt_fields(prompt, lower=False) == expected


@pytest.mark.parametrize(
    "prompt, note_data, allow_empty, expected",
    [
        ("Define {{Front}}", {"Front": "hello"}, False, "Define hello"),
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
        ("{{c1::only cloze}}", {}, False, "{{c1::only cloze}}"),
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
    import src.prompt_helpers

    monkeypatch.setattr(
        src.prompt_helpers,
        "config",
        MockConfig(allow_empty_fields=allow_empty),
    )

    from src.prompt_helpers import interpolate_prompt

    assert interpolate_prompt(prompt, MockNote(note_data)) == expected
