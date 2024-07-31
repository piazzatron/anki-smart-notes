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
from typing import Callable, Dict, List, Sequence, Tuple, Union

import aiohttp
from anki.notes import Note, NoteId
from aqt import mw

from .config import Config
from .field_resolver import FieldResolver
from .logger import logger
from .models import ChatModels, ChatProviders
from .nodes import ChatPayload, FieldNode, TTSPayload
from .notes import get_note_type
from .prompts import get_extras, get_prompt_fields, get_prompts
from .sentry import run_async_in_background_with_sentry
from .ui.ui_utils import show_message_box
from .utils import bump_usage_counter, check_for_api_key, get_fields, run_on_main

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
            if model == "gpt-4o-mini"
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
                    logger.debug("Sleeping for 60s until next batch")
                    processed_count = 0
                    await asyncio.sleep(60)

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
        target_field: Union[str, None] = None,
        on_field_update: Union[Callable[[], None], None] = None,
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
            logger.error("no prompts found for note type")
            return False

        # Topsort + parallel process the DAG
        dag = self.generate_fields_dag(
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
        failure_map = {
            401: "Smart Notes Error: OpenAI returned 401, meaning there's an issue with your API key.",
            404: "Smart Notes Error: OpenAI returned 404 - did you pay for an API key? Paying for ChatGPT premium alone will not work (this is an OpenAI limitation).",
            429: "Smart Notes error: OpenAI rate limit exceeded. Ensure you have a paid API key (this plugin will not work with free API tier). Wait a few minutes and try again.",
        }

        if isinstance(e, aiohttp.ClientResponseError):
            if e.status in failure_map:
                show_message_box(failure_map[e.status])
        else:
            logger.error(e)
            show_message_box(f"Smart Notes Error: Unknown error: {e}")

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
        note: Note,
        provider: ChatProviders,
        model: ChatModels,
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

        chat_fn = lambda: self.field_resolver.get_chat_response(
            prompt=prompt, note=note, model=model, provider=provider
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

    def generate_fields_dag(
        self, note: Note, overwrite_fields: bool, target_field: Union[str, None] = None
    ) -> Dict[str, FieldNode]:
        """Generates a directed acyclic graph of prompts for a note, or a subset of that graph if a target_fields list is passed. Returns a mapping of field -> PromptNode"""
        try:
            logger.debug("Generating dag...")
            note_type = get_note_type(note)
            prompts = get_prompts(to_lower=True).get(note_type, None)
            if not prompts:
                logger.error("generate_fields_dag: no prompts found for note type")
                return {}

            dag: Dict[str, FieldNode] = {}
            fields = get_fields(note_type)

            # Have to iterate over fields to get the canonical capitalization lol
            for field in fields:

                field_lower = field.lower()
                prompt = prompts.get(field_lower)
                if not prompt:
                    continue

                extras = get_extras(note_type, field)
                type = extras["type"]
                should_generate_automatically = extras["automatic"]

                payload: Union[ChatPayload, TTSPayload]
                if type == "chat":
                    payload = ChatPayload(
                        provider=extras["chat_provider"],
                        model=extras["chat_model"],
                        temperature=extras["chat_temperature"],
                        prompt=prompt,
                    )
                elif type == "tts":
                    payload = TTSPayload(
                        provider=extras["tts_provider"],
                        model=extras["tts_model"],
                        voice=extras["tts_voice"],
                        input=prompt,
                        options={},
                    )

                dag[field_lower] = FieldNode(
                    field=field_lower,
                    field_upper=field,
                    out_nodes=[],
                    in_nodes=[],
                    existing_value=note[field],
                    overwrite=overwrite_fields,
                    manual=not should_generate_automatically,
                    is_target=bool(
                        target_field and field_lower == target_field.lower()
                    ),
                    payload=payload,
                )

            if not len(dag):
                logger.debug("Unexpectedly empty dag!")
                return dag

            for field, prompt in prompts.items():
                in_fields = get_prompt_fields(prompt)

                for in_field in in_fields:
                    if in_field in dag:
                        this_node = dag[field]
                        depends_on = dag[in_field]
                        this_node.in_nodes.append(depends_on)
                        depends_on.out_nodes.append(this_node)

            # If there's a target field, trim
            # the dag to only the input of the target field
            if target_field:
                target_node = dag[target_field.lower()]
                trimmed: Dict[str, FieldNode] = {target_field.lower(): target_node}

                # Add pre
                explore = target_node.in_nodes.copy()
                while len(explore):
                    cur = explore.pop()
                    cur.generate_despite_manual = True
                    trimmed[cur.field] = cur
                    explore.extend(cur.in_nodes.copy())

                logger.debug("Generated target fields dag")
                logger.debug(trimmed)
                return trimmed

            logger.debug("Generated dag")
            logger.debug(dag)
            return dag
        except Exception as e:
            logger.error(f"Error creating dag: {e}")
            return {}

    def has_cycle(self, dag: Dict[str, FieldNode]) -> bool:
        """Tests for cycles in a DAG. Returns True if there are cycles, False if there are not."""
        dag = dag.copy()
        for start in dag.values():
            seen = set()
            explore = [start]
            while len(explore):
                cur = explore.pop()
                if cur.field in seen:
                    return True
                seen.add(cur.field)
                explore.extend(cur.out_nodes.copy())

        return False
