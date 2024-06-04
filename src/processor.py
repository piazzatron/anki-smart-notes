from aqt import editor
from typing import Sequence, Callable, Union

from anki.notes import Note, NoteId
from aqt import editor, mw
from aqt.operations import CollectionOp
from anki.collection import OpChanges
from .prompts import interpolate_prompt
from .utils import run_async_in_background, check_for_api_key
from .open_ai_client import OpenAIClient
from .config import Config

import asyncio


class Processor:
    def __init__(self, client: OpenAIClient, config: Config):
        self.client = client
        self.config = config

    def process_single_field(
        self, note: Note, target_field_name: str, editor: editor.Editor
    ) -> None:

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
            if note.id and mw:
                mw.col.update_note(note)
            editor.loadNote()

        run_async_in_background(
            lambda: async_process_single_field(note, target_field_name),
            lambda _: on_success(),
        )

    def process_notes_with_progress(self, note_ids: Sequence[NoteId]) -> None:
        """Processes notes in the background with a progress bar, batching into a single undo op"""

        async def process_notes(notes: Sequence[Note]):
            tasks = []
            for note in notes:
                tasks.append(self._process_note(note))
            await asyncio.gather(*tasks)

        print("Processing notes...")

        if not check_for_api_key(self.config):
            return

        if not mw:
            return

        def wrapped_process_notes() -> OpChanges:
            notes = [mw.col.get_note(note_id) for note_id in note_ids]
            asyncio.run(process_notes(notes))
            changes = OpChanges()
            changes.note = True
            mw.col.update_notes(notes)
            return changes

        op = CollectionOp(
            parent=mw,
            op=lambda _: wrapped_process_notes(),
        )

        op.run_in_background()

    # TODO: do I even need this method or can I just use the batch one?
    def process_note(
        self,
        note: Note,
        overwrite_fields: bool = False,
        on_success: Callable[[], None] = lambda: None,
    ):
        """Process a single note, filling in fields with prompts from the user"""
        run_async_in_background(
            lambda: self._process_note(note, overwrite_fields=overwrite_fields),
            lambda _: on_success(),
        )

    async def _process_note(self, note: Note, overwrite_fields=False):
        print(f"Processing note")
        note_type = note.note_type()

        if not note_type:
            print("Error: no note type")
            return

        note_type_name = note_type["name"]
        field_prompts = self.config.prompts_map.get("note_types", {}).get(
            note_type_name, None
        )

        if not field_prompts:
            print("Error: no prompts found for note type")
            return

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
            return

        # TODO: handle exceptions here
        responses = await asyncio.gather(*tasks)
        print("Responses: ", responses)
        for i, response in enumerate(responses):
            target_field = field_prompt_items[i][0]
            note[target_field] = response

    def get_chat_response(self, prompt: str, on_success: Callable[[str], None]):

        run_async_in_background(
            lambda: self.client.async_get_chat_response(prompt), on_success
        )
