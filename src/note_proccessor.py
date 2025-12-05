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
from collections.abc import Callable, Sequence
from typing import Optional

import aiohttp
from anki.cards import Card, CardId
from anki.decks import DeckId
from anki.notes import Note, NoteId
from aqt import mw

from .app_state import (
    app_state,
    has_api_key,
    is_capacity_remaining,
    is_capacity_remaining_or_legacy,
)
from .config import Config, bump_usage_counter
from .constants import GENERIC_CREDITS_MESSAGE, STANDARD_BATCH_LIMIT
from .dag import generate_fields_dag
from .field_processor import FieldProcessor
from .logger import logger
from .nodes import FieldNode
from .notes import get_note_type
from .prompts import get_prompts_for_note
from .sentry import run_async_in_background_with_sentry
from .ui.ui_utils import show_message_box
from .utils import run_on_main

# OPEN_AI rate limits
NEW_OPEN_AI_MODEL_REQ_PER_MIN = 500
OLD_OPEN_AI_MODEL_REQ_PER_MIN = 3500


class NoteProcessor:
    def __init__(self, field_processor: FieldProcessor, config: Config):
        self.field_processor = field_processor
        self.config = config
        self.req_in_progress = False

    def process_cards_with_progress(
        self,
        card_ids: Sequence[CardId],
        on_success: Optional[Callable[[list[Note], list[Note], list[Note]], None]],
        overwrite_fields: bool = False,
    ) -> None:
        """Processes notes in the background with a progress bar, batching into a single undo op"""

        if not mw or not mw.col:
            return

        bump_usage_counter()
        cards = [mw.col.get_card(card_in) for card_in in card_ids]

        # If a card appears multiple times in the same deck, process it just a single time
        cards = list({card.nid: card for card in cards}.values())

        note_ids = [card.nid for card in cards]
        did_map = {card.nid: card.did for card in cards}

        if not self._assert_preconditions():
            return

        logger.debug("Processing notes...")

        if not is_capacity_remaining_or_legacy(show_box=False):
            return

        def wrapped_on_success(res: tuple[list[Note], list[Note], list[Note]]) -> None:
            updated, failed, skipped = res
            if not mw or not mw.col:
                return
            mw.col.update_notes(updated)
            self._reqlinquish_req_in_process()
            if on_success:
                on_success(updated, failed, skipped)

        def on_failure(e: Exception) -> None:
            self._reqlinquish_req_in_process()
            show_message_box(f"Error: {e}")

        # TODO: this logic should be re-addressed when I revisit batch limits (ANK-28)
        if is_capacity_remaining():
            limit = STANDARD_BATCH_LIMIT
        else:
            model = self.config.chat_model
            limit = (
                OLD_OPEN_AI_MODEL_REQ_PER_MIN
                if model == "gpt-4o-mini"
                else NEW_OPEN_AI_MODEL_REQ_PER_MIN
            )
        logger.debug(f"Rate limit: {limit}")

        # Only show fancy progress meter for large batches
        mw.progress.start(
            label=f"✨Generating... (0/{len(note_ids)})",
            min=0,
            max=0,
            immediate=True,
        )

        def on_update(
            updated: list[Note], processed_count: int, finished: bool
        ) -> None:
            if not mw or not mw.col:
                return

            mw.col.update_notes(updated)

            if not finished:
                mw.progress.update(
                    label=f"✨ Generating... ({processed_count}/{len(note_ids)})",
                    value=processed_count,
                    max=len(note_ids),
                )
            else:
                logger.info("Finished processing all notes")
                mw.progress.finish()

        async def op():
            total_updated = []
            total_failed = []
            total_skipped = []
            to_process_ids = note_ids[:]

            # Manually track processed count since sometimes we may
            # process a note without actually calling OpenAI
            processed_count = 0

            while len(to_process_ids) > 0:
                logger.debug("Processing batch...")
                batch = to_process_ids[:limit]
                to_process_ids = to_process_ids[limit:]
                updated, failed, skipped = await self._process_notes_batch(
                    batch, overwrite_fields=overwrite_fields, did_map=did_map
                )

                processed_count += len(batch)

                total_updated.extend(updated)
                total_failed.extend(failed)
                total_skipped.extend(skipped)

                # Update the notes in the main thread
                run_on_main(
                    lambda updated=updated,
                    to_process_ids_empty=len(to_process_ids) == 0,
                    processed_count=processed_count: on_update(
                        updated,
                        processed_count,
                        to_process_ids_empty,
                    )
                )

                if not to_process_ids:
                    break

            return total_updated, total_failed, total_skipped

        run_async_in_background_with_sentry(
            op, wrapped_on_success, on_failure, with_progress=True
        )

    async def _process_notes_batch(
        self,
        note_ids: Sequence[NoteId],
        overwrite_fields: bool,
        did_map: dict[NoteId, DeckId],
    ) -> tuple[list[Note], list[Note], list[Note]]:
        """Returns updated, failed, skipped notes"""
        logger.debug(f"Processing {len(note_ids)} notes...")
        if not mw or not mw.col:
            logger.error("No mw!")
            return ([], [], [])

        notes = [mw.col.get_note(note_id) for note_id in note_ids]

        # Only process notes that have prompts
        to_process: list[Note] = []
        skipped: list[Note] = []
        for note in notes:
            note_type = get_note_type(note)
            prompts = get_prompts_for_note(note_type, did_map[note.id])
            if not prompts:
                logger.debug("Error: no prompts found for note type")
                skipped.append(note)
            else:
                to_process.append(note)
        if not to_process:
            logger.debug("No notes to process")
            return ([], [], [])

        # Run them all in parallel
        tasks = []
        for note in to_process:
            tasks.append(
                self._process_note(
                    note, overwrite_fields=overwrite_fields, deck_id=did_map[note.id]
                )
            )
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process errors
        notes_to_update = []
        failed = []
        for i, result in enumerate(results):
            note = to_process[i]
            if isinstance(result, Exception):
                logger.error(
                    f"Error processing note {note_ids[i]}: {result}, {''.join(traceback.format_exception(type(result), result, result.__traceback__))}"
                )
                failed.append(note)
            elif result:
                notes_to_update.append(note)
            else:
                skipped.append(note)

        logger.debug(
            f"Updated: {len(notes_to_update)}, Failed: {len(failed)}, Skipped: {len(skipped)}"
        )

        return (notes_to_update, failed, skipped)

    def process_card(
        self,
        card: Card,
        show_progress: bool,
        overwrite_fields: bool = False,
        on_success: Callable[[bool], None] = lambda _: None,
        on_failure: Optional[Callable[[Exception], None]] = None,
        target_field: Optional[str] = None,
        on_field_update: Optional[Callable[[], None]] = None,
    ):
        """Process a single note, filling in fields with prompts from the user"""
        if not self._assert_preconditions():
            return

        note = card.note()

        def wrapped_on_success(updated: bool) -> None:
            self._reqlinquish_req_in_process()
            on_success(updated)

        def wrapped_failure(e: Exception) -> None:
            self._handle_failure(e)
            self._reqlinquish_req_in_process()
            if on_failure:
                on_failure(e)

        # NOTE: for some reason i can't run bump_usage_counter in this hook without causing a
        # an PyQT crash, so I'm running it in the on_success callback instead
        run_async_in_background_with_sentry(
            lambda: self._process_note(
                note,
                overwrite_fields=overwrite_fields,
                deck_id=card.did,
                target_field=target_field,
                on_field_update=on_field_update,
                show_progress=show_progress,
            ),
            wrapped_on_success,
            wrapped_failure,
        )

    # Note: one quirk is that if overwrite_fields = True AND there's a target field,
    # it will regenerate any fields up until the target field. A bit weird but
    # this combination of values doesn't really make sense anyways so it's probably fine.
    # Would be better modeled with some mode switch or something.
    async def _process_note(
        self,
        note: Note,
        deck_id: DeckId,
        overwrite_fields: bool = False,
        target_field: Optional[str] = None,
        on_field_update: Optional[Callable[[], None]] = None,
        show_progress: bool = False,
    ) -> bool:
        """Process a single note, returns whether any fields were updated. Optionally can target specific fields. Caller responsible for handling any exceptions."""

        note_type = get_note_type(note)
        prompts_for_note = get_prompts_for_note(note_type, deck_id)

        if not prompts_for_note:
            logger.debug("no prompts found for note type")
            return False

        # Topsort + parallel process the DAG
        dag = generate_fields_dag(
            note,
            target_field=target_field,
            overwrite_fields=overwrite_fields,
            deck_id=deck_id,
        )

        did_update = False

        will_show_progress = show_progress and len(dag)
        if will_show_progress:
            run_on_main(
                lambda: mw.progress.start(  # type: ignore
                    label="✨ Generating...",
                    min=0,
                    max=len(dag),
                    immediate=True,
                )
            )

        try:
            while len(dag):
                next_batch: list[FieldNode] = [
                    node for node in dag.values() if not node.in_nodes
                ]
                logger.debug(f"Processing next nodes: {next_batch}")
                batch_tasks = {
                    node.field: self._process_node(
                        # Only show the error box for the target field
                        node,
                        note,
                        show_error_message_box=node.is_target,
                    )
                    for node in next_batch
                }

                responses = await asyncio.gather(*batch_tasks.values())

                for field, response in zip(batch_tasks.keys(), responses):
                    node = dag[field]
                    if response:
                        logger.debug(
                            f"Updating field {field} with response: {response}"
                        )
                        note[node.field_upper] = response

                    if node.abort:
                        for out_node in node.out_nodes:
                            out_node.abort = True

                    for out_node in node.out_nodes:
                        out_node.in_nodes.remove(node)

                    # New notes have ID 0 and don't exist in the DB yet, so can't be updated!
                    if note.id and node.did_update:
                        if mw and mw.col:
                            mw.col.update_note(note)
                        did_update = True

                    dag.pop(field)
                    if on_field_update:
                        run_on_main(on_field_update)

        finally:
            if will_show_progress:
                run_on_main(lambda: mw.progress.finish())  # type: ignore

        return did_update

    def _handle_failure(self, e: Exception) -> None:
        logger.debug("Handling failure")

        openai_failure_map = {
            401: "Smart Notes Error: OpenAI returned 401, meaning there's an issue with your API key.",
            404: "Smart Notes Error: OpenAI returned 404 - did you pay for an API key? Paying for ChatGPT premium alone will not work (this is an OpenAI limitation).",
            429: "Smart Notes error: OpenAI rate limit exceeded. Ensure you have a paid API key (this plugin will not work with free API tier). Wait a few minutes and try again.",
        }

        if isinstance(e, aiohttp.ClientResponseError):
            status = e.status
            logger.debug(f"Got status: {status}")
            unknown_error = f"Smart Notes Error: Unknown error: {e}"

            # First time we see a 4xx error, update subscription state
            if is_capacity_remaining():
                logger.debug(f"Got API error: {e}")
                if status >= 400 and status < 500:
                    logger.debug(
                        "Saw 4xx error, something wrong with some subscription"
                    )
                    app_state.update_subscription_state()
                    return
                else:
                    logger.error(f"Got 500 error: {e}")
                    show_message_box(unknown_error)
            elif has_api_key():
                if status in openai_failure_map:
                    show_message_box(openai_failure_map[status])
                else:
                    show_message_box(unknown_error)
            else:
                if status == 402:
                    # Shouldn't get here; requests should be blocked if you're
                    # out of credits.
                    logger.debug("Got 402 error but app is locked & no API key")
                    show_message_box(GENERIC_CREDITS_MESSAGE)
                else:
                    logger.error("Got 4xx error but app is locked & no API key")
                    show_message_box(unknown_error)
        else:
            logger.error(f"Got non-HTTP error: {e}")
            show_message_box(f"Smart Notes Error: Unknown error: {e}")

    def _assert_preconditions(self) -> bool:
        valid_app_mode = self._assert_valid_app_mode()
        if not valid_app_mode:
            logger.error("Invalid app mode")
            return False
        no_existing_req = self.assert_no_req_in_process()
        return no_existing_req

    def assert_no_req_in_process(self) -> bool:
        if self.req_in_progress:
            logger.info("A request is already in progress.")
            return False

        self.req_in_progress = True
        return True

    def _reqlinquish_req_in_process(self) -> None:
        self.req_in_progress = False

    def _assert_valid_app_mode(self) -> bool:
        return is_capacity_remaining() or has_api_key()

    async def _process_node(
        self, node: FieldNode, note: Note, show_error_message_box: bool
    ) -> Optional[str]:
        if node.abort:
            logger.debug(f"Skipping field {node.field}")
            return None

        logger.debug(f"Processing field {node.field}")

        value = note[node.field_upper]

        # If not target and manual, skip
        if node.manual and not (node.is_target or node.generate_despite_manual):
            node.abort = True
            logger.debug(f"Skipping field {node.field}")
            return None

        # Skip it if there's a value and we don't want to overwrite
        if value and not (node.is_target or node.overwrite):
            return value

        new_value = await self.field_processor.resolve(
            node, note, show_error_message_box
        )
        if new_value:
            node.did_update = True

        return new_value
