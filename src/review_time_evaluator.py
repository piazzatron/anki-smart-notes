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
import traceback
from typing import Any

from anki.cards import Card, CardId
from aqt import mw

from .api_client import OutOfCreditsError
from .app_state import app_state, is_capacity_remaining_or_legacy
from .config import config
from .logger import logger
from .note_proccessor import NoteProcessor
from .notes import is_card_fully_processed
from .sentry import run_async_in_background_with_sentry
from .ui.sparkle import Sparkle
from .utils import run_on_main

# Number of upcoming scheduler cards to inspect on each review tick.
LOOKAHEAD = 30

# Minimum uncovered queue size required before firing a top-off batch when the
# reviewer already has a comfortable buffer of processed cards ahead.
MIN_TOP_OFF = 10


class ReviewTimeEvaluator:
    """Keeps review-time Smart Field generation ahead of the reviewer.

    Each reviewer tick evaluates the current card plus the scheduler lookahead
    queue, starts one background generation wave when useful, and redraws only
    the currently visible card as individual card tasks complete.
    """

    def __init__(self, processor: NoteProcessor) -> None:
        self.processor = processor
        self.pending_tick = False

    def tick(self) -> None:
        # Review hooks call tick() whenever the current card changes or is answered.
        # The evaluator keeps a small generation buffer ahead of the reviewer: include
        # the current card if it still needs fields, scan Anki's scheduler lookahead for
        # more eligible cards, and start one background wave for the uncovered cards.
        #
        # Only one batch-style operation may run at a time. If a browser batch or prior
        # review wave is active, remember that another tick is needed and replay it when
        # the active batch completes. Once the reviewer already has enough processed
        # cards ahead, avoid firing tiny top-off batches until enough uncovered cards
        # accumulate.
        if not mw or not mw.col or mw.state != "review":
            return

        if not config.generate_at_review:
            return

        if not is_capacity_remaining_or_legacy(show_box=False):
            return

        if self.processor.batch_in_progress:
            self.pending_tick = True
            return

        self.pending_tick = False

        reviewer = mw.reviewer
        current_card = reviewer.card if reviewer else None
        current_card_candidates = (
            [current_card]
            if current_card and self.is_card_eligible(current_card)
            else []
        )
        queued_card_candidates, processed_ahead_count = self.get_queued_card_candidates(
            existing_candidate_ids={card.id for card in current_card_candidates}
        )
        candidates = current_card_candidates + queued_card_candidates

        if not candidates:
            return

        if (
            not current_card_candidates
            and len(candidates) < MIN_TOP_OFF
            and processed_ahead_count >= MIN_TOP_OFF
        ):
            return

        for card in candidates:
            self.processor.in_flight.add(card.id)
        self.processor.batch_in_progress = True

        run_async_in_background_with_sentry(
            lambda: self.run_batch(candidates),
            self.on_complete,
            self.on_complete_error,
            use_collection=False,
        )

    def get_queued_card_candidates(
        self, existing_candidate_ids: set[CardId]
    ) -> tuple[list[Card], int]:
        if not mw or not mw.col:
            return ([], 0)

        candidates: list[Card] = []
        processed_ahead_count = 0
        candidate_ids = set(existing_candidate_ids)
        scheduler: Any = mw.col.sched

        for queued_card in scheduler.get_queued_cards(fetch_limit=LOOKAHEAD).cards:
            card = Card(mw.col, backend_card=queued_card.card)

            # The current card can also appear in Anki's lookahead queue, so
            # keep only the first copy of a card in this evaluation wave.
            if card.id in candidate_ids:
                continue

            # Other generation entry points share this set, which prevents
            # overlapping work when the reviewer and editor/browser both tick.
            if card.id in self.processor.in_flight:
                continue

            # Processed cards count toward the user's ahead-of-time buffer, but
            # they don't need to be included in the next generation batch.
            if is_card_fully_processed(card):
                processed_ahead_count += 1
                continue

            candidates.append(card)
            candidate_ids.add(card.id)

        return (candidates, processed_ahead_count)

    def is_card_eligible(self, card: Card) -> bool:
        if card.id in self.processor.in_flight:
            return False
        return not is_card_fully_processed(card)

    async def run_batch(self, candidates: list[Card]) -> None:
        results = await asyncio.gather(
            *[self.run_card_task(card) for card in candidates],
            return_exceptions=True,
        )
        if any(isinstance(result, OutOfCreditsError) for result in results):
            raise OutOfCreditsError()

    async def run_card_task(self, card: Card) -> None:
        did_change = False
        try:
            did_change = await self.processor._process_note(  # type: ignore
                card.note(), deck_id=card.did, overwrite_fields=False
            )
        except OutOfCreditsError:
            raise
        except Exception as e:
            logger.error(
                f"Error prepping card {card.id}: {e}, {''.join(traceback.format_exception(type(e), e, e.__traceback__))}"
            )
        finally:
            self.processor.in_flight.discard(card.id)

        run_on_main(
            lambda card_id=card.id,
            did_change=did_change: self.maybe_redraw_and_sparkle(card_id, did_change)
        )

    def on_complete(self, _: Any) -> None:
        self.processor.batch_in_progress = False
        self.process_pending_tick()

    def on_complete_error(self, e: Exception) -> None:
        self.processor.batch_in_progress = False
        if isinstance(e, OutOfCreditsError):
            app_state.update_subscription_state()
        self.process_pending_tick()

    def process_pending_tick(self) -> None:
        if not self.pending_tick:
            return

        self.pending_tick = False
        self.tick()

    def maybe_redraw_and_sparkle(self, card_id: CardId, did_change: bool) -> None:
        if not did_change or not mw or not mw.reviewer:
            return

        reviewer: Any = mw.reviewer
        current_card = reviewer.card
        if current_card is not None and current_card.id == card_id:
            reviewer._redraw_current_card()
            Sparkle()
