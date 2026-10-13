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

import pytest
from fixtures import MockCard, MockConfig, MockNote, MockProcessor

from src.api_client import OutOfCreditsError


class AddedNote(MockNote):
    """A note as seen by note_will_be_added: the id is assigned after the add."""

    def __init__(self, note_id: int, *, did: int = 1, processed: bool = False):
        super().__init__({"f1": "1"}, note_id=0)
        self.added_id = note_id
        self.card = MockCard(id=note_id, did=did, processed=processed, note=self)

    def finish_add(self) -> None:
        self.id = self.added_id

    def cards(self) -> list[MockCard]:
        return [self.card]


class MockCollection:
    def __init__(self) -> None:
        self.notes: dict[int, AddedNote] = {}

    def get_note(self, note_id: int) -> AddedNote:
        return self.notes[note_id]


class MockProgress:
    def __init__(self) -> None:
        self.single_shots: list = []

    def single_shot(self, ms: int, func) -> None:
        self.single_shots.append(func)


def setup_add_time_evaluator(monkeypatch, *, generate_on_add=True):
    import src.add_time_evaluator

    processor = MockProcessor()
    evaluator = src.add_time_evaluator.AddTimeEvaluator(processor)
    mw = SimpleNamespace(col=MockCollection(), progress=MockProgress())
    cfg = MockConfig()
    cfg.generate_on_add = generate_on_add
    waves: list = []
    tooltips: list[str] = []
    monkeypatch.setattr(src.add_time_evaluator, "mw", mw)
    monkeypatch.setattr(src.add_time_evaluator, "config", cfg)
    monkeypatch.setattr(src.add_time_evaluator, "run_on_main", lambda work: work())
    monkeypatch.setattr(src.add_time_evaluator, "tooltip", tooltips.append)
    monkeypatch.setattr(
        src.add_time_evaluator, "is_capacity_remaining_or_legacy", lambda: True
    )
    monkeypatch.setattr(
        src.add_time_evaluator, "is_card_fully_processed", lambda card: card.processed
    )
    monkeypatch.setattr(
        src.add_time_evaluator,
        "run_async_in_background_with_sentry",
        lambda op, on_success, on_failure, use_collection: waves.append(
            (op, on_success, on_failure)
        ),
    )
    return SimpleNamespace(
        evaluator=evaluator,
        processor=processor,
        mw=mw,
        waves=waves,
        tooltips=tooltips,
        module=src.add_time_evaluator,
    )


def add_notes(env, notes: list[AddedNote]) -> None:
    """Simulate col.add_notes: the hook fires for every note, then ids land."""
    for note in notes:
        env.evaluator.on_note_will_be_added(note)
    for note in notes:
        note.finish_add()
        env.mw.col.notes[note.id] = note


def fire_drain(env) -> None:
    shots = env.mw.progress.single_shots[:]
    env.mw.progress.single_shots.clear()
    for shot in shots:
        shot()


def run_wave(env) -> None:
    op, on_success, _ = env.waves.pop(0)
    asyncio.run(op())
    on_success(None)


def test_burst_is_processed_in_waves_one_at_a_time(monkeypatch):
    env = setup_add_time_evaluator(monkeypatch)
    add_notes(env, [AddedNote(i, did=i) for i in range(1, 26)])

    # One drain is scheduled for the whole burst.
    assert len(env.mw.progress.single_shots) == 1
    fire_drain(env)

    assert len(env.waves) == 1
    assert env.evaluator.wave_in_progress

    # More adds while a wave runs don't start a second concurrent wave.
    add_notes(env, [AddedNote(100, did=100)])
    fire_drain(env)
    assert len(env.waves) == 1

    wave_sizes = []
    while env.waves:
        before = len(env.processor.processed_cards)
        run_wave(env)
        wave_sizes.append(len(env.processor.processed_cards) - before)

    assert wave_sizes == [10, 10, 6]
    assert sorted(env.processor.processed_cards) == [*range(1, 26), 100]
    assert not env.evaluator.wave_in_progress


def test_bulk_add_beyond_limit_is_skipped_and_reported(monkeypatch):
    env = setup_add_time_evaluator(monkeypatch)
    monkeypatch.setattr(env.module, "MAX_PENDING", 5)
    add_notes(env, [AddedNote(i) for i in range(1, 9)])

    fire_drain(env)
    while env.waves:
        run_wave(env)

    assert len(env.processor.processed_cards) == 5
    assert len(env.tooltips) == 1
    assert "3" in env.tooltips[0]


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

    fire_drain(env)
    run_wave(env)

    assert env.processor.processed_cards == [4]


def test_does_nothing_when_setting_is_off(monkeypatch):
    env = setup_add_time_evaluator(monkeypatch, generate_on_add=False)
    add_notes(env, [AddedNote(1)])

    assert env.mw.progress.single_shots == []
    assert not env.evaluator.pending


def test_out_of_credits_drops_queue_and_refreshes_account(monkeypatch):
    class BrokeProcessor(MockProcessor):
        async def process_note(self, *args, **kwargs) -> bool:
            raise OutOfCreditsError()

    env = setup_add_time_evaluator(monkeypatch)
    env.evaluator.processor = BrokeProcessor()
    refreshes = []
    monkeypatch.setattr(
        env.module.app_state, "update_account_state", lambda: refreshes.append(True)
    )
    add_notes(env, [AddedNote(i) for i in range(1, 16)])
    fire_drain(env)

    op, _, on_failure = env.waves.pop(0)
    with pytest.raises(OutOfCreditsError):
        asyncio.run(op())
    on_failure(OutOfCreditsError())

    assert not env.evaluator.pending
    assert env.waves == []
    assert refreshes == [True]


def test_stop_drops_pending_and_ignores_completion(monkeypatch):
    env = setup_add_time_evaluator(monkeypatch)
    add_notes(env, [AddedNote(i) for i in range(1, 16)])
    fire_drain(env)

    env.evaluator.stop()
    run_wave(env)
    add_notes(env, [AddedNote(99)])
    fire_drain(env)

    assert env.processor.processed_cards == []
    assert env.waves == []
