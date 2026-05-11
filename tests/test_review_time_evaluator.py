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

from dataclasses import dataclass
from typing import Any

import pytest


@dataclass
class MockCard:
    id: int
    did: int = 1
    processed: bool = False

    def note(self) -> Any:
        return object()


class MockProcessor:
    def __init__(self) -> None:
        self.processed_cards: list[int] = []

    async def process_note(
        self,
        note: Any,
        deck_id: int,
        overwrite_fields: bool = False,
    ) -> bool:
        self.processed_cards.append(deck_id)
        return True


class MockQueuedCard:
    def __init__(self, card: MockCard) -> None:
        self.card = card


class MockQueuedCards:
    def __init__(self, cards: list[MockCard]) -> None:
        self.cards = [MockQueuedCard(card) for card in cards]


class MockSched:
    def __init__(self, cards: list[MockCard]) -> None:
        self.cards = cards
        self.fetch_limits: list[int] = []

    def get_queued_cards(self, fetch_limit: int) -> MockQueuedCards:
        self.fetch_limits.append(fetch_limit)
        return MockQueuedCards(self.cards[:fetch_limit])


class MockCollection:
    def __init__(self, cards: list[MockCard]) -> None:
        self.sched = MockSched(cards)


class MockReviewer:
    def __init__(self, card: MockCard | None) -> None:
        self.card = card
        self.redraws = 0

    def _redraw_current_card(self) -> None:
        self.redraws += 1


class MockMw:
    def __init__(self, current: MockCard | None, queued: list[MockCard]) -> None:
        self.state = "review"
        self.col = MockCollection(queued)
        self.reviewer = MockReviewer(current)


class MockConfig:
    generate_at_review = True


def setup_review_time_evaluator(monkeypatch, current=None, queued=None):
    import src.review_time_evaluator

    if queued is None:
        queued = []

    processor = MockProcessor()
    evaluator = src.review_time_evaluator.ReviewTimeEvaluator(processor)  # type: ignore
    monkeypatch.setattr(src.review_time_evaluator, "mw", MockMw(current, queued))
    monkeypatch.setattr(src.review_time_evaluator, "config", MockConfig())
    monkeypatch.setattr(
        src.review_time_evaluator,
        "is_capacity_remaining_or_legacy",
        lambda show_box=False: True,
    )
    monkeypatch.setattr(
        src.review_time_evaluator,
        "is_card_fully_processed",
        lambda card: card.processed,
    )
    monkeypatch.setattr(
        src.review_time_evaluator,
        "Card",
        lambda col, backend_card: backend_card,
    )
    return evaluator, processor, src.review_time_evaluator


def test_tick_sets_pending_tick_when_wave_in_progress(monkeypatch):
    evaluator, _, _ = setup_review_time_evaluator(
        monkeypatch,
        current=MockCard(id=1),
        queued=[],
    )
    evaluator.wave_in_progress = True

    evaluator.tick()

    assert evaluator.pending_tick


def test_get_queued_card_candidates_does_not_mutate_existing_ids(monkeypatch):
    existing_candidate_ids = {1}
    evaluator, _, _ = setup_review_time_evaluator(
        monkeypatch,
        current=None,
        queued=[
            MockCard(id=1),
            MockCard(id=2),
            MockCard(id=3, processed=True),
        ],
    )
    evaluator.in_flight.add(4)

    candidates, hit_end_of_queue = evaluator.get_queued_card_candidates(
        existing_candidate_ids
    )

    assert [card.id for card in candidates] == [2]
    assert hit_end_of_queue
    assert existing_candidate_ids == {1}


def test_tick_filters_in_flight_and_processed_cards(monkeypatch):
    started_batches = []
    current = MockCard(id=1, processed=True)
    queued = [
        MockCard(id=2),
        MockCard(id=3, processed=True),
        MockCard(id=4),
    ]
    evaluator, _, review_time_evaluator = setup_review_time_evaluator(
        monkeypatch,
        current=current,
        queued=queued,
    )
    evaluator.in_flight.add(2)
    monkeypatch.setattr(
        review_time_evaluator,
        "run_async_in_background_with_sentry",
        lambda op,
        on_success,
        on_failure=None,
        with_progress=False,
        use_collection=True: started_batches.append((op, use_collection)),
    )

    evaluator.tick()

    assert evaluator.in_flight == {2, 4}
    assert evaluator.wave_in_progress
    assert len(started_batches) == 1
    assert started_batches[0][1] is False


def test_tick_skips_tiny_top_off_when_queue_has_more_cards(monkeypatch):
    started_batches = []
    queued = [
        MockCard(id=1),
        *[MockCard(id=i, processed=True) for i in range(2, 31)],
    ]
    evaluator, _, review_time_evaluator = setup_review_time_evaluator(
        monkeypatch,
        current=MockCard(id=99, processed=True),
        queued=queued,
    )
    monkeypatch.setattr(review_time_evaluator, "MIN_TOP_OFF", 10)
    monkeypatch.setattr(
        review_time_evaluator,
        "run_async_in_background_with_sentry",
        lambda *args, **kwargs: started_batches.append(args),
    )

    evaluator.tick()

    assert started_batches == []
    assert evaluator.in_flight == set()
    assert not evaluator.wave_in_progress


def test_tick_processes_tiny_top_off_at_end_of_queue(monkeypatch):
    started_batches = []
    evaluator, _, review_time_evaluator = setup_review_time_evaluator(
        monkeypatch,
        current=MockCard(id=99, processed=True),
        queued=[MockCard(id=1)],
    )
    monkeypatch.setattr(review_time_evaluator, "MIN_TOP_OFF", 10)
    monkeypatch.setattr(
        review_time_evaluator,
        "run_async_in_background_with_sentry",
        lambda *args, **kwargs: started_batches.append(args),
    )

    evaluator.tick()

    assert len(started_batches) == 1
    assert evaluator.in_flight == {1}
    assert evaluator.wave_in_progress


def test_current_card_bypasses_top_off_gate(monkeypatch):
    started_batches = []
    queued = [MockCard(id=i, processed=True) for i in range(1, 11)]
    evaluator, _, review_time_evaluator = setup_review_time_evaluator(
        monkeypatch,
        current=MockCard(id=99),
        queued=queued,
    )
    monkeypatch.setattr(review_time_evaluator, "MIN_TOP_OFF", 10)
    monkeypatch.setattr(
        review_time_evaluator,
        "run_async_in_background_with_sentry",
        lambda *args, **kwargs: started_batches.append(args),
    )

    evaluator.tick()

    assert len(started_batches) == 1
    assert evaluator.in_flight == {99}
    assert evaluator.wave_in_progress


def test_pending_tick_refires_after_completion(monkeypatch):
    started_batches = []
    evaluator, processor, review_time_evaluator = setup_review_time_evaluator(
        monkeypatch,
        current=MockCard(id=1),
        queued=[],
    )
    monkeypatch.setattr(
        review_time_evaluator,
        "run_async_in_background_with_sentry",
        lambda *args, **kwargs: started_batches.append(args),
    )
    evaluator.pending_tick = True

    evaluator.on_complete(None)

    assert not evaluator.pending_tick
    assert evaluator.wave_in_progress
    assert evaluator.in_flight == {1}
    assert len(started_batches) == 1


def test_tick_clears_stale_pending_tick_when_starting_batch(monkeypatch):
    started_batches = []
    evaluator, processor, review_time_evaluator = setup_review_time_evaluator(
        monkeypatch,
        current=MockCard(id=1),
        queued=[],
    )
    evaluator.pending_tick = True
    monkeypatch.setattr(
        review_time_evaluator,
        "run_async_in_background_with_sentry",
        lambda *args, **kwargs: started_batches.append(args),
    )

    evaluator.tick()

    assert not evaluator.pending_tick
    assert evaluator.wave_in_progress
    assert evaluator.in_flight == {1}
    assert len(started_batches) == 1


def test_maybe_redraw_only_for_current_card(monkeypatch):
    current = MockCard(id=1)
    evaluator, _, review_time_evaluator = setup_review_time_evaluator(
        monkeypatch,
        current=current,
        queued=[],
    )
    sparkles = []
    monkeypatch.setattr(review_time_evaluator, "Sparkle", lambda: sparkles.append(True))

    evaluator.maybe_redraw_and_sparkle(2, True)
    evaluator.maybe_redraw_and_sparkle(1, False)
    evaluator.maybe_redraw_and_sparkle(1, True)

    assert review_time_evaluator.mw.reviewer.redraws == 1
    assert sparkles == [True]


@pytest.mark.asyncio
async def test_run_batch_updates_state_for_each_card(monkeypatch):
    evaluator, processor, review_time_evaluator = setup_review_time_evaluator(
        monkeypatch,
        current=MockCard(id=1),
        queued=[],
    )
    evaluator.in_flight.update({1, 2})
    redraws = []
    monkeypatch.setattr(
        review_time_evaluator,
        "run_on_main",
        lambda work: redraws.append(work),
    )

    await evaluator.run_batch([MockCard(id=1, did=10), MockCard(id=2, did=20)])

    assert evaluator.in_flight == set()
    assert processor.processed_cards == [10, 20]
    assert len(redraws) == 2
