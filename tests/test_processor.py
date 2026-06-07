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

import asyncio
from typing import Any

import pytest
from attr import dataclass

from src.database.migrations import apply_database_migrations


@dataclass
class MockNote:
    _note_type: str
    _data: dict[str, Any]

    id = 1

    def note_type(self):
        return {"name": self._note_type, "id": NOTE_TYPE_ID}

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
    allow_empty_fields: bool
    prompts_map: Any = None
    chat_provider = "auto"
    chat_model = "auto"
    chat_reasoning_level = "off"
    chat_web_search = False
    tts_provider = "openai"
    tts_voice = "alloy"
    tts_model = "tts-1"
    openai_api_key = ""
    auth_token: str = ""
    debug: bool = True


def p(str) -> str:
    # Avoid underscores so markdown-to-html conversion (always-on) is a no-op
    # on the simulated chat output.
    return f"p-{str}"


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
        generation_source: object,
        retry_count: int = 0,
        web_search: bool = False,
        reasoning_level: str = "off",
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
NOTE_TYPE_ID = 123


@pytest.fixture(autouse=True)
def sqlite_database(tmp_path, monkeypatch):
    import src.database.connection

    monkeypatch.setattr(
        src.database.connection,
        "get_database_path",
        lambda: str(tmp_path / "smart_notes.sqlite3"),
    )
    apply_database_migrations()


def seed_smart_fields(prompts_map, options):
    from src.models.smart_fields import ChatSmartFieldSettings, SmartFieldCreate
    from src.services.smart_field_service import smart_field_service

    for field, prompt in prompts_map.items():
        smart_field_service.save_smart_field(
            SmartFieldCreate(
                note_type_id=NOTE_TYPE_ID,
                deck_id=1,
                target_field_name=field,
                enabled=not options.get(field, {}).get("manual", False),
                settings=ChatSmartFieldSettings(
                    prompt_text=prompt,
                    provider="auto",
                    model="auto",
                    web_search_enabled=False,
                ),
            )
        )

    return smart_field_service.get_smart_fields_for_note(
        NOTE_TYPE_ID, 1, include_global=True
    )


def setup_data(monkeypatch, note, prompts_map, options, allow_empty_fields):
    import src.app_state
    import src.dag
    import src.field_resolver
    import src.prompt_helpers
    from src.field_resolver import FieldResolver
    from src.note_proccessor import NoteProcessor

    openai = MockOpenAIClient()
    chat = MockChatClient()

    seed_smart_fields(prompts_map, options)

    c = MockConfig(allow_empty_fields=allow_empty_fields)
    f = FieldResolver(
        openai_provider=openai,
        chat_provider=chat,
        tts_provider=chat,
        image_provider=chat,
    )  # type: ignore
    p = NoteProcessor(field_resolver=f, config=c)

    monkeypatch.setattr(
        src.dag,
        "get_fields",
        lambda _: note.fields(),  # type: ignore
    )

    # Replace config and app_state with mocks - cleaner than patching individual functions
    mock_app_state = MockAppState()
    monkeypatch.setattr(src.app_state, "config", c)
    monkeypatch.setattr(src.app_state, "app_state", mock_app_state)
    monkeypatch.setattr(src.prompt_helpers, "config", c)
    monkeypatch.setattr(src.field_resolver, "config", c, raising=False)

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
        # C) Manual field with existing value should NOT abort downstream
        #       .     .     .
        # f1 -> f2 -> f3
        #       M
        (
            "chained manual with value doesn't stop chain",
            {"f1": "1", "f2": "existing", "f3": ""},
            {"f2": "{{f1}}", "f3": "{{f2}}"},
            {"f2": "existing", "f3": p("existing")},
            {
                "f2": {"manual": True},
            },
        ),
        # D) Manual field WITHOUT value should still abort downstream
        #       .     X     X
        # f1 -> f2 -> f3
        #       M
        (
            "chained manual without value stops chain",
            {"f1": "1", "f2": "", "f3": ""},
            {"f2": "{{f1}}", "f3": "{{f2}}"},
            {"f2": "", "f3": ""},
            {
                "f2": {"manual": True},
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

    await p.process_note(
        n, deck_id=1, overwrite_fields=overwrite_fields, target_field=target_field
    )

    for k, v in expected.items():
        assert n[k] == v, f"{name}: Field {k} is {n[k]}, expected {v}"


def test_process_card_forwards_use_collection(monkeypatch):
    from src.note_proccessor import NoteProcessor

    class MockCard:
        id = 1
        did = 1

        def note(self):
            return MockNote(note_type=NOTE_TYPE_NAME, data={"f1": "1"})

    calls = []
    processor = NoteProcessor(  # type: ignore
        field_resolver=None,
        config=MockConfig(prompts_map={}, allow_empty_fields=False),
    )
    monkeypatch.setattr(processor, "_assert_preconditions", lambda: True)
    monkeypatch.setattr("src.note_proccessor.bump_usage_counter", lambda: None)
    monkeypatch.setattr(
        "src.note_proccessor.run_async_in_background_with_sentry",
        lambda op,
        on_success,
        on_failure=None,
        with_progress=False,
        use_collection=True: calls.append(use_collection),
    )

    processor.process_card(MockCard(), show_progress=False, use_collection=False)  # type: ignore

    assert calls == [False]


def test_process_cards_with_progress_noops_during_batch(monkeypatch):
    import src.note_proccessor
    from src.note_proccessor import NoteProcessor

    class MockCollection:
        pass

    class MockMw:
        col = MockCollection()

    calls = []
    processor = NoteProcessor(  # type: ignore
        field_resolver=None,
        config=MockConfig(prompts_map={}, allow_empty_fields=False),
    )
    processor.batch_in_progress = True
    monkeypatch.setattr(src.note_proccessor, "mw", MockMw())
    monkeypatch.setattr(
        "src.note_proccessor.run_async_in_background_with_sentry",
        lambda *args, **kwargs: calls.append(args),
    )

    processor.process_cards_with_progress([1], on_success=None)

    assert calls == []
    assert processor.batch_in_progress


@pytest.mark.asyncio
async def test_process_cards_with_progress_uses_worker_pool(monkeypatch):
    import src.note_proccessor
    from src.note_proccessor import NoteProcessor

    class MockBatchNote:
        def __init__(self, note_id):
            self.id = note_id

        def note_type(self):
            return {"name": NOTE_TYPE_NAME, "id": NOTE_TYPE_ID}

    class MockCard:
        def __init__(self, card_id):
            self.nid = card_id
            self.did = 1

    class MockCollection:
        def get_card(self, card_id):
            return MockCard(card_id)

        def get_note(self, note_id):
            return MockBatchNote(note_id)

        def update_notes(self, notes):
            pass

    class MockProgress:
        def start(self, **kwargs):
            pass

        def update(self, **kwargs):
            pass

        def finish(self):
            pass

        def want_cancel(self):
            return False

    class MockMw:
        def __init__(self):
            self.col = MockCollection()
            self.progress = MockProgress()

    captured = {}
    started = []
    slow_note_release = asyncio.Event()
    third_note_started = asyncio.Event()
    processor = NoteProcessor(  # type: ignore
        field_resolver=None,
        config=MockConfig(prompts_map={}, allow_empty_fields=False),
    )

    async def fake_process_note(note, overwrite_fields, deck_id, **kwargs):
        started.append(note.id)
        if note.id == 1:
            await slow_note_release.wait()
        if note.id == 3:
            third_note_started.set()
        return True

    monkeypatch.setattr(src.note_proccessor, "mw", MockMw())
    monkeypatch.setattr(src.note_proccessor, "STANDARD_BATCH_LIMIT", 2)
    monkeypatch.setattr(src.note_proccessor, "bump_usage_counter", lambda: None)
    monkeypatch.setattr(src.note_proccessor, "is_capacity_remaining", lambda: True)
    monkeypatch.setattr(
        src.note_proccessor,
        "is_capacity_remaining_or_legacy",
        lambda show_box=False: True,
    )
    monkeypatch.setattr(src.note_proccessor, "run_on_main", lambda work: work())
    monkeypatch.setattr(
        src.note_proccessor, "get_note_type_id", lambda note: NOTE_TYPE_ID
    )
    monkeypatch.setattr(
        src.note_proccessor.smart_field_service,
        "get_smart_fields_for_note",
        lambda *args, **kwargs: [object()],
    )
    monkeypatch.setattr(
        "src.note_proccessor.run_async_in_background_with_sentry",
        lambda op, on_success, on_failure=None: captured.update({"op": op}),
    )
    monkeypatch.setattr(processor, "_assert_valid_app_mode", lambda: True)
    monkeypatch.setattr(processor, "process_note", fake_process_note)

    processor.process_cards_with_progress([1, 2, 3], on_success=None)

    op_task = asyncio.create_task(captured["op"]())
    try:
        await asyncio.wait_for(third_note_started.wait(), timeout=0.2)
        assert started == [1, 2, 3]
    finally:
        slow_note_release.set()
        await op_task


@pytest.mark.asyncio
async def test_process_notes_batch_returns_skipped_notes_without_smart_fields(
    monkeypatch,
):
    import src.note_proccessor
    from src.note_proccessor import NoteProcessor

    note = MockNote(note_type=NOTE_TYPE_NAME, data={"f1": "1"})

    class MockCollection:
        def get_note(self, note_id):
            return note

    class MockMw:
        col = MockCollection()

    monkeypatch.setattr(src.note_proccessor, "mw", MockMw())
    monkeypatch.setattr(
        src.note_proccessor.smart_field_service,
        "get_smart_fields_for_note",
        lambda *args, **kwargs: [],
    )

    updated, failed, skipped, hit_out_of_credits = await NoteProcessor(  # type: ignore
        field_resolver=None,
        config=MockConfig(prompts_map={}, allow_empty_fields=False),
    )._process_notes_batch(
        [note.id],
        overwrite_fields=False,
        did_map={note.id: 1},
    )

    assert updated == []
    assert failed == []
    assert skipped == [note]
    assert hit_out_of_credits is False


@pytest.mark.asyncio
async def test_process_notes_worker_pool_returns_results_in_input_order(monkeypatch):
    from src.note_proccessor import NoteProcessor

    release_first = asyncio.Event()
    processor = NoteProcessor(  # type: ignore
        field_resolver=None,
        config=MockConfig(prompts_map={}, allow_empty_fields=False),
    )
    notes = {
        1: MockNote(note_type=NOTE_TYPE_NAME, data={"f1": "1"}),
        2: MockNote(note_type=NOTE_TYPE_NAME, data={"f1": "2"}),
        3: MockNote(note_type=NOTE_TYPE_NAME, data={"f1": "3"}),
    }

    notes[1].id = 1
    notes[2].id = 2
    notes[3].id = 3

    async def process_note_batch(note_ids, overwrite_fields, did_map, should_cancel):
        note_id = note_ids[0]
        if note_id == 1:
            await release_first.wait()
        elif note_id == 2:
            release_first.set()
        return ([notes[note_id]], [], [], False)

    monkeypatch.setattr(processor, "_process_notes_batch", process_note_batch)

    (
        updated,
        failed,
        skipped,
        hit_out_of_credits,
        processed_count,
    ) = await processor._process_notes_worker_pool(
        [1, 2, 3],
        overwrite_fields=False,
        did_map={1: 1, 2: 1, 3: 1},
        worker_count=2,
    )

    assert [note.id for note in updated] == [1, 2, 3]
    assert failed == []
    assert skipped == []
    assert hit_out_of_credits is False
    assert processed_count == 3


@pytest.mark.asyncio
async def test_process_notes_worker_pool_drains_workers_after_fatal_error(monkeypatch):
    from src.note_proccessor import NoteProcessor

    processor = NoteProcessor(  # type: ignore
        field_resolver=None,
        config=MockConfig(prompts_map={}, allow_empty_fields=False),
    )
    started: list[int] = []
    second_note_started = asyncio.Event()
    release_second_note = asyncio.Event()

    async def process_note_batch(note_ids, overwrite_fields, did_map, should_cancel):
        note_id = note_ids[0]
        started.append(note_id)

        if note_id == 1:
            await second_note_started.wait()
            raise RuntimeError("unexpected worker failure")

        if note_id == 2:
            second_note_started.set()
            await release_second_note.wait()

        return ([], [], [], False)

    monkeypatch.setattr(processor, "_process_notes_batch", process_note_batch)

    pool_task = asyncio.create_task(
        processor._process_notes_worker_pool(
            [1, 2, 3],
            overwrite_fields=False,
            did_map={1: 1, 2: 1, 3: 1},
            worker_count=2,
        )
    )

    await asyncio.wait_for(second_note_started.wait(), timeout=0.2)
    await asyncio.sleep(0)
    assert pool_task.done() is False

    release_second_note.set()
    with pytest.raises(RuntimeError, match="unexpected worker failure"):
        await pool_task

    assert started == [1, 2]


@pytest.mark.asyncio
async def test_process_notes_worker_pool_drains_after_admission_error(monkeypatch):
    from src.note_proccessor import NoteProcessor

    processor = NoteProcessor(  # type: ignore
        field_resolver=None,
        config=MockConfig(prompts_map={}, allow_empty_fields=False),
    )
    started: list[int] = []
    second_note_started = asyncio.Event()
    should_cancel_should_raise = asyncio.Event()
    release_second_note = asyncio.Event()

    async def process_note_batch(note_ids, overwrite_fields, did_map, should_cancel):
        note_id = note_ids[0]
        started.append(note_id)

        if note_id == 1:
            await second_note_started.wait()
            should_cancel_should_raise.set()

        if note_id == 2:
            second_note_started.set()
            await release_second_note.wait()

        return ([], [], [], False)

    def should_cancel():
        if should_cancel_should_raise.is_set():
            raise RuntimeError("admission check failed")
        return False

    monkeypatch.setattr(processor, "_process_notes_batch", process_note_batch)

    pool_task = asyncio.create_task(
        processor._process_notes_worker_pool(
            [1, 2, 3],
            overwrite_fields=False,
            did_map={1: 1, 2: 1, 3: 1},
            worker_count=2,
            should_cancel=should_cancel,
        )
    )

    await asyncio.wait_for(second_note_started.wait(), timeout=0.2)
    await asyncio.sleep(0)
    assert pool_task.done() is False

    release_second_note.set()
    with pytest.raises(RuntimeError, match="admission check failed"):
        await pool_task

    assert started == [1, 2]


@pytest.mark.asyncio
async def test_process_cards_with_progress_stops_queue_after_out_of_credits(
    monkeypatch,
):
    import src.note_proccessor
    from src.api_client import OutOfCreditsError
    from src.note_proccessor import NoteProcessor

    class MockBatchNote:
        def __init__(self, note_id):
            self.id = note_id

        def note_type(self):
            return {"name": NOTE_TYPE_NAME, "id": NOTE_TYPE_ID}

    class MockCard:
        def __init__(self, card_id):
            self.nid = card_id
            self.did = 1

    class MockCollection:
        def get_card(self, card_id):
            return MockCard(card_id)

        def get_note(self, note_id):
            return MockBatchNote(note_id)

        def update_notes(self, notes):
            pass

    class MockProgress:
        def start(self, **kwargs):
            pass

        def update(self, **kwargs):
            pass

        def finish(self):
            pass

        def want_cancel(self):
            return False

    class MockMw:
        def __init__(self):
            self.col = MockCollection()
            self.progress = MockProgress()

    captured = {}
    started = []
    first_note_started = asyncio.Event()
    out_of_credits_seen = asyncio.Event()
    processor = NoteProcessor(  # type: ignore
        field_resolver=None,
        config=MockConfig(prompts_map={}, allow_empty_fields=False),
    )

    async def fake_process_note(note, overwrite_fields, deck_id, **kwargs):
        started.append(note.id)
        if note.id == 1:
            first_note_started.set()
            await out_of_credits_seen.wait()
            return True
        if note.id == 2:
            await first_note_started.wait()
            out_of_credits_seen.set()
            raise OutOfCreditsError()
        return True

    monkeypatch.setattr(src.note_proccessor, "mw", MockMw())
    monkeypatch.setattr(src.note_proccessor, "STANDARD_BATCH_LIMIT", 2)
    monkeypatch.setattr(src.note_proccessor, "bump_usage_counter", lambda: None)
    monkeypatch.setattr(src.note_proccessor, "is_capacity_remaining", lambda: True)
    monkeypatch.setattr(
        src.note_proccessor,
        "is_capacity_remaining_or_legacy",
        lambda show_box=False: True,
    )
    monkeypatch.setattr(src.note_proccessor, "run_on_main", lambda work: work())
    monkeypatch.setattr(
        src.note_proccessor, "get_note_type_id", lambda note: NOTE_TYPE_ID
    )
    monkeypatch.setattr(
        src.note_proccessor.smart_field_service,
        "get_smart_fields_for_note",
        lambda *args, **kwargs: [object()],
    )
    monkeypatch.setattr(
        "src.note_proccessor.run_async_in_background_with_sentry",
        lambda op, on_success, on_failure=None: captured.update({"op": op}),
    )
    monkeypatch.setattr(processor, "_assert_valid_app_mode", lambda: True)
    monkeypatch.setattr(processor, "process_note", fake_process_note)

    processor.process_cards_with_progress([1, 2, 3], on_success=None)

    with pytest.raises(OutOfCreditsError):
        await captured["op"]()

    assert started == [1, 2]


@pytest.mark.asyncio
async def test_process_note_updates_collection_on_main_thread(monkeypatch):
    import src.note_proccessor

    class MockCollection:
        def __init__(self):
            self.updated_notes = []

        def update_note(self, note):
            self.updated_notes.append(note)

    class MockProgress:
        def want_cancel(self):
            return False

    class MockMw:
        def __init__(self):
            self.col = MockCollection()
            self.progress = MockProgress()

    n = MockNote(note_type=NOTE_TYPE_NAME, data={"f1": "1", "f2": ""})
    p = setup_data(  # type: ignore
        monkeypatch=monkeypatch,
        note=n,
        prompts_map={"f2": "{{f1}}"},
        options={},
        allow_empty_fields=False,
    )
    mw = MockMw()
    monkeypatch.setattr(src.note_proccessor, "mw", mw)
    monkeypatch.setattr(src.note_proccessor, "run_on_main", lambda work: work())

    await p.process_note(n, deck_id=1)

    assert mw.col.updated_notes == [n]


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

    n = MockNote(note_type=NOTE_TYPE_NAME, data=note)
    smart_fields = seed_smart_fields(prompts_map, {})

    # Mock get_fields like in setup_data
    monkeypatch.setattr(
        src.dag,
        "get_fields",
        lambda _: n.fields(),
    )

    dag = src.dag.generate_fields_dag(
        n, smart_fields=smart_fields, overwrite_fields=True
    )
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

    res = await p.process_note(n, deck_id=1, overwrite_fields=False, target_field=None)
    assert res == expected
