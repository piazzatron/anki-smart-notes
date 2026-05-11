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
        self.in_flight: set[int] = set()
        self.batch_in_progress = False
        self.processed_cards: list[int] = []

    async def _process_note(
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


def setup_review_prepper(monkeypatch, current=None, queued=None):
    import src.review_prepper

    if queued is None:
        queued = []

    processor = MockProcessor()
    prepper = src.review_prepper.ReviewPrepper(processor)  # type: ignore
    monkeypatch.setattr(src.review_prepper, "mw", MockMw(current, queued))
    monkeypatch.setattr(src.review_prepper, "config", MockConfig())
    monkeypatch.setattr(
        src.review_prepper,
        "is_capacity_remaining_or_legacy",
        lambda show_box=False: True,
    )
    monkeypatch.setattr(
        src.review_prepper,
        "is_card_fully_processed",
        lambda card: card.processed,
    )
    monkeypatch.setattr(
        src.review_prepper,
        "Card",
        lambda col, backend_card: backend_card,
    )
    return prepper, processor, src.review_prepper


def test_tick_sets_pending_tick_when_batch_in_progress(monkeypatch):
    prepper, processor, _ = setup_review_prepper(
        monkeypatch,
        current=MockCard(id=1),
        queued=[],
    )
    processor.batch_in_progress = True

    prepper.tick()

    assert prepper.pending_tick


def test_tick_filters_in_flight_and_processed_cards(monkeypatch):
    started_batches = []
    current = MockCard(id=1, processed=True)
    queued = [
        MockCard(id=2),
        MockCard(id=3, processed=True),
        MockCard(id=4),
    ]
    prepper, processor, review_prepper = setup_review_prepper(
        monkeypatch,
        current=current,
        queued=queued,
    )
    processor.in_flight.add(2)
    monkeypatch.setattr(
        review_prepper,
        "run_async_in_background_with_sentry",
        lambda op,
        on_success,
        on_failure=None,
        with_progress=False,
        use_collection=True: started_batches.append((op, use_collection)),
    )

    prepper.tick()

    assert processor.in_flight == {2, 4}
    assert processor.batch_in_progress
    assert len(started_batches) == 1
    assert started_batches[0][1] is False


def test_tick_skips_tiny_top_off_when_buffer_is_comfortable(monkeypatch):
    started_batches = []
    queued = [
        *[MockCard(id=i, processed=True) for i in range(1, 11)],
        MockCard(id=11),
    ]
    prepper, processor, review_prepper = setup_review_prepper(
        monkeypatch,
        current=MockCard(id=99, processed=True),
        queued=queued,
    )
    monkeypatch.setattr(review_prepper, "MIN_TOP_OFF", 10)
    monkeypatch.setattr(
        review_prepper,
        "run_async_in_background_with_sentry",
        lambda *args, **kwargs: started_batches.append(args),
    )

    prepper.tick()

    assert started_batches == []
    assert processor.in_flight == set()
    assert not processor.batch_in_progress


def test_current_card_bypasses_top_off_gate(monkeypatch):
    started_batches = []
    queued = [MockCard(id=i, processed=True) for i in range(1, 11)]
    prepper, processor, review_prepper = setup_review_prepper(
        monkeypatch,
        current=MockCard(id=99),
        queued=queued,
    )
    monkeypatch.setattr(review_prepper, "MIN_TOP_OFF", 10)
    monkeypatch.setattr(
        review_prepper,
        "run_async_in_background_with_sentry",
        lambda *args, **kwargs: started_batches.append(args),
    )

    prepper.tick()

    assert len(started_batches) == 1
    assert processor.in_flight == {99}
    assert processor.batch_in_progress


def test_pending_tick_refires_after_completion(monkeypatch):
    started_batches = []
    prepper, processor, review_prepper = setup_review_prepper(
        monkeypatch,
        current=MockCard(id=1),
        queued=[],
    )
    monkeypatch.setattr(
        review_prepper,
        "run_async_in_background_with_sentry",
        lambda *args, **kwargs: started_batches.append(args),
    )
    prepper.pending_tick = True

    prepper.on_complete(None)

    assert not prepper.pending_tick
    assert processor.batch_in_progress
    assert processor.in_flight == {1}
    assert len(started_batches) == 1


def test_tick_clears_stale_pending_tick_when_starting_batch(monkeypatch):
    started_batches = []
    prepper, processor, review_prepper = setup_review_prepper(
        monkeypatch,
        current=MockCard(id=1),
        queued=[],
    )
    prepper.pending_tick = True
    monkeypatch.setattr(
        review_prepper,
        "run_async_in_background_with_sentry",
        lambda *args, **kwargs: started_batches.append(args),
    )

    prepper.tick()

    assert not prepper.pending_tick
    assert processor.batch_in_progress
    assert processor.in_flight == {1}
    assert len(started_batches) == 1


def test_maybe_redraw_only_for_current_card(monkeypatch):
    current = MockCard(id=1)
    prepper, _, review_prepper = setup_review_prepper(
        monkeypatch,
        current=current,
        queued=[],
    )
    sparkles = []
    monkeypatch.setattr(review_prepper, "Sparkle", lambda: sparkles.append(True))

    prepper.maybe_redraw_and_sparkle(2, True)
    prepper.maybe_redraw_and_sparkle(1, False)
    prepper.maybe_redraw_and_sparkle(1, True)

    assert review_prepper.mw.reviewer.redraws == 1
    assert sparkles == [True]


@pytest.mark.asyncio
async def test_run_batch_updates_state_for_each_card(monkeypatch):
    prepper, processor, review_prepper = setup_review_prepper(
        monkeypatch,
        current=MockCard(id=1),
        queued=[],
    )
    processor.in_flight.update({1, 2})
    redraws = []
    monkeypatch.setattr(
        review_prepper,
        "run_on_main",
        lambda work: redraws.append(work),
    )

    await prepper.run_batch([MockCard(id=1, did=10), MockCard(id=2, did=20)])

    assert processor.in_flight == set()
    assert processor.processed_cards == [10, 20]
    assert len(redraws) == 2
