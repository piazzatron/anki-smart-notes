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

from typing import Any

import pytest
from attr import dataclass


@dataclass
class MockNote:
    _data: dict[str, Any]

    def items(self):
        return self._data.items()


@dataclass
class MockConfig:
    allow_empty_fields: bool


@pytest.mark.parametrize(
    "prompt, expected",
    [
        ("[[f1]]", ["f1"]),
        ("{{f1}}", ["f1"]),
        ("[[f1]] [[f2]]", ["f1", "f2"]),
        ("{{f1}} {{f2}}", ["f1", "f2"]),
        ("[[f1]] {{f2}}", ["f1", "f2"]),
        ("no fields here", []),
        ("[[Front]] and {{Back}}", ["front", "back"]),
        ("[[F1]]", ["f1"]),
        ("{{F1}}", ["f1"]),
    ],
)
def test_get_prompt_fields(prompt, expected):
    from src.prompts import get_prompt_fields

    assert get_prompt_fields(prompt) == expected


@pytest.mark.parametrize(
    "prompt, expected",
    [
        ("[[f1]]", ["f1"]),
        ("{{f1}}", ["f1"]),
        ("[[Front]]", ["Front"]),
        ("{{Front}}", ["Front"]),
    ],
)
def test_get_prompt_fields_no_lower(prompt, expected):
    from src.prompts import get_prompt_fields

    assert get_prompt_fields(prompt, lower=False) == expected


@pytest.mark.parametrize(
    "prompt, note_data, expected",
    [
        ("[[f1]]", {"f1": "hello"}, "hello"),
        ("{{f1}}", {"f1": "hello"}, "hello"),
        ("[[f1]] and [[f2]]", {"f1": "hello", "f2": "world"}, "hello and world"),
        ("{{f1}} and {{f2}}", {"f1": "hello", "f2": "world"}, "hello and world"),
        ("[[f1]] and {{f2}}", {"f1": "hello", "f2": "world"}, "hello and world"),
        ("no fields", {"f1": "hello"}, "no fields"),
    ],
)
def test_interpolate_prompt(prompt, note_data, expected, monkeypatch):
    import src.prompts
    from src.prompts import interpolate_prompt

    note = MockNote(data=note_data)
    c = MockConfig(allow_empty_fields=False)
    monkeypatch.setattr(src.prompts, "config", c)
    result = interpolate_prompt(prompt, note)
    assert result == expected


def test_interpolate_prompt_empty_field_not_allowed(monkeypatch):
    import src.prompts
    from src.prompts import interpolate_prompt

    note = MockNote(data={"f1": "hello", "f2": ""})
    c = MockConfig(allow_empty_fields=False)
    monkeypatch.setattr(src.prompts, "config", c)
    assert interpolate_prompt("[[f1]] [[f2]]", note) is None


def test_interpolate_prompt_empty_field_allowed(monkeypatch):
    import src.prompts
    from src.prompts import interpolate_prompt

    note = MockNote(data={"f1": "hello", "f2": ""})
    c = MockConfig(allow_empty_fields=True)
    monkeypatch.setattr(src.prompts, "config", c)
    assert interpolate_prompt("[[f1]] [[f2]]", note) == "hello "


@pytest.mark.parametrize(
    "prompt, expected",
    [
        ("[[vocab]]", ["vocab"]),
        ("[[vocab]] with no cloze issues", ["vocab"]),
        ("[text](url)", []),
        ("![alt text](image.png)", []),
        ("[link](https://example.com) and [[field]]", ["field"]),
        ("![img](pic.jpg) then [[vocab]]", ["vocab"]),
        ("[single brackets]", []),
        ("text with [misc] brackets", []),
        ("[a]([b]) [[real_field]]", ["real_field"]),
    ],
)
def test_get_prompt_fields_ignores_non_field_brackets(prompt, expected):
    from src.prompts import get_prompt_fields

    assert get_prompt_fields(prompt) == expected


@pytest.mark.parametrize(
    "prompt, note_data, expected",
    [
        (
            "Define [[vocab]]",
            {"vocab": "{{c1::hello}}"},
            "Define {{c1::hello}}",
        ),
        (
            "Explain [[vocab]]",
            {"vocab": "{{c1::word}} means {{c2::meaning}}"},
            "Explain {{c1::word}} means {{c2::meaning}}",
        ),
        (
            "[[front]] - [[back]]",
            {"front": "{{c1::cat}}", "back": "animal"},
            "{{c1::cat}} - animal",
        ),
    ],
)
def test_interpolate_prompt_preserves_cloze_deletions(
    prompt, note_data, expected, monkeypatch
):
    import src.prompts
    from src.prompts import interpolate_prompt

    note = MockNote(data=note_data)
    c = MockConfig(allow_empty_fields=False)
    monkeypatch.setattr(src.prompts, "config", c)
    assert interpolate_prompt(prompt, note) == expected


@pytest.mark.parametrize(
    "prompt, note_data, expected",
    [
        (
            "Translate [[vocab]] ![icon](img.png)",
            {"vocab": "hello"},
            "Translate hello ![icon](img.png)",
        ),
        (
            "See [docs](https://example.com) for [[vocab]]",
            {"vocab": "hello"},
            "See [docs](https://example.com) for hello",
        ),
        (
            "[![img](pic.jpg)](link) and [[vocab]]",
            {"vocab": "hello"},
            "[![img](pic.jpg)](link) and hello",
        ),
    ],
)
def test_interpolate_prompt_preserves_markdown(
    prompt, note_data, expected, monkeypatch
):
    import src.prompts
    from src.prompts import interpolate_prompt

    note = MockNote(data=note_data)
    c = MockConfig(allow_empty_fields=False)
    monkeypatch.setattr(src.prompts, "config", c)
    assert interpolate_prompt(prompt, note) == expected
