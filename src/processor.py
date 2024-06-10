import aiohttp
from aqt import editor
from typing import Sequence, Callable, Union

from anki.notes import Note, NoteId
from aqt import editor, mw
from aqt.operations import CollectionOp
from anki.collection import OpChanges

from .ui.ui_utils import show_message_box
from .prompts import interpolate_prompt
from .utils import bump_usage_counter, run_async_in_background, check_for_api_key
from .open_ai_client import OpenAIClient
from .config import Config

import asyncio


class Processor:
    def __init__(self, client: OpenAIClient, config: Config):
        self.client = client
        self.config = config
        self.req_in_progress = False

    def ensure_no_req_in_progress(self) -> bool:
        if self.req_in_progress:
            show_message_box(
                "A request is already in progress. Please wait for the prior request to finish before creating a new one."
            )
            return False

        self.req_in_progress = True
        return True

    def _reqlinquish_req_in_progress(self) -> None:
        self.req_in_progress = False

    def process_single_field(
        self, note: Note, target_field_name: str, editor: editor.Editor
    ) -> None:

        bump_usage_counter()

        if not self.ensure_no_req_in_progress():
            return

        async def async_process_single_field(
            note: Note, target_field_name: str
        ) -> None:
            print("IN PROCESS SINGLE FIELD")
            prompt = self.config.get_prompt(note.note_type()["name"], target_field_name)  # type: ignore[index]
            prompt = interpolate_prompt(prompt, note)
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
        self, note_ids: Sequence[NoteId], on_success: Union[Callable[[], None], None]
    ) -> None:
        """Processes notes in the background with a progress bar, batching into a single undo op"""

        bump_usage_counter()

        if not self.ensure_no_req_in_progress():
            return

        async def process_notes(notes: Sequence[Note]):
            tasks = []
            for note in notes:
                tasks.append(self._process_note(note))
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return results

        print("Processing notes...")

        if not check_for_api_key(self.config):
            return

        if not mw:
            return

        def wrapped_process_notes() -> OpChanges:
            notes = [mw.col.get_note(note_id) for note_id in note_ids]

            changes = OpChanges()

            # Sanity check that we actually have prompts for these note types
            has_prompts = True
            for note in notes:
                note_type = note.note_type()
                if not note_type:
                    print("Error: no note type")
                    return OpChanges()
                note_type_name = note_type["name"]
                if note_type_name not in self.config.prompts_map.get("note_types", {}):
                    print("Error: no prompts found for note type")
                    has_prompts = False

            if not has_prompts:
                raise Exception("Not all selected note types have smart fields.")

            asyncio.run(process_notes(notes))
            changes.note = True
            mw.col.update_notes(notes)
            return changes

        def wrapped_on_success(_: OpChanges) -> None:
            self._reqlinquish_req_in_progress()
            if on_success:
                on_success()

        def on_failure(e: Exception) -> None:
            self._reqlinquish_req_in_progress()
            show_message_box(f"Error: {e}")

        op = CollectionOp(
            parent=mw,
            op=lambda _: wrapped_process_notes(),
        )

        op.success(wrapped_on_success)
        op.failure(on_failure)
        op.run_in_background()

    # TODO: do I even need this method or can I just use the batch one?
    def process_note(
        self,
        note: Note,
        overwrite_fields: bool = False,
        on_success: Callable[[bool], None] = lambda _: None,
        on_failure: Union[Callable[[Exception], None], None] = None,
    ):
        """Process a single note, filling in fields with prompts from the user"""
        if not self.ensure_no_req_in_progress():
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
            lambda: self._process_note(note, overwrite_fields=overwrite_fields),
            wrapped_on_success,
            wrapped_failure,
        )

    async def _process_note(self, note: Note, overwrite_fields=False) -> bool:
        """Process a single note, returns whether any fields were updated. Caller responsible for handling any exceptions."""
        print(f"Processing note")
        note_type = note.note_type()

        if not note_type:
            print("Error: no note type")
            return False

        note_type_name = note_type["name"]
        field_prompts = self.config.prompts_map.get("note_types", {}).get(
            note_type_name, None
        )

        if not field_prompts:
            print("Error: no prompts found for note type")
            return False

        tasks = []

        field_prompt_items = list(field_prompts["fields"].items())
        for field, prompt in field_prompt_items:
            # Don't overwrite fields that already exist
            if (not overwrite_fields) and note[field]:
                print(f"Skipping field: {field}")
                continue

            print(f"Processing field: {field}, prompt: {prompt}")

            prompt = interpolate_prompt(prompt, note)

            task = self.client.async_get_chat_response(prompt)
            tasks.append(task)

        # Maybe filled out already, if so return early
        if not tasks:
            return False

        responses = await asyncio.gather(*tasks)
        print("Responses: ", responses)
        for i, response in enumerate(responses):
            target_field = field_prompt_items[i][0]
            note[target_field] = response

        return True

    def _handle_failure(self, e: Exception) -> None:
        if isinstance(e, aiohttp.ClientResponseError):
            if e.status == 401:
                show_message_box(
                    "Smart Notes Error: OpenAI returned 401, meaning there's an issue with your API key."
                )
            elif e.status == 429:
                show_message_box(
                    "Smart Notes error: OpenAI rate limit exceeded. Wait a few minutes and try again."
                )
            else:
                show_message_box(f"Smart Notes Error: Unknown error from OpenAI - {e}")

    def get_chat_response(self, prompt: str, on_success: Callable[[str], None]):

        run_async_in_background(
            lambda: self.client.async_get_chat_response(prompt), on_success
        )
