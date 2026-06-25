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
from typing import Any, cast

from anki.cards import Card, CardId
from anki.scheduler.v3 import Scheduler
from aqt import mw

from .api_client import ClientFacingAPIError, OutOfCreditsError
from .app_state import app_state, is_capacity_remaining_or_legacy
from .config import config
from .logger import logger
from .note_proccessor import NoteProcessor
from .sentry import run_async_in_background_with_sentry
from .ui.sparkle import Sparkle
from .utils import run_on_main
from .utils.notes_utils import is_card_fully_processed

# Number of upcoming scheduler cards to inspect on each review tick.
LOOKAHEAD = 25

# Minimum number of uncovered queued cards required before firing a normal
# top-off batch. Smaller batches still run when they flush the end of the queue.
MIN_BATCH_SIZE = 5


class ReviewTimeEvaluator:
    """Keeps review-time Smart Field generation ahead of the reviewer.

    Each overview or reviewer tick evaluates the current card plus the scheduler
    lookahead queue, starts one background generation wave when useful, and
    redraws only the currently visible card as individual card tasks complete.
    """

    def __init__(self, processor: NoteProcessor) -> None:
        self.processor = processor
        self.in_flight: set[CardId] = set()
        self.wave_in_progress = False
        self.pending_tick = False

    def tick(self) -> None:
        # Overview and review hooks call tick() when the deck overview loads or
        # the current card changes/is answered. The evaluator keeps a small
        # generation buffer ahead of the reviewer: include the current card if
        # review mode has one that still needs fields, scan Anki's scheduler
        # lookahead for more eligible cards, and start one background wave for
        # the uncovered cards.
        #
        # Only one review wave may run at a time. If a prior review wave is active,
        # remember that another tick is needed and replay it when the active wave
        # completes. Otherwise, wait until enough uncovered cards have accumulated,
        # unless the scheduler returned fewer than LOOKAHEAD cards and this wave should
        # flush the end-of-queue leftovers.
        if not mw or not mw.col or mw.state not in {"overview", "review"}:
            return

        if not config.generate_at_review:
            return

        if not is_capacity_remaining_or_legacy(show_box=False):
            return

        if self.wave_in_progress:
            self.pending_tick = True
            return

        self.pending_tick = False
        logger.info("Starting review-time evaluation tick")

        reviewer = mw.reviewer if mw.state == "review" else None
        current_card = reviewer.card if reviewer else None
        current_card_candidates = (
            [current_card]
            if current_card and self.is_card_eligible(current_card)
            else []
        )
        queued_card_candidates, hit_end_of_queue = self.get_queued_card_candidates(
            existing_candidate_ids={card.id for card in current_card_candidates}
        )

        logger.debug(
            f"Found {len(current_card_candidates)} eligible current card(s) and {len(queued_card_candidates)} eligible queued card(s) for review-time evaluation"
        )

        candidates = current_card_candidates + queued_card_candidates

        if not candidates:
            logger.info("Zero eligible cards found for review-time evaluation")
            return

        if (
            not current_card_candidates
            and len(queued_card_candidates) < MIN_BATCH_SIZE
            and not hit_end_of_queue
        ):
            logger.info(
                "Not enough eligible cards to start review-time evaluation wave"
            )
            return

        for card in candidates:
            self.in_flight.add(card.id)

        # tick() runs synchronously on the main thread, so another hook cannot
        # enter between the early wave_in_progress check and this assignment.
        self.wave_in_progress = True

        run_async_in_background_with_sentry(
            lambda: self.run_batch(candidates),
            self.on_complete,
            self.on_complete_error,
            use_collection=False,
        )

    def get_queued_card_candidates(
        self, existing_candidate_ids: set[CardId]
    ) -> tuple[list[Card], bool]:
        if not mw or not mw.col:
            return ([], False)

        candidates: list[Card] = []
        candidate_ids = set(existing_candidate_ids)
        scheduler = cast(Scheduler, mw.col.sched)

        queued_cards = scheduler.get_queued_cards(fetch_limit=LOOKAHEAD).cards

        hit_end_of_queue = len(queued_cards) < LOOKAHEAD

        for queued_card in queued_cards:
            card = Card(mw.col, backend_card=queued_card.card)

            # The current card can also appear in Anki's lookahead queue, so
            # keep only the first copy of a card in this evaluation wave.
            if card.id in candidate_ids:
                continue

            # Avoid processing the same queued card twice while an earlier
            # review wave is still generating it.
            if card.id in self.in_flight:
                continue

            # Already-processed cards don't need to be included in the next
            # generation batch.
            if is_card_fully_processed(card):
                continue

            candidates.append(card)
            candidate_ids.add(card.id)

        return (candidates, hit_end_of_queue)

    def is_card_eligible(self, card: Card) -> bool:
        if card.id in self.in_flight:
            return False
        return not is_card_fully_processed(card)

    async def run_batch(self, candidates: list[Card]) -> None:
        logger.info(f"Starting review-time evaluation wave for {len(candidates)} cards")
        results = await asyncio.gather(
            *[self.run_card_task(card) for card in candidates],
            return_exceptions=True,
        )
        if any(isinstance(result, OutOfCreditsError) for result in results):
            raise OutOfCreditsError()

    async def run_card_task(self, card: Card) -> None:
        did_change = False
        try:
            did_change = await self.processor.process_note(
                card.note(), deck_id=card.did, overwrite_fields=False
            )
        except OutOfCreditsError:
            raise
        except Exception as e:
            if isinstance(e, ClientFacingAPIError):
                logger.info(f"Client-facing error prepping card {card.id}")
            else:
                logger.error(
                    f"Error prepping card {card.id}: {e}, {''.join(traceback.format_exception(type(e), e, e.__traceback__))}"
                )
        finally:
            self.in_flight.discard(card.id)

        run_on_main(
            lambda card_id=card.id,
            did_change=did_change: self.maybe_redraw_and_sparkle(card_id, did_change)
        )

    def on_complete(self, _: Any) -> None:
        self.wave_in_progress = False
        self.process_pending_tick()

    def on_complete_error(self, e: Exception) -> None:
        self.wave_in_progress = False
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
