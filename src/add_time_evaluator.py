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
from collections import deque
from typing import Any, Optional

from anki.cards import Card
from anki.notes import Note
from aqt import mw
from aqt.utils import tooltip

from .api_client import OutOfCreditsError, UserDisplayableError
from .app_state import app_state, is_capacity_remaining_or_legacy
from .config import config
from .logger import logger
from .note_proccessor import NoteProcessor
from .sentry import run_async_in_background_with_sentry
from .utils import run_on_main
from .utils.notes_utils import is_card_fully_processed

# Delay between an add and the drain that picks it up. Gives the add time to
# finish (note ids are assigned after note_will_be_added fires) and lets a burst
# of AnkiConnect adds coalesce into full waves.
DRAIN_DELAY_MS = 1000

# Maximum number of notes processed concurrently in one add-time wave.
MAX_WAVE_SIZE = 10

# Maximum number of added notes waiting for generation. Notes added beyond this
# (a bulk add from a script or another add-on) are left for review-time or
# browser batch generation instead of silently spending credits on all of them.
MAX_PENDING = 100


class AddTimeEvaluator:
    """Generates automatic Smart Fields for notes shortly after they are added.

    The main use case is notes created outside the Add dialog, such as through
    AnkiConnect by Yomitan. Added notes queue up and are processed in waves of
    at most MAX_WAVE_SIZE, one wave at a time.
    """

    def __init__(self, processor: NoteProcessor) -> None:
        self.processor = processor
        # Appended from whichever thread adds the note (the Add dialog adds on a
        # background thread) and drained on the main thread. deque append and
        # popleft are thread-safe.
        self.pending: deque[Note] = deque()
        self.dropped_count = 0
        self.drain_scheduled = False
        self.wave_in_progress = False
        self.is_stopped = False

    def stop(self) -> None:
        self.is_stopped = True
        self.pending.clear()
        self.dropped_count = 0
        self.drain_scheduled = False
        self.wave_in_progress = False

    def on_note_will_be_added(self, note: Note) -> None:
        if self.is_stopped or not config.generate_on_add:
            return

        if len(self.pending) >= MAX_PENDING:
            self.dropped_count += 1
        else:
            # The note has no id yet; the add assigns it to this same object
            # once the backend call returns.
            self.pending.append(note)

        run_on_main(self.schedule_drain)

    def schedule_drain(self) -> None:
        if self.is_stopped or self.drain_scheduled or not mw:
            return
        self.drain_scheduled = True
        mw.progress.single_shot(DRAIN_DELAY_MS, self.drain)

    def drain(self) -> None:
        self.drain_scheduled = False
        if self.is_stopped or not mw or not mw.col:
            return

        if self.dropped_count:
            logger.info(
                f"Skipped add-time generation for {self.dropped_count} note(s) beyond the {MAX_PENDING} note limit"
            )
            tooltip(
                f"Smart Notes: too many notes added at once. Skipped generating {self.dropped_count} of them."
            )
            self.dropped_count = 0

        # The active wave drains again when it completes.
        if self.wave_in_progress:
            return

        if not is_capacity_remaining_or_legacy():
            logger.info("Dropping add-time generation queue: no capacity")
            self.pending.clear()
            return

        candidates: list[Card] = []
        while self.pending and len(candidates) < MAX_WAVE_SIZE:
            note = self.pending.popleft()
            card = self.get_candidate_card(note)
            if card:
                candidates.append(card)

        if not candidates:
            return

        self.wave_in_progress = True
        run_async_in_background_with_sentry(
            lambda: self.run_batch(candidates),
            self.on_complete,
            self.on_complete_error,
            use_collection=False,
        )

    def get_candidate_card(self, added_note: Note) -> Optional[Card]:
        if not mw or not mw.col:
            return None

        # A note without an id never made it into the collection (the add failed).
        if not added_note.id:
            return None

        try:
            note = mw.col.get_note(added_note.id)
        except Exception:
            # Deleted again before the drain ran.
            return None

        # Prompts are scoped by deck, so use a real card's deck rather than the
        # requested one: a deck override on the card template can move it.
        cards = note.cards()
        if not cards:
            return None

        card = cards[0]
        return None if is_card_fully_processed(card) else card

    async def run_batch(self, candidates: list[Card]) -> None:
        if self.is_stopped:
            return

        logger.info(f"Starting add-time generation wave for {len(candidates)} notes")
        results = await asyncio.gather(
            *[self.run_card_task(card) for card in candidates],
            return_exceptions=True,
        )

        if any(isinstance(result, OutOfCreditsError) for result in results):
            raise OutOfCreditsError()

    async def run_card_task(self, card: Card) -> None:
        if self.is_stopped:
            return

        try:
            await self.processor.process_note(
                card.note(), deck_id=card.did, overwrite_fields=False
            )
        except OutOfCreditsError:
            raise
        except Exception as e:
            if self.is_stopped:
                logger.info(
                    f"Stopped add-time task for note {card.nid} during profile cleanup"
                )
            elif isinstance(e, UserDisplayableError):
                # Keep this below error level so expected per-note failures do not
                # become Sentry events through the logging integration.
                logger.info(f"User-displayable error generating note {card.nid}: {e}")
            else:
                logger.error(
                    f"Error generating note {card.nid}: {e}, {''.join(traceback.format_exception(type(e), e, e.__traceback__))}"
                )

    def on_complete(self, _: Any) -> None:
        self.wave_in_progress = False
        if self.is_stopped:
            return
        if self.pending:
            self.drain()

    def on_complete_error(self, e: Exception) -> None:
        self.wave_in_progress = False
        if self.is_stopped:
            return
        if isinstance(e, OutOfCreditsError):
            logger.info("Out of credits; dropping add-time generation queue")
            self.pending.clear()
            app_state.update_account_state()
            return
        if self.pending:
            self.drain()
