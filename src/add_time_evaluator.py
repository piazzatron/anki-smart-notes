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

import traceback
from typing import Any, Optional

from anki.cards import Card
from anki.notes import Note
from aqt import mw

from .api_client import OutOfCreditsError, UserDisplayableError
from .app_state import app_state, is_capacity_remaining_or_legacy
from .config import config
from .logger import logger
from .note_proccessor import NoteProcessor
from .sentry import run_async_in_background_with_sentry
from .utils import run_on_main
from .utils.notes_utils import is_card_fully_processed

# note_will_be_added fires before the add assigns the note id, so wait for the add
# to finish before looking the note up.
START_DELAY_MS = 1000

# Maximum number of added notes generating at once. Notes added while this many
# are generating are skipped and left for review-time or browser batch
# generation, so a bulk add from a script or another add-on can't launch
# hundreds of requests.
MAX_IN_FLIGHT = 10


class AddTimeEvaluator:
    """Generates automatic Smart Fields for notes shortly after they are added.

    The main use case is notes created outside the Add dialog, such as through
    AnkiConnect by Yomitan. Each added note generates in its own background
    operation, up to MAX_IN_FLIGHT at once.
    """

    def __init__(self, processor: NoteProcessor) -> None:
        self.processor = processor
        self.in_flight = 0
        self.is_stopped = False

    def stop(self) -> None:
        self.is_stopped = True
        self.in_flight = 0

    def on_note_will_be_added(self, note: Note) -> None:
        # Can run off the main thread: the Add dialog adds in a background op.
        if self.is_stopped or not config.generate_on_add:
            return
        run_on_main(lambda: self.schedule_start(note))

    def schedule_start(self, note: Note) -> None:
        if self.is_stopped or not mw:
            return
        mw.progress.single_shot(START_DELAY_MS, lambda: self.start(note))

    def start(self, added_note: Note) -> None:
        if self.is_stopped or not mw or not mw.col:
            return

        if not is_capacity_remaining_or_legacy():
            return

        if self.in_flight >= MAX_IN_FLIGHT:
            logger.debug(
                f"Skipping add-time generation for note {added_note.id}: {MAX_IN_FLIGHT} notes already generating"
            )
            return

        card = self.get_candidate_card(added_note)
        if not card:
            return

        self.in_flight += 1
        run_async_in_background_with_sentry(
            lambda: self.run_card_task(card),
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
            # Deleted again before generation started.
            return None

        # Prompts are scoped by deck, so use a real card's deck rather than the
        # requested one: a deck override on the card template can move it.
        cards = note.cards()
        if not cards:
            return None

        card = cards[0]
        return None if is_card_fully_processed(card) else card

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
        if self.is_stopped:
            return
        self.in_flight -= 1

    def on_complete_error(self, e: Exception) -> None:
        if self.is_stopped:
            return
        self.in_flight -= 1
        if isinstance(e, OutOfCreditsError):
            app_state.update_account_state()
