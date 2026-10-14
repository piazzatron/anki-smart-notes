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
from types import SimpleNamespace

from fixtures import MockCard, MockConfig, MockNote, MockProcessor

from src.api_client import OutOfCreditsError


class AddedNote(MockNote):
    """A note as seen by note_will_be_added: the id is assigned after the add."""

    def __init__(self, note_id: int, *, did: int = 1, processed: bool = False):
        super().__init__({"f1": "1"}, note_id=0)
        self.added_id = note_id
        self.card = MockCard(id=note_id, did=did, processed=processed, note=self)
        self.card.nid = note_id

    def finish_add(self) -> None:
        self.id = self.added_id

    def cards(self) -> list[MockCard]:
        return [self.card]


class MockCollection:
    def __init__(self) -> None:
        self.notes: dict[int, AddedNote] = {}

    def get_note(self, note_id: int) -> AddedNote:
        return self.notes[note_id]


class MockTimerProgress:
    def __init__(self) -> None:
        self.single_shots: list = []

    def single_shot(self, ms: int, func) -> None:
        self.single_shots.append(func)


def setup_add_time_evaluator(monkeypatch, *, generate_on_add=True):
    import src.add_time_evaluator

    processor = MockProcessor()
    evaluator = src.add_time_evaluator.AddTimeEvaluator(processor)
    mw = SimpleNamespace(col=MockCollection(), progress=MockTimerProgress())
    cfg = MockConfig()
    cfg.generate_on_add = generate_on_add
    jobs: list = []
    monkeypatch.setattr(src.add_time_evaluator, "mw", mw)
    monkeypatch.setattr(src.add_time_evaluator, "config", cfg)
    monkeypatch.setattr(src.add_time_evaluator, "run_on_main", lambda work: work())
    monkeypatch.setattr(
        src.add_time_evaluator, "is_capacity_remaining_or_legacy", lambda: True
    )
    monkeypatch.setattr(
        src.add_time_evaluator, "is_card_fully_processed", lambda card: card.processed
    )
    monkeypatch.setattr(
        src.add_time_evaluator,
        "run_async_in_background_with_sentry",
        lambda op, on_success, on_failure, use_collection: jobs.append(
            (op, on_success, on_failure)
        ),
    )
    return SimpleNamespace(
        evaluator=evaluator,
        processor=processor,
        mw=mw,
        jobs=jobs,
        module=src.add_time_evaluator,
    )


def add_notes(env, notes: list[AddedNote]) -> None:
    """Simulate col.add_notes: the hook fires for every note, then ids land."""
    for note in notes:
        env.evaluator.on_note_will_be_added(note)
    for note in notes:
        note.finish_add()
        env.mw.col.notes[note.id] = note


def fire_starts(env) -> None:
    shots = env.mw.progress.single_shots[:]
    env.mw.progress.single_shots.clear()
    for shot in shots:
        shot()


def run_jobs(env) -> None:
    jobs = env.jobs[:]
    env.jobs.clear()
    for op, on_success, on_failure in jobs:
        try:
            result = asyncio.run(op())
        except Exception as e:
            on_failure(e)
        else:
            on_success(result)


def test_bulk_add_beyond_limit_is_skipped(monkeypatch):
    env = setup_add_time_evaluator(monkeypatch)
    add_notes(env, [AddedNote(i, did=i) for i in range(1, 26)])
    fire_starts(env)

    assert len(env.jobs) == 10
    assert env.evaluator.in_flight == 10

    run_jobs(env)

    assert env.processor.processed_cards == list(range(1, 11))
    assert env.evaluator.in_flight == 0

    # Slots free up once generation finishes.
    add_notes(env, [AddedNote(100, did=100)])
    fire_starts(env)
    run_jobs(env)

    assert env.processor.processed_cards[-1] == 100


def test_skips_failed_deleted_and_already_filled_notes(monkeypatch):
    env = setup_add_time_evaluator(monkeypatch)
    failed_add = AddedNote(1, did=1)
    deleted = AddedNote(2, did=2)
    filled = AddedNote(3, did=3, processed=True)
    kept = AddedNote(4, did=4)
    for note in [failed_add, deleted, filled, kept]:
        env.evaluator.on_note_will_be_added(note)
    for note in [deleted, filled, kept]:
        note.finish_add()
    env.mw.col.notes = {3: filled, 4: kept}

    fire_starts(env)
    run_jobs(env)

    assert env.processor.processed_cards == [4]
    assert env.evaluator.in_flight == 0


def test_slow_add_still_generates_and_failed_add_gives_up(monkeypatch):
    env = setup_add_time_evaluator(monkeypatch)
    slow = AddedNote(1, did=1)
    failed = AddedNote(2, did=2)
    env.evaluator.on_note_will_be_added(slow)
    env.evaluator.on_note_will_be_added(failed)

    # Neither add has assigned an id when the first check runs.
    fire_starts(env)
    slow.finish_add()
    env.mw.col.notes[slow.id] = slow
    for _ in range(env.module.MAX_START_ATTEMPTS):
        fire_starts(env)
    run_jobs(env)

    assert env.processor.processed_cards == [1]
    assert env.mw.progress.single_shots == []


def test_does_nothing_when_setting_is_off(monkeypatch):
    env = setup_add_time_evaluator(monkeypatch, generate_on_add=False)
    add_notes(env, [AddedNote(1)])

    assert env.mw.progress.single_shots == []


def test_failed_generation_frees_its_slot(monkeypatch):
    class FailingProcessor(MockProcessor):
        async def process_note(self, *args, **kwargs) -> bool:
            raise RuntimeError("provider exploded")

    env = setup_add_time_evaluator(monkeypatch)
    env.evaluator.processor = FailingProcessor()
    error_logs = []
    monkeypatch.setattr(env.module.logger, "error", error_logs.append)
    add_notes(env, [AddedNote(i) for i in range(1, 4)])

    fire_starts(env)
    run_jobs(env)

    assert env.evaluator.in_flight == 0
    assert len(error_logs) == 3


def test_out_of_credits_refreshes_account_and_frees_slot(monkeypatch):
    class BrokeProcessor(MockProcessor):
        async def process_note(self, *args, **kwargs) -> bool:
            raise OutOfCreditsError()

    env = setup_add_time_evaluator(monkeypatch)
    env.evaluator.processor = BrokeProcessor()
    refreshes = []
    monkeypatch.setattr(
        env.module.app_state, "update_account_state", lambda: refreshes.append(True)
    )
    add_notes(env, [AddedNote(1)])

    fire_starts(env)
    run_jobs(env)

    assert refreshes == [True]
    assert env.evaluator.in_flight == 0


def test_stop_ignores_scheduled_starts(monkeypatch):
    env = setup_add_time_evaluator(monkeypatch)
    add_notes(env, [AddedNote(1)])

    env.evaluator.stop()
    fire_starts(env)

    assert env.jobs == []
