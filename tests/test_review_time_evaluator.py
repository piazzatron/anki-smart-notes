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

import pytest
from fixtures import MockCard, MockConfig, MockProcessor

from src.api_client import ClientFacingAPIError


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
    def __init__(
        self, current: MockCard | None, queued: list[MockCard], state: str
    ) -> None:
        self.state = state
        self.col = MockCollection(queued)
        self.reviewer = MockReviewer(current)


def setup_review_time_evaluator(monkeypatch, current=None, queued=None, state="review"):
    import src.review_time_evaluator

    if queued is None:
        queued = []

    processor = MockProcessor()
    evaluator = src.review_time_evaluator.ReviewTimeEvaluator(processor)  # type: ignore
    monkeypatch.setattr(src.review_time_evaluator, "mw", MockMw(current, queued, state))
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
    monkeypatch.setattr(review_time_evaluator, "MIN_BATCH_SIZE", 10)
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
    monkeypatch.setattr(review_time_evaluator, "MIN_BATCH_SIZE", 10)
    monkeypatch.setattr(
        review_time_evaluator,
        "run_async_in_background_with_sentry",
        lambda *args, **kwargs: started_batches.append(args),
    )

    evaluator.tick()

    assert len(started_batches) == 1
    assert evaluator.in_flight == {1}
    assert evaluator.wave_in_progress


def test_tick_processes_initial_wave_from_overview(monkeypatch):
    started_batches = []
    evaluator, _, review_time_evaluator = setup_review_time_evaluator(
        monkeypatch,
        current=MockCard(id=99),
        queued=[MockCard(id=1)],
        state="overview",
    )
    monkeypatch.setattr(review_time_evaluator, "MIN_BATCH_SIZE", 10)
    monkeypatch.setattr(
        review_time_evaluator,
        "run_async_in_background_with_sentry",
        lambda *args, **kwargs: started_batches.append(args),
    )

    evaluator.tick()

    assert len(started_batches) == 1
    assert evaluator.in_flight == {1}
    assert evaluator.wave_in_progress


def test_tick_ignores_non_review_states(monkeypatch):
    started_batches = []
    evaluator, _, review_time_evaluator = setup_review_time_evaluator(
        monkeypatch,
        current=MockCard(id=99),
        queued=[MockCard(id=1)],
        state="deckBrowser",
    )
    monkeypatch.setattr(
        review_time_evaluator,
        "run_async_in_background_with_sentry",
        lambda *args, **kwargs: started_batches.append(args),
    )

    evaluator.tick()

    assert started_batches == []
    assert evaluator.in_flight == set()
    assert not evaluator.wave_in_progress


def test_tick_ignores_stopped_evaluator(monkeypatch):
    started_batches = []
    evaluator, _, review_time_evaluator = setup_review_time_evaluator(
        monkeypatch,
        current=MockCard(id=99),
        queued=[MockCard(id=1)],
    )
    monkeypatch.setattr(
        review_time_evaluator,
        "run_async_in_background_with_sentry",
        lambda *args, **kwargs: started_batches.append(args),
    )

    evaluator.stop()
    evaluator.tick()

    assert started_batches == []
    assert evaluator.in_flight == set()
    assert not evaluator.wave_in_progress


def test_current_card_bypasses_top_off_gate(monkeypatch):
    started_batches = []
    queued = [MockCard(id=i, processed=True) for i in range(1, 11)]
    evaluator, _, review_time_evaluator = setup_review_time_evaluator(
        monkeypatch,
        current=MockCard(id=99),
        queued=queued,
    )
    monkeypatch.setattr(review_time_evaluator, "MIN_BATCH_SIZE", 10)
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


def test_stopped_evaluator_drops_pending_tick(monkeypatch):
    started_batches = []
    evaluator, _, review_time_evaluator = setup_review_time_evaluator(
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

    evaluator.stop()
    evaluator.on_complete(None)

    assert not evaluator.pending_tick
    assert not evaluator.wave_in_progress
    assert evaluator.in_flight == set()
    assert started_batches == []


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


@pytest.mark.asyncio
async def test_run_card_task_logs_client_facing_errors_without_error_level(
    monkeypatch,
):
    class FailingProcessor(MockProcessor):
        async def process_note(self, *args, **kwargs) -> bool:
            raise ClientFacingAPIError("Try a different provider.")

    evaluator, _, review_time_evaluator = setup_review_time_evaluator(
        monkeypatch,
        current=MockCard(id=1),
        queued=[],
    )
    evaluator.processor = FailingProcessor()  # type: ignore[assignment]
    evaluator.in_flight.add(1)
    error_logs = []
    info_logs = []
    redraws = []
    monkeypatch.setattr(review_time_evaluator.logger, "error", error_logs.append)
    monkeypatch.setattr(review_time_evaluator.logger, "info", info_logs.append)
    monkeypatch.setattr(
        review_time_evaluator, "run_on_main", lambda work: redraws.append(work)
    )

    await evaluator.run_card_task(MockCard(id=1, did=10))

    assert evaluator.in_flight == set()
    assert error_logs == []
    assert info_logs == [
        "Client-facing error prepping card 1: Try a different provider."
    ]
    assert len(redraws) == 1


@pytest.mark.asyncio
async def test_run_card_task_suppresses_shutdown_errors(monkeypatch):
    evaluator, _, review_time_evaluator = setup_review_time_evaluator(
        monkeypatch,
        current=MockCard(id=1),
        queued=[],
    )

    class ClosingProcessor(MockProcessor):
        async def process_note(self, *args, **kwargs) -> bool:
            evaluator.stop()
            raise RuntimeError("CollectionNotOpen")

    evaluator.processor = ClosingProcessor()  # type: ignore[assignment]
    evaluator.in_flight.add(1)
    error_logs = []
    info_logs = []
    redraws = []
    monkeypatch.setattr(review_time_evaluator.logger, "error", error_logs.append)
    monkeypatch.setattr(review_time_evaluator.logger, "info", info_logs.append)
    monkeypatch.setattr(
        review_time_evaluator, "run_on_main", lambda work: redraws.append(work)
    )

    await evaluator.run_card_task(MockCard(id=1, did=10))

    assert evaluator.in_flight == set()
    assert error_logs == []
    assert info_logs == ["Stopped review-time card task 1 during profile cleanup"]
    assert redraws == []
