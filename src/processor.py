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
from typing import Callable, List, Sequence, Tuple, Union

import aiohttp
from anki.notes import Note, NoteId
from aqt import mw

from .app_state import (
    app_state,
    has_api_key,
    is_app_unlocked,
    is_app_unlocked_or_legacy,
)
from .config import Config
from .constants import CHAINED_FIELDS_SKIPPED_ERROR, STANDARD_BATCH_LIMIT
from .dag import generate_fields_dag
from .field_resolver import FieldResolver
from .logger import logger
from .models import ChatModels, ChatProviders
from .nodes import FieldNode
from .notes import get_note_type, get_note_types, has_chained_ai_fields
from .prompts import get_prompts
from .sentry import run_async_in_background_with_sentry
from .ui.ui_utils import show_message_box
from .utils import bump_usage_counter, run_on_main

# OPEN_AI rate limits
NEW_OPEN_AI_MODEL_REQ_PER_MIN = 500
OLD_OPEN_AI_MODEL_REQ_PER_MIN = 3500


class Processor:

    def __init__(self, field_resolver: FieldResolver, config: Config):
        self.field_resolver = field_resolver
        self.config = config
        self.req_in_progress = False

    def process_notes_with_progress(
        self,
        note_ids: Sequence[NoteId],
        on_success: Union[Callable[[List[Note], List[Note]], None], None],
        overwrite_fields: bool = False,
    ) -> None:
        """Processes notes in the background with a progress bar, batching into a single undo op"""

        if not mw:
            return

        bump_usage_counter()

        if not self._assert_preconditions():
            return

        logger.debug("Processing notes...")

        if not is_app_unlocked_or_legacy(show_box=False):
            return

        def wrapped_on_success(res: Tuple[List[Note], List[Note]]) -> None:
            updated, failed = res
            if not mw:
                return
            mw.col.update_notes(updated)
            self._reqlinquish_req_in_process()
            if on_success:
                on_success(updated, failed)

        def on_failure(e: Exception) -> None:
            self._reqlinquish_req_in_process()
            show_message_box(f"Error: {e}")

        if is_app_unlocked():
            limit = STANDARD_BATCH_LIMIT
        else:
            model = self.config.chat_model
            limit = (
                OLD_OPEN_AI_MODEL_REQ_PER_MIN
                if model == "gpt-4o-mini"
                else NEW_OPEN_AI_MODEL_REQ_PER_MIN
            )
        is_large_batch = len(note_ids) >= 3
        logger.debug(f"Rate limit: {limit}")

        # Only show fancy progress meter for large batches
        if is_large_batch:
            mw.progress.start(
                label=f"(0/{len(note_ids)})...",
                min=0,
                max=len(note_ids),
                immediate=True,
            )

        def on_update(
            updated: List[Note], processed_count: int, finished: bool
        ) -> None:
            if not mw:
                return

            mw.col.update_notes(updated)

            if is_large_batch:
                if not finished:
                    mw.progress.update(
                        label=f"({processed_count}/{len(note_ids)})",
                        value=processed_count,
                        max=len(note_ids),
                    )
                else:
                    mw.progress.finish()

        async def op():
            total_updated = []
            total_failed = []
            to_process_ids = note_ids[:]

            # Manually track processed count since sometimes we may
            # process a note without actually calling OpenAI
            processed_count = 0

            while len(to_process_ids) > 0:
                logger.debug("Processing batch...")
                batch = to_process_ids[:limit]
                to_process_ids = to_process_ids[limit:]
                updated, failed, skipped = await self._process_notes_batch(
                    batch, overwrite_fields=overwrite_fields
                )

                processed_count += len(updated) + len(failed)

                total_updated.extend(updated)
                total_updated.extend(skipped)
                total_failed.extend(failed)

                # Update the notes in the main thread
                run_on_main(
                    lambda: on_update(
                        updated,
                        len(total_updated) + len(total_failed),
                        len(to_process_ids) == 0,
                    )
                )

                if not to_process_ids:
                    break

                if (
                    processed_count >= limit - 5
                ):  # Make it a little fuzzy in case we've used some reqs already
                    processed_count = 0

            return total_updated, total_failed

        run_async_in_background_with_sentry(
            op, wrapped_on_success, on_failure, with_progress=(not is_large_batch)
        )

    async def _process_notes_batch(
        self, note_ids: Sequence[NoteId], overwrite_fields: bool
    ) -> Tuple[List[Note], List[Note], List[Note]]:
        """Returns updated, failed, skipped notes"""
        logger.debug(f"Processing {len(note_ids)} notes...")
        if not mw:
            logger.error("No mw!")
            return ([], [], [])

        notes = [mw.col.get_note(note_id) for note_id in note_ids]
        prompts = get_prompts()

        # Only process notes that have prompts
        to_process = []
        skipped = []
        for note in notes:

            note_type = get_note_type(note)
            if note_type not in prompts:
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
            tasks.append(self._process_note(note, overwrite_fields=overwrite_fields))
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process errors
        notes_to_update = []
        failed = []
        for i, result in enumerate(results):
            note = to_process[i]
            if isinstance(result, Exception):
                logger.debug(f"Error processing note {note_ids[i]}: {result}")
                failed.append(note)
            elif result:
                notes_to_update.append(note)
            else:
                skipped.append(note)

        logger.debug(
            f"Updated: {len(notes_to_update)}, Failed: {len(failed)}, Skipped: {len(skipped)}"
        )

        return (notes_to_update, failed, skipped)

    def process_note(
        self,
        note: Note,
        overwrite_fields: bool = False,
        on_success: Callable[[bool], None] = lambda _: None,
        on_failure: Union[Callable[[Exception], None], None] = None,
        target_field: Union[str, None] = None,
        on_field_update: Union[Callable[[], None], None] = None,
    ):
        """Process a single note, filling in fields with prompts from the user"""
        if not self._assert_preconditions():
            return

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
                target_field=target_field,
                on_field_update=on_field_update,
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
        overwrite_fields: bool = False,
        target_field: Union[str, None] = None,
        on_field_update: Union[Callable[[], None], None] = None,
    ) -> bool:
        """Process a single note, returns whether any fields were updated. Optionally can target specific fields. Caller responsible for handling any exceptions."""

        note_type = get_note_type(note)
        field_prompts = get_prompts().get(note_type, None)

        if not field_prompts:
            logger.debug("no prompts found for note type")
            return False

        # Topsort + parallel process the DAG
        dag = generate_fields_dag(
            note, target_field=target_field, overwrite_fields=overwrite_fields
        )

        did_update = False

        while len(dag):
            next_batch: List[FieldNode] = [
                node for node in dag.values() if not node.in_nodes
            ]
            logger.debug(f"Processing next nodes: {next_batch}")
            batch_tasks = {
                node.field: self._process_node(node, note) for node in next_batch
            }

            responses = await asyncio.gather(*batch_tasks.values())

            for field, response in zip(batch_tasks.keys(), responses):
                node = dag[field]
                if response:
                    logger.debug(f"Updating field {field} with response")
                    note[node.field_upper] = response

                if node.abort:
                    for out_node in node.out_nodes:
                        out_node.abort = True

                for out_node in node.out_nodes:
                    out_node.in_nodes.remove(node)

                if node.did_update:
                    did_update = True

                dag.pop(field)
                if on_field_update:
                    run_on_main(on_field_update)

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
            if is_app_unlocked():
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
                # Shouldn't get here
                logger.error(f"Got 4xx error but app is locked & no API key")
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
        """For now, checks that if the app is locked, there are no chained smart fields"""
        # This should be blocked before here, but JIC
        if is_app_unlocked():
            return True

        # Check for chained smart fields
        if has_api_key():
            all_note_types = get_note_types()
            has_chained_fields = any(
                has_chained_ai_fields(note_type) for note_type in all_note_types
            )
            logger.debug(f"Has chained fields: {has_chained_fields}")
            if has_chained_fields and not self.config.did_show_chained_error_dialog:
                show_message_box(CHAINED_FIELDS_SKIPPED_ERROR)
                self.config.did_show_chained_error_dialog = True
            return True

        return False

    def get_chat_response(
        self,
        prompt: str,
        note: Note,
        provider: ChatProviders,
        model: ChatModels,
        field_lower: str,
        on_success: Callable[[str], None],
        on_failure: Union[Callable[[Exception], None], None] = None,
    ):

        if not self._assert_preconditions():
            return

        def wrapped_on_success(response: str) -> None:
            self._reqlinquish_req_in_process()
            on_success(response)

        def wrapped_on_failure(e: Exception) -> None:
            self._handle_failure(e)
            self._reqlinquish_req_in_process()
            if on_failure:
                on_failure(e)

        # TODO: needs field_upper
        chat_fn = lambda: self.field_resolver.get_chat_response(
            prompt=prompt,
            note=note,
            model=model,
            provider=provider,
            field_lower=field_lower,
        )

        run_async_in_background_with_sentry(
            chat_fn,
            wrapped_on_success,
            wrapped_on_failure,
        )

    async def _process_node(self, node: FieldNode, note: Note) -> Union[str, None]:
        if node.abort:
            return None

        value = note[node.field_upper]

        # If not target and manual, skip
        if node.manual and not (node.is_target or node.generate_despite_manual):
            node.abort = True
            logger.debug(f"Skipping field {node.field}")
            return None

        # Skip it if there's a value and we don't want to overwrite
        if value and not (node.is_target or node.overwrite):
            return value

        new_value = await self.field_resolver.resolve(node, note)
        if new_value:
            node.did_update = True

        return new_value
