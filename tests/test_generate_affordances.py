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

import json
import shutil
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Optional

import pytest
from fixtures import NOTE_TYPE_ID, FakeAnkiDb, use_temp_sqlite

import src.ui.generate_affordances
import src.utils.notes_utils
from src.models.smart_fields import (
    ChatSmartFieldSettings,
    SmartField,
    SmartFieldCreate,
    TTSSmartFieldSettings,
)
from src.services.smart_field_service import smart_field_service
from src.ui.generate_affordances import (
    SelectionActions,
    fillable_smart_fields,
    selection_actions,
)
from src.utils.notes_utils import note_decks

GLOBAL = -1
OTHER_DECK = 2


@pytest.fixture(autouse=True)
def sqlite_database(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, migrated_database: Path
) -> None:
    use_temp_sqlite(monkeypatch, tmp_path)
    monkeypatch.setattr(smart_field_service, "_get_profile_name", lambda: "__test__")
    shutil.copy(migrated_database, tmp_path / "smart_notes.sqlite3")


def install_collection(
    monkeypatch: pytest.MonkeyPatch,
    *,
    cards: list[tuple[int, int, int]],
    notes: Optional[list[tuple[int, int, str]]] = None,
) -> None:
    """A collection of Front/Back/Audio notes with these cards and notes."""

    def get_note_type(_: int) -> dict[str, Any]:
        return {"flds": [{"name": name} for name in ("Front", "Back", "Audio")]}

    fake_mw = SimpleNamespace(
        col=SimpleNamespace(
            db=FakeAnkiDb(cards=cards, notes=notes),
            models=SimpleNamespace(get=get_note_type),
        )
    )
    monkeypatch.setattr(src.utils.notes_utils, "mw", fake_mw)
    monkeypatch.setattr(src.ui.generate_affordances, "mw", fake_mw)


def add_smart_field(
    target: str,
    *,
    prompt: str = "Define {{Front}}",
    deck_id: int = GLOBAL,
    enabled: bool = True,
) -> None:
    smart_field_service.create_smart_field(
        SmartFieldCreate(
            note_type_id=NOTE_TYPE_ID,
            deck_id=deck_id,  # type: ignore
            target_field_name=target,
            enabled=enabled,
            settings=ChatSmartFieldSettings(
                prompt_text=prompt,
                provider="auto",
                model="auto",
                web_search_enabled=False,
            ),
        )
    )


def add_voice_field(target: str, source: str) -> None:
    smart_field_service.create_smart_field(
        SmartFieldCreate(
            note_type_id=NOTE_TYPE_ID,
            deck_id=GLOBAL,  # type: ignore
            target_field_name=target,
            enabled=True,
            settings=TTSSmartFieldSettings(
                source_field_name=source,
                provider="openai",
                model="tts-1",
                voice_id="alloy",
            ),
        )
    )


def smart_fields() -> list[SmartField]:
    return smart_field_service.get_smart_fields_for_note(NOTE_TYPE_ID, 1)  # type: ignore


def test_notes_resolve_by_their_last_selected_card(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Note 10 has cards 1 and 3 in different decks; the table returns rows out
    # of selection order.
    install_collection(monkeypatch, cards=[(1, 10, 1), (2, 20, 1), (3, 10, 2)])

    assert note_decks([3, 2, 1]) == {10: 1, 20: 1}
    assert list(note_decks([1, 2, 3]).items()) == [(10, 2), (20, 1)]


@pytest.mark.parametrize(
    ("front", "back_enabled", "include_manual", "expected"),
    [
        # Back reads Front, and the voice reads Back once it's generated.
        ("word", True, False, {"back", "audio"}),
        # Markup alone is empty, so nothing has an input.
        ("<br>", True, False, set()),
        # A disabled Back doesn't generate in a batch, so the voice has nothing
        # to read; targeting the voice fills Back first.
        ("word", False, False, set()),
        ("word", False, True, {"back", "audio"}),
    ],
)
def test_fillable_fields_need_an_input_with_text_or_one_generated_first(
    front: str, back_enabled: bool, include_manual: bool, expected: set[str]
) -> None:
    add_smart_field("Back", enabled=back_enabled)
    add_voice_field("Audio", "back")
    add_smart_field("Extra", prompt="A random word")

    fillable = fillable_smart_fields(
        {"front": front, "back": "", "audio": "", "extra": "filled"},
        smart_fields(),
        include_manual=include_manual,
    )

    assert fillable == expected


@pytest.mark.parametrize(
    ("front", "back", "audio", "audio_enabled", "expected"),
    [
        ("word", "", "", True, SelectionActions(1, True, True, True, False)),
        # Empty Smart Fields whose inputs are all empty can't generate.
        ("", "", "", True, SelectionActions(1, True, True, False, False)),
        ("word", "x", "x", True, SelectionActions(1, True, False, False, True)),
        ("word", "x", "", True, SelectionActions(1, True, True, True, True)),
        # Batch generation skips a disabled Smart Field, empty or filled.
        ("word", "x", "", False, SelectionActions(1, True, False, False, True)),
        ("word", "", "x", False, SelectionActions(1, True, True, True, False)),
    ],
)
def test_selection_offers_what_batch_generation_would_do(
    monkeypatch: pytest.MonkeyPatch,
    front: str,
    back: str,
    audio: str,
    audio_enabled: bool,
    expected: SelectionActions,
) -> None:
    add_smart_field("back")
    add_smart_field("Audio", enabled=audio_enabled)
    install_collection(
        monkeypatch,
        cards=[(1, 10, 1)],
        notes=[(10, NOTE_TYPE_ID, "\x1f".join([front, back, audio]))],
    )

    assert selection_actions([1]) == expected


def test_only_disabled_smart_fields_hide_the_banner(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    add_smart_field("Back", enabled=False)
    install_collection(
        monkeypatch,
        cards=[(1, 10, 1)],
        notes=[(10, NOTE_TYPE_ID, "word\x1f\x1f")],
    )

    assert not selection_actions([1]).has_smart_fields


@pytest.mark.parametrize(
    ("card_ids", "expected"),
    [
        # The last selected card sits in the deck with the Smart Field.
        ([1, 2], SelectionActions(1, True, True, True, False)),
        # The last selected card sits in a deck without one.
        ([2, 1], SelectionActions(1, False, False, False, False)),
    ],
)
def test_multi_card_note_counts_once_and_uses_the_generation_deck(
    monkeypatch: pytest.MonkeyPatch,
    card_ids: list[int],
    expected: SelectionActions,
) -> None:
    add_smart_field("Back", deck_id=OTHER_DECK)
    install_collection(
        monkeypatch,
        cards=[(1, 10, 1), (2, 10, OTHER_DECK)],
        notes=[(10, NOTE_TYPE_ID, "word\x1f\x1f")],
    )

    assert selection_actions(card_ids) == expected


@pytest.mark.parametrize(
    ("page_fields", "expected"),
    [
        # The user typed into Extra while Back was generating: both are kept.
        (["word", "", "typed"], ["word", "generated", "typed"]),
        # The user wrote their own Back meanwhile: theirs wins.
        (["word", "mine", ""], ["word", "mine", ""]),
        # The note was added and the page moved on to a blank one: nothing written.
        (["", "", ""], None),
    ],
)
def test_generation_into_the_experimental_add_dialog_respects_the_page(
    monkeypatch: pytest.MonkeyPatch,
    page_fields: list[str],
    expected: Optional[list[str]],
) -> None:
    from fixtures import MockNote

    from src.ui.generate_affordances import show_generated_note

    fake_mw = SimpleNamespace(
        col=SimpleNamespace(media=SimpleNamespace(escape_media_filenames=lambda v: v))
    )
    monkeypatch.setattr(src.ui.generate_affordances, "mw", fake_mw)
    written: list[str] = []

    class FakeWeb:
        def evalWithCallback(self, _: str, callback: Any) -> None:  # noqa: N802
            callback({"mid": str(NOTE_TYPE_ID), "fields": page_fields})

        def eval(self, js: str) -> None:
            written.append(js)

    page_editor = SimpleNamespace(addMode=True, web=FakeWeb())
    note = MockNote({"Front": "word", "Back": "generated", "Extra": ""})

    show_generated_note(page_editor, note, ["word", "", ""])  # type: ignore

    if expected is None:
        assert written == []
        return
    [js] = written
    names, values = json.loads(f"[{js.removeprefix('setFields(').removesuffix(');')}]")
    assert names == ["Front", "Back", "Extra"]
    assert values == expected
