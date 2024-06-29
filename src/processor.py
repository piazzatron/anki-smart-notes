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
from typing import Any, Callable, List, Sequence, Tuple, Union

import aiohttp
from anki.notes import Note, NoteId
from aqt import editor, mw
from aqt.operations import QueryOp

from .config import Config
from .logger import logger
from .open_ai_client import OpenAIClient
from .prompts import interpolate_prompt
from .sentry import sentry
from .ui.ui_utils import show_message_box
from .utils import bump_usage_counter, check_for_api_key, run_on_main

# OPEN_AI rate limits
NEW_OPEN_AI_MODEL_REQ_PER_MIN = 500
OLD_OPEN_AI_MODEL_REQ_PER_MIN = 3500


class Processor:
    def __init__(self, client: OpenAIClient, config: Config):
        self.client = client
        self.config = config
        self.req_in_progress = False

    def process_single_field(
        self, note: Note, target_field_name: str, editor: editor.Editor
    ) -> None:

        bump_usage_counter()

        if not self._ensure_no_req_in_progress():
            return

        async def async_process_single_field(
            note: Note, target_field_name: str
        ) -> None:
            prompt = self.config.get_prompt(note.note_type()["name"], target_field_name)  # type: ignore[index]
            prompt = interpolate_prompt(prompt, note)
            if not prompt:
                return
            response = await self.client.async_get_chat_response(prompt)
            note[target_field_name] = response

        def on_success() -> None:
            # Only update note if it's already in the database
            self._reqlinquish_req_in_progress()
            if note.id and mw:
                mw.col.update_note(note)
            editor.loadNote()

        def on_failure(e: Exception) -> None:
            self._handle_failure(e)
            self._reqlinquish_req_in_progress()

        run_async_in_background(
            lambda: async_process_single_field(note, target_field_name),
            lambda _: on_success(),
            on_failure,
        )

    def process_notes_with_progress(
        self,
        note_ids: Sequence[NoteId],
        on_success: Union[Callable[[List[Note], List[Note]], None], None],
    ) -> None:
        """Processes notes in the background with a progress bar, batching into a single undo op"""

        if not mw:
            return

        bump_usage_counter()

        if not self._ensure_no_req_in_progress():
            return

        logger.debug("Processing notes...")

        if not check_for_api_key(self.config):
            return

        def wrapped_on_success(res: Tuple[List[Note], List[Note]]) -> None:
            updated, failed = res
            if not mw:
                return
            mw.col.update_notes(updated)
            self._reqlinquish_req_in_progress()
            if on_success:
                on_success(updated, failed)

        def on_failure(e: Exception) -> None:
            self._reqlinquish_req_in_progress()
            show_message_box(f"Error: {e}")

        model = self.config.openai_model
        limit = (
            OLD_OPEN_AI_MODEL_REQ_PER_MIN
            if model == "gpt-3.5-turbo"
            else NEW_OPEN_AI_MODEL_REQ_PER_MIN
        )
        is_large_batch = len(note_ids) >= limit
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
                        label=f"({processed_count}/{len(note_ids)})... waiting 60s for rate limit.",
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
                updated, failed, skipped = await self._process_notes_batch(batch)

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
                    logger.debug("Sleeping for 60s until next batch")
                    processed_count = 0
                    await asyncio.sleep(60)

            return total_updated, total_failed

        run_async_in_background(
            op, wrapped_on_success, on_failure, with_progress=(not is_large_batch)
        )

    async def _process_notes_batch(
        self, note_ids: Sequence[NoteId]
    ) -> Tuple[List[Note], List[Note], List[Note]]:
        """Returns updated, failed, skipped notes"""
        logger.debug(f"Processing {len(note_ids)} notes...")
        if not mw:
            logger.error("No mw!")
            return ([], [], [])

        notes = [mw.col.get_note(note_id) for note_id in note_ids]

        # Only process notes that have prompts
        to_process = []
        skipped = []
        for note in notes:
            note_type = note.note_type()
            if not note_type:
                # Should never happen
                raise Exception("Error: no note type")

            note_type_name = note_type["name"]
            if note_type_name not in self.config.prompts_map.get("note_types", {}):
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
            tasks.append(self._process_note(note))
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process errors
        notes_to_update = []
        failed = []
        for i, result in enumerate(results):
            note = to_process[i]
            if isinstance(result, Exception):
                logger.error(f"Error processing note {note_ids[i]}: {result}")
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
        target_fields: List[str] = [],
    ):
        """Process a single note, filling in fields with prompts from the user"""
        if not self._ensure_no_req_in_progress():
            return

        def wrapped_on_success(updated: bool) -> None:
            self._reqlinquish_req_in_progress()
            on_success(updated)

        def wrapped_failure(e: Exception) -> None:
            self._handle_failure(e)
            self._reqlinquish_req_in_progress()
            if on_failure:
                on_failure(e)

        # NOTE: for some reason i can't run bump_usage_counter in this hook without causing a
        # an PyQT crash, so I'm running it in the on_success callback instead
        run_async_in_background(
            lambda: self._process_note(
                note, overwrite_fields=overwrite_fields, target_fields=target_fields
            ),
            wrapped_on_success,
            wrapped_failure,
        )

    async def _process_note(
        self, note: Note, overwrite_fields: bool = False, target_fields: List[str] = []
    ) -> bool:
        """Process a single note, returns whether any fields were updated. Optionally can target specific fields. Caller responsible for handling any exceptions."""
        # logger.debug(f"Processing note")
        note_type = note.note_type()

        if not note_type:
            logger.error("no note type")
            return False

        note_type_name = note_type["name"]
        field_prompts = self.config.prompts_map.get("note_types", {}).get(
            note_type_name, None
        )

        if not field_prompts:
            logger.error("no prompts found for note type")
            return False

        tasks = []

        field_prompt_items = list(field_prompts["fields"].items())

        # If targetting specific fields, filter out the ones we don't want
        if target_fields:
            field_prompt_items = [
                item for item in field_prompt_items if item[0] in target_fields
            ]

        for field, prompt in field_prompt_items:
            # Don't overwrite fields that already exist
            if (not overwrite_fields) and note[field]:
                # logger.debug(f"Skipping already generated field: {field}")
                continue

            # logger.debug(f"Processing field: {field}, prompt: {prompt}")

            interpolated_prompt = interpolate_prompt(prompt, note)
            if not interpolated_prompt:
                # logger.debug(f"Skipping empty prompt for field: {field}")
                continue

            # Need to return both the chat response + the target field, since we're skiping
            # fields potentially here. Default arg to avoid stale closure
            async def get_response(
                field=field, interpolated_prompt=interpolated_prompt
            ) -> Tuple[str, str]:
                response = await self.client.async_get_chat_response(
                    interpolated_prompt
                )
                return (field, response)

            tasks.append(get_response())

        # Maybe filled out already, if so return early
        if not tasks:
            return False

        responses = await asyncio.gather(*tasks)
        # logger.debug(f"Responses {responses}")
        for target_field, response in responses:
            note[target_field] = response

        return True

    def _handle_failure(self, e: Exception) -> None:

        failure_map = {
            401: "Smart Notes Error: OpenAI returned 401, meaning there's an issue with your API key.",
            404: "Smart Notes Error: OpenAI returned 404 - did you pay for an API key? Paying for ChatGPT premium alone will not work (this is an OpenAI limitation).",
            429: "Smart Notes error: OpenAI rate limit exceeded. Ensure you have a paid API key (this plugin will not work with free API tier). Wait a few minutes and try again.",
        }

        if isinstance(e, aiohttp.ClientResponseError):
            if e.status in failure_map:
                show_message_box(failure_map[e.status])
            else:
                show_message_box(f"Smart Notes Error: Unknown error from OpenAI - {e}")

    def _ensure_no_req_in_progress(self) -> bool:
        if self.req_in_progress:
            logger.info("A request is already in progress.")
            return False

        self.req_in_progress = True
        return True

    def _reqlinquish_req_in_progress(self) -> None:
        self.req_in_progress = False

    def get_chat_response(
        self,
        prompt: str,
        on_success: Callable[[str], None],
        on_failure: Union[Callable[[Exception], None], None] = None,
    ):

        if not self._ensure_no_req_in_progress():
            return

        def wrapped_on_success(response: str) -> None:
            self._reqlinquish_req_in_progress()
            on_success(response)

        def wrapped_on_failure(e: Exception) -> None:
            self._handle_failure(e)
            self._reqlinquish_req_in_progress()
            if on_failure:
                on_failure(e)

        run_async_in_background(
            lambda: self.client.async_get_chat_response(prompt),
            wrapped_on_success,
            wrapped_on_failure,
        )


def run_async_in_background(
    op: Callable[[], Any],
    on_success: Callable[[Any], None],
    on_failure: Union[Callable[[Exception], None], None] = None,
    with_progress: bool = False,
):
    "Runs an async operation in the background and calls on_success when done."

    if not mw:
        raise Exception("Error: mw not found in run_async_in_background")

    # Wrap for sentry error reporting
    if sentry:
        op = sentry.wrap_async(op)
        on_success = sentry.wrap(on_success)
        if on_failure:
            on_failure = sentry.wrap(on_failure)

    query_op = QueryOp(
        parent=mw,
        op=lambda _: asyncio.run(op()),
        success=on_success,
    )

    if on_failure:
        query_op.failure(on_failure)

    if with_progress:
        query_op = query_op.with_progress()

    query_op.run_in_background()
