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
    _note_type: str
    _data: dict[str, Any]

    id = 1

    def note_type(self):
        return {"name": self._note_type}

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value):
        self._data[key] = value

    def __contains__(self, key):
        return key in self._data

    def items(self):
        return self._data.items()

    def fields(self):
        return self._data.keys()


@dataclass
class MockConfig:
    prompts_map: Any
    allow_empty_fields: bool
    chat_provider = "openai"
    chat_model = "gpt-4o-mini"
    chat_temperature = 0
    tts_provider = "openai"
    tts_voice = "alloy"
    tts_model = "tts-1"
    openai_api_key = ""
    auth_token: str = ""
    uuid: str = "test-uuid-12345"
    debug: bool = True


def p(str) -> str:
    return f"p_{str}"


class MockOpenAIClient:
    async def async_get_chat_response(self, prompt: str):
        return p(prompt)


class MockChatClient:
    async def async_get_chat_response(
        self,
        prompt: str,
        model: str,
        provider: str,
        note_id: int,
        temperature: int = 0,
        retry_count: int = 0,
    ) -> str:
        return p(prompt)


class MockAppState:
    """Mock app state that simulates an unlocked app with unlimited capacity"""

    state = {
        "subscription": "PAID_PLAN_ACTIVE",  # Unlocked state
        "plan": {
            "planId": "test_plan",
            "planName": "Test Plan",
            "notesUsed": 0,
            "notesLimit": 1000,
            "daysLeft": 30,
            "textCreditsUsed": 0,
            "textCreditsCapacity": 1000,
            "voiceCreditsUsed": 0,
            "voiceCreditsCapacity": 1000,
            "imageCreditsUsed": 0,
            "imageCreditsCapacity": 1000,
        },
    }


NOTE_TYPE_NAME = "note_type_1"


def setup_data(monkeypatch, note, prompts_map, options, allow_empty_fields):
    import src.app_state
    import src.dag
    import src.prompts
    from src.field_processor import FieldProcessor
    from src.note_proccessor import NoteProcessor

    openai = MockOpenAIClient()
    chat = MockChatClient()

    # Create extras for all fields with prompts, with defaults for fields not in options
    extras = {}
    for field in prompts_map:
        if field in options:
            extras[field] = {
                "automatic": not options[field]["manual"],
                "type": "chat",
                "use_custom_model": False,
                # Add the config values that key_or_config_val looks for
                "chat_model": "gpt-4o-mini",
                "chat_provider": "openai",
                "chat_temperature": 0,
                "chat_markdown_to_html": False,
            }
        else:
            extras[field] = {
                "automatic": True,
                "type": "chat",
                "use_custom_model": False,
                # Add the config values that key_or_config_val looks for
                "chat_model": "gpt-4o-mini",
                "chat_provider": "openai",
                "chat_temperature": 0,
                "chat_markdown_to_html": False,
            }  # Default extras

    prompts_map = {
        "note_types": {NOTE_TYPE_NAME: {"1": {"fields": prompts_map, "extras": extras}}}
    }

    c = MockConfig(prompts_map=prompts_map, allow_empty_fields=allow_empty_fields)
    f = FieldProcessor(
        openai_provider=openai,
        chat_provider=chat,
        tts_provider=chat,
        image_provider=chat,
    )  # type: ignore
    p = NoteProcessor(field_processor=f, config=c)

    monkeypatch.setattr(
        src.dag,
        "get_fields",
        lambda _: note.fields(),  # type: ignore
    )

    # Replace config and app_state with mocks - cleaner than patching individual functions
    mock_app_state = MockAppState()
    monkeypatch.setattr(src.app_state, "config", c)
    monkeypatch.setattr(src.app_state, "app_state", mock_app_state)

    monkeypatch.setattr(src.prompts, "config", c)
    monkeypatch.setattr(
        src.prompts,
        "get_prompts_for_note",
        lambda note_type, deck_id, override_prompts_map=None: prompts_map["note_types"][
            note_type
        ]["1"]["fields"],
    )
    monkeypatch.setattr(
        src.prompts,
        "get_extras",
        lambda note_type,
        field,
        deck_id,
        prompts=None,
        fallback_to_global_deck=True: extras.get(field, {"automatic": True}),
    )

    return p


"""
test_processor_1 Parameters:
    name: str - Test case name for identification
    note: dict[str, str] - Note field data, e.g. {"f1": "value", "f2": ""}
    prompts_map: dict[str, str] - Field prompts, e.g. {"f2": "{{f1}}"}
    expected: dict[str, str] - Expected field values after processing
    options: dict[str, Any] - Test options:
        - "overwrite": bool - Whether to overwrite existing field values
        - "target_field": str - Specific field to process (if any)
        - "allow_empty": bool - Whether to allow processing with empty reference fields
        - "{field_name}": dict - Field-specific options:
            - "manual": bool - Whether field is marked as manual

Example: ("basic", {"f1": "1", "f2": ""}, {"f2": "{{f1}}"}, {"f2": "p_1"}, {})
"""


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "name, note, prompts_map, expected, options",
    [
        # ------ Basic -------
        # A super basic, single field example
        ("basic", {"f1": "1", "f2": ""}, {"f2": "{{f1}}"}, {"f2": p("1")}, {}),
        # Two fields, in parallel
        (
            "parallel",
            {"f1": "1", "f2": "2", "f3": "", "f4": ""},
            {"f3": "{{f1}}", "f4": "{{f2}}"},
            {"f3": p("1"), "f4": p("2")},
            {},
        ),
        # ---- Overwrite ----
        # no overwrite
        ("no overwrite", {"f1": "1", "f2": "old"}, {"f2": "{{f1}}"}, {"f2": "old"}, {}),
        # yes overwrite
        (
            "yes overwrite",
            {"f1": "1", "f2": "old"},
            {"f2": "{{f1}}"},
            {"f2": p("1")},
            {"overwrite": True},
        ),
        # Chained overwrite does overwrite
        (
            "chained overwrite does overwrite",
            {"f1": "1", "f2": "old", "f3": ""},
            {"f2": "{{f1}}", "f3": "{{f2}}"},
            {"f2": p("1"), "f3": p(p("1"))},
            {"overwrite": True},
        ),
        # Chained no overwrite does not overwrite
        (
            "chained overwrite does not overwrite",
            {"f1": "1", "f2": "old", "f3": ""},
            {"f2": "{{f1}}", "f3": "{{f2}}"},
            {"f2": "old", "f3": p("old")},
            {"overwrite": False},
        ),
        # ---- Allow Empty -----
        # Not allowed, references 2 fields, 0 empty
        (
            "allow empty 1",
            {"f1": "1", "f2": "2", "f3": ""},
            {"f3": "{{f1}} {{f2}}"},
            {"f3": p("1 2")},
            {},
        ),
        # Not allowed, references 2 fields, 1 empty
        (
            "allow empty 2",
            {"f1": "1", "f2": "", "f3": ""},
            {"f3": "{{f1}} {{f2}}"},
            {"f3": ""},
            {},
        ),
        # Allowed, references 2 fields, 1 empty
        (
            "allow empty 3",
            {"f1": "1", "f2": "", "f3": ""},
            {"f3": "{{f1}} {{f2}}"},
            {"f3": p("1 ")},
            {
                "allow_empty": True,
            },
        ),
        # Allowed, references 2 field, both empty
        (
            "allow empty 4",
            {"f1": "", "f2": "", "f3": ""},
            {"f3": "{{f1}} {{f2}}"},
            {"f3": ""},
            {
                "allow_empty": True,
            },
        ),
        # Allowed, references 1 field, empty
        (
            "allow empty 5",
            {"f1": "", "f2": ""},
            {"f2": "{{f1}}"},
            {"f2": ""},
            {
                "allow_empty": True,
            },
        ),
        # Chained, 1 empty, not allow empty
        # f1 -> f2 -> f3
        # f4 -> f5 ---^
        (
            "chained, not allowing empty",
            {"f1": "1", "f2": "", "f3": "", "f4": "", "f5": ""},
            {"f2": "{{f1}}", "f3": "{{f2}} {{f5}}", "f5": "{{f4}}"},
            {"f2": p("1"), "f3": "", "f4": "", "f5": ""},
            {
                "allow_empty": False,
            },
        ),
        # Chained, allow empty
        # f1 -> f2 -> f3
        # f4 -> f5 ---^
        (
            "chained, allowing empty",
            {"f1": "1", "f2": "", "f3": "", "f4": "", "f5": ""},
            {"f2": "{{f1}}", "f3": "{{f2}} {{f5}}", "f5": "{{f4}}"},
            {"f2": p("1"), "f3": p(p("1") + " "), "f4": "", "f5": ""},
            {
                "allow_empty": True,
            },
        ),
        # ----- Target Field ------
        # Target field specified, only that field is updated
        (
            "target only updates target",
            {"f1": "1", "f2": "2", "f3": "", "f4": ""},
            {"f3": "{{f1}}", "f4": "{{f2}}"},
            {"f3": p("1"), "f4": "", "f1": "1"},
            {
                "target_field": "f3",
            },
        ),
        # with target should NOT overwrite prior fields
        (
            "chained target overwrite doesn't overwrite prior fields",
            {"f1": "1", "f2": "old", "f3": ""},
            {"f2": "{{f1}}", "f3": "{{f2}}"},
            {"f2": "old", "f3": p("old")},
            {"target_field": "f3"},
        ),
        # Target field specified, always regenerates
        (
            "target always regenerates even if filled",
            {"f1": "1", "f2": "2", "f3": "OLD", "f4": ""},
            {"f3": "{{f1}}", "f4": "{{f2}}"},
            {"f3": p("1"), "f4": ""},
            {
                "target_field": "f3",
            },
        ),
        # ----- Manual fields ---------
        # Manual field not generated
        (
            "manual not generated",
            {"f1": "1", "f2": "2", "f3": "", "f4": ""},
            {"f3": "{{f1}}", "f4": "{{f2}}"},
            {"f3": "", "f4": p("2")},
            {
                "f3": {"manual": True},
            },
        ),
        # Manual field + target is generated
        (
            "manual + target is generated",
            {"f1": "1", "f2": "2", "f3": "", "f4": ""},
            {"f3": "{{f1}}", "f4": "{{f2}}"},
            {"f3": p("1"), "f4": ""},
            {
                "target_field": "f3",
                "f3": {"manual": True},
            },
        ),
        # ------- Chained Prompts ------
        # Simple case
        (
            "chained simple",
            {"f1": "1", "f2": "", "f3": ""},
            {"f2": "{{f1}}", "f3": "{{f2}}"},
            {"f2": p("1"), "f3": p(p("1"))},
            {},
        ),
        # Complex chain
        (
            "chained complex",
            {"f1": "1", "f2": "", "f3": "", "f4": "", "f5": ""},
            {
                "f2": "{{f1}}",
                "f3": "{{f2}}",
                "f4": "{{f2}}",
                "f5": "{{f3}} {{f2}} {{f4}}",
            },
            {
                "f2": p("1"),
                "f3": p(p("1")),
                "f4": p(p("1")),
                "f5": p(p(p("1")) + " " + p("1") + " " + p(p("1"))),
            },
            {},
        ),
        # Chain, shouldn't regenerate fields that already exist
        (
            "chain preserves already filled fields",
            {"f1": "1", "f2": "old", "f3": ""},
            {"f2": "{{f1}}", "f3": "{{f2}}"},
            {"f2": "old", "f3": p("old")},
            {},
        ),
        # ------ Target Fields ------
        # Generate the target field, it should only update that field + things before
        #             T
        # f1 -> f2 -> f3 -> f4
        #    -> f5 ---^
        #    -> f6
        (
            "chained target updates",
            {"f1": "1", "f2": "", "f3": "", "f4": "", "f5": "", "f6": ""},
            {
                "f2": "{{f1}}",
                "f3": "{{f2}} {{f5}}",
                "f4": "{{f3}}",
                "f5": "{{f1}}",
                "f6": "{{f1}}",
            },
            {
                "f2": p("1"),
                "f5": p("1"),
                "f3": p(p("1") + " " + p("1")),
                "f4": "",
                "f6": "",
            },
            {
                "target_field": "f3",
            },
        ),
        # ------ Chained manual ------
        # Behavior:
        # - A) If no target field is specified, the manual field is not generated
        #   and should stop the chain
        # - B) If a target field is specified, the manual field is generated if it's
        #   anywhere BEFORE the target field
        #
        # A) case where manual field stops the chain
        #       .     X     X
        # f1 -> f2 -> f3 -> f2
        #             M
        (
            "chained manual stops chain",
            {"f1": "1", "f2": "", "f3": "old", "f4": "old"},
            {"f2": "{{f1}}", "f3": "{{f2}}", "f4": "{{f3}}"},
            {"f2": p("1"), "f3": "old", "f4": "old"},
            {
                "f3": {"manual": True},
            },
        ),
        # B)case
        # Self is target, should generate self + any manual BEFORE self
        # f1 -> f2 -> f3 -> f4 -> f5 -> f6
        #       M     MT          M
        (
            "chained manual before target is generated",
            {"f1": "1", "f2": "", "f3": "old", "f4": "old", "f5": "old", "f6": "old"},
            {"f2": "{{f1}}", "f3": "{{f2}}", "f4": "{{f3}}"},
            {
                "f2": p("1"),
                "f3": p(p("1")),
                "f4": "old",
                "f5": "old",
                "f6": "old",
            },
            {
                "f2": {"manual": True},
                "f3": {"manual": True},
                "f5": {"manual": True},
                "target_field": "f3",
            },
        ),
        # LEFT OFF:
        # Overwrite! I think this is the last real one?
        # TODO: next chains + overwrite
        # TODO: error handling?
    ],
)
async def test_processor_1(name, note, prompts_map, expected, options, monkeypatch):
    overwrite_fields = bool(options.get("overwrite"))
    target_field = options.get("target_field")
    allow_empty_fields = bool(options.get("allow_empty"))

    n = MockNote(note_type=NOTE_TYPE_NAME, data=note)
    p = setup_data(  # type: ignore
        monkeypatch=monkeypatch,
        note=n,
        prompts_map=prompts_map,
        options=options,
        allow_empty_fields=allow_empty_fields,
    )

    await p._process_note(
        n, deck_id=1, overwrite_fields=overwrite_fields, target_field=target_field
    )

    for k, v in expected.items():
        assert n[k] == v, f"{name}: Field {k} is {n[k]}, expected {v}"


"""
test_cycle Parameters:
    note: dict[str, str] - Note field data
    prompts_map: dict[str, str] - Field prompts that may contain cycles
    expected: bool - Whether a cycle should be detected

Example: ({"f1": "1", "f2": ""}, {"f2": "{{f1}} {{f4}}", "f4": "{{f2}}"}, True)
"""


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "note, prompts_map, expected",
    [
        # No cycle
        (
            {"f1": "1", "f2": "2", "f3": "", "f4": ""},
            {"f3": "{{f1}}", "f4": "{{f2}}"},
            False,
        ),
        # Cycle
        # f1 -> f2 -> f3 -> f4
        # .     ^-----------|
        (
            {"f1": "1", "f2": "2", "f3": "", "f4": ""},
            {"f2": "{{f1}} {{f4}}", "f3": "{{f2}}", "f4": "{{f3}}"},
            True,
        ),
        # Diamond shaped DAG - no cycle
        # f1 -> f2 -> f4
        # f1 -> f3 -> f4
        (
            {"f1": "1", "f2": "", "f3": "", "f4": ""},
            {"f2": "{{f1}}", "f3": "{{f1}}", "f4": "{{f2}} {{f3}}"},
            False,
        ),
    ],
)
async def test_cycle(note, prompts_map, expected, monkeypatch):
    import src.dag
    import src.prompts

    n = MockNote(note_type=NOTE_TYPE_NAME, data=note)

    # Set up the same mocks that setup_data does for prompts
    extras = {
        field: {"automatic": True, "type": "chat", "use_custom_model": False}
        for field in prompts_map
    }
    prompts_data = {
        "note_types": {NOTE_TYPE_NAME: {"1": {"fields": prompts_map, "extras": extras}}}
    }
    c = MockConfig(prompts_map=prompts_data, allow_empty_fields=False)

    monkeypatch.setattr(src.prompts, "config", c)
    monkeypatch.setattr(
        src.prompts,
        "get_prompts_for_note",
        lambda note_type, deck_id, override_prompts_map=None: prompts_data[
            "note_types"
        ][note_type]["1"]["fields"],
    )

    # Mock get_fields like in setup_data
    monkeypatch.setattr(
        src.dag,
        "get_fields",
        lambda _: n.fields(),
    )

    dag = src.dag.generate_fields_dag(n, deck_id=1, overwrite_fields=True)
    cycle = src.dag.has_cycle(dag)
    assert cycle == expected


"""
test_returns_if_updated Parameters:
    note: dict[str, str] - Note field data
    prompts_map: dict[str, str] - Field prompts
    expected: bool - Whether the note should be marked as updated

Example: ({"f1": "1", "f2": ""}, {"f2": "{{f1}}"}, True)
"""


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "note, prompts_map, expected",
    [
        (
            {"f1": "1", "f2": ""},
            {"f2": "{{f1}}"},
            True,
        ),
        (
            {"f1": "1", "f2": "1"},
            {"f2": "{{f1}}"},
            False,
        ),
    ],
)
async def test_returns_if_updated(note, prompts_map, expected, monkeypatch):
    n = MockNote(note_type=NOTE_TYPE_NAME, data=note)
    p = setup_data(  # type: ignore
        monkeypatch=monkeypatch,
        note=n,
        prompts_map=prompts_map,
        options={},
        allow_empty_fields=False,
    )

    res = await p._process_note(n, deck_id=1, overwrite_fields=False, target_field=None)  # type: ignore
    assert res == expected
