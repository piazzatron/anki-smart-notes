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

LOOKAHEAD = 30
MIN_TOP_OFF = 10


class ReviewPrepper:
    def __init__(self, processor: NoteProcessor) -> None:
        self.processor = processor
        self.pending_tick = False

    def tick(self) -> None:
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

        candidates: list[Card] = []
        current_card_needs_processing = self.add_current_card_if_eligible(candidates)
        processed_ahead_count = self.add_queued_cards_if_eligible(candidates)

        if not candidates:
            return

        if (
            not current_card_needs_processing
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

    def add_current_card_if_eligible(self, candidates: list[Card]) -> bool:
        reviewer = mw.reviewer if mw else None
        card = reviewer.card if reviewer else None
        if not card or not self.is_card_eligible(card):
            return False

        candidates.append(card)
        return True

    def add_queued_cards_if_eligible(self, candidates: list[Card]) -> int:
        if not mw or not mw.col:
            return 0

        processed_ahead_count = 0
        candidate_ids = {card.id for card in candidates}
        scheduler: Any = mw.col.sched
        if not hasattr(scheduler, "get_queued_cards"):
            return 0

        for queued_card in scheduler.get_queued_cards(fetch_limit=LOOKAHEAD).cards:
            card = Card(mw.col, backend_card=queued_card.card)
            if card.id in candidate_ids:
                continue
            if card.id in self.processor.in_flight:
                continue
            if is_card_fully_processed(card):
                processed_ahead_count += 1
                continue

            candidates.append(card)
            candidate_ids.add(card.id)

        return processed_ahead_count

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
