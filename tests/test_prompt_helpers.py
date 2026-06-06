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
from unittest.mock import MagicMock

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
}

DEFAULT_CHAT_OPTIONS = {
    "chat_provider": None,
    "chat_model": None,
    "chat_reasoning_level": None,
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
        "chat_reasoning_level": None,
        "chat_web_search": None,
        "tts_model": None,
        "tts_provider": None,
        "tts_voice": None,
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
    import src.prompt_helpers

    c = MockConfig(prompts_map=prompts_map)
    monkeypatch.setattr(src.prompt_helpers, "config", c)
    monkeypatch.setattr(
        src.prompt_helpers,
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
    from src.prompt_helpers import get_prompt_fields

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
    from src.prompt_helpers import get_prompt_fields

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
    import src.prompt_helpers

    c = MockConfig(allow_empty_fields=allow_empty)
    monkeypatch.setattr(src.prompt_helpers, "config", c)

    from src.prompt_helpers import interpolate_prompt

    note = MockNote(data=note_data)
    result = interpolate_prompt(prompt, note)
    assert result == expected


def test_valid_prompt_fields_exclude_unsaved_tts_fields(monkeypatch):
    import src.utils.notes_utils

    audio_extras = make_extras()
    audio_extras["type"] = "tts"
    prompts_map = make_prompts_map(
        "Basic",
        1,
        {"Audio": "{{Front}}"},
        {"Audio": audio_extras},
    )
    monkeypatch.setattr(
        src.utils.notes_utils,
        "get_fields",
        lambda _: ["Front", "Audio", "Back"],
    )
    monkeypatch.setattr(
        src.utils.notes_utils,
        "get_note_type_id_from_name",
        lambda _: 123,
    )
    monkeypatch.setattr(
        src.utils.notes_utils.smart_field_service,
        "get_smart_fields_for_note",
        lambda *_, **__: [],
    )

    assert src.utils.notes_utils.get_valid_fields_for_prompt(
        selected_note_type="Basic",
        deck_id=1,
        selected_note_field="Back",
        prompts_map=prompts_map,
    ) == ["Front"]


def test_valid_prompt_fields_exclude_global_unsaved_tts_fields(monkeypatch):
    import src.utils.notes_utils

    audio_extras = make_extras()
    audio_extras["type"] = "tts"
    prompts_map = make_prompts_map(
        "Basic",
        -1,
        {"Audio": "{{Front}}"},
        {"Audio": audio_extras},
    )
    monkeypatch.setattr(
        src.utils.notes_utils,
        "get_fields",
        lambda _: ["Front", "Audio", "Back"],
    )
    monkeypatch.setattr(
        src.utils.notes_utils,
        "get_note_type_id_from_name",
        lambda _: 123,
    )
    monkeypatch.setattr(
        src.utils.notes_utils.smart_field_service,
        "get_smart_fields_for_note",
        lambda *_, **__: [],
    )

    assert src.utils.notes_utils.get_valid_fields_for_prompt(
        selected_note_type="Basic",
        deck_id=1,
        selected_note_field="Back",
        prompts_map=prompts_map,
    ) == ["Front"]

    assert src.utils.notes_utils.get_valid_fields_for_prompt(
        selected_note_type="Basic",
        deck_id=1,
        selected_note_field="Back",
        prompts_map=prompts_map,
        include_global_smart_fields=False,
    ) == ["Front", "Audio"]


def test_valid_prompt_fields_exclude_persisted_global_tts_fields(monkeypatch):
    import src.utils.notes_utils
    from src.models.smart_fields import SmartField, TTSSmartFieldSettings

    monkeypatch.setattr(
        src.utils.notes_utils,
        "get_fields",
        lambda _: ["Front", "Audio", "Back"],
    )
    monkeypatch.setattr(
        src.utils.notes_utils,
        "get_note_type_id_from_name",
        lambda _: 123,
    )
    monkeypatch.setattr(
        src.utils.notes_utils.smart_field_service,
        "get_smart_fields_for_note",
        lambda *_, **__: [
            SmartField(
                id="audio",
                note_type_id=123,
                deck_id=-1,
                target_field_name="audio",
                enabled=True,
                settings=TTSSmartFieldSettings(
                    source_field_name="Front",
                    provider="openai",
                    model="tts-1",
                    voice_id="alloy",
                ),
            )
        ],
    )

    assert src.utils.notes_utils.get_valid_fields_for_prompt(
        selected_note_type="Basic",
        deck_id=1,
        selected_note_field="Back",
    ) == ["Front"]


def test_custom_text_prompt_rejects_invalid_prompt(monkeypatch):
    import src.ui.custom_prompt

    messages: list[str] = []
    dialog = src.ui.custom_prompt.CustomTextPrompt.__new__(
        src.ui.custom_prompt.CustomTextPrompt
    )
    dialog._prompt_window = MagicMock()
    dialog._prompt_window.toPlainText.return_value = "Define {{Audio}}"
    dialog._note = MagicMock()
    dialog._deck_id = 1
    dialog._field_upper = "Back"
    dialog._loading = True
    dialog._update_ui_states = MagicMock()
    monkeypatch.setattr(
        src.ui.custom_prompt,
        "prompt_has_error",
        lambda *_, **__: "Cannot reference TTS or image fields in prompts",
    )
    monkeypatch.setattr(
        src.ui.custom_prompt,
        "show_message_box",
        lambda message: messages.append(message),
    )
    monkeypatch.setattr(
        src.ui.custom_prompt,
        "run_async_in_background_with_sentry",
        MagicMock(),
    )

    src.ui.custom_prompt.CustomTextPrompt.on_generate(dialog)

    assert messages == [
        "Invalid prompt: Cannot reference TTS or image fields in prompts"
    ]
    assert dialog._loading is False
    dialog._update_ui_states.assert_called_once()
    src.ui.custom_prompt.run_async_in_background_with_sentry.assert_not_called()


def test_prompt_dialog_initial_tts_source_uses_filtered_source_fields(monkeypatch):
    import src.ui.prompt_dialog

    prompts_map = make_prompts_map("Basic", -1, {}, {})
    dialog = src.ui.prompt_dialog.PromptDialog.__new__(
        src.ui.prompt_dialog.PromptDialog
    )
    dialog.prompts_map = prompts_map
    monkeypatch.setattr(
        src.ui.prompt_dialog,
        "get_fields",
        lambda _: ["Front", "Audio", "Back"],
    )

    def fake_get_valid_fields_for_prompt(
        note_type,
        deck_id,
        selected_note_field=None,
        prompts_map=None,
        include_global_smart_fields=True,
    ):
        if include_global_smart_fields:
            return ["Front", "Back"]
        return ["Front", "Audio", "Back"]

    monkeypatch.setattr(
        src.ui.prompt_dialog,
        "get_valid_fields_for_prompt",
        fake_get_valid_fields_for_prompt,
    )

    assert dialog._get_initial_source_field("Basic", 1) == "Back"


class TestMoveSmartField:
    def test_move_field_removes_old_and_adds_new(self, monkeypatch):
        from src.prompt_helpers import add_or_update_prompts, remove_prompt

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
        from src.prompt_helpers import add_or_update_prompts, remove_prompt

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
        from src.prompt_helpers import add_or_update_prompts, remove_prompt

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
        from src.prompt_helpers import add_or_update_prompts, remove_prompt

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
        from src.prompt_helpers import remove_prompt

        extras = make_extras()
        prompts_map = make_prompts_map(
            "Basic", 1, {"Back": "{{Front}}"}, {"Back": extras}
        )
        setup_prompts(monkeypatch, prompts_map)

        removed = remove_prompt(prompts_map, "Basic", 1, "Back")
        assert "Basic" not in removed["note_types"]

    def test_save_to_same_field_no_removal_needed(self, monkeypatch):
        from src.prompt_helpers import add_or_update_prompts

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
