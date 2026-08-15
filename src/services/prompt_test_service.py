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

import base64
import secrets
from dataclasses import dataclass
from typing import Literal, Optional, Union

from anki.cards import CardId
from anki.decks import DeckId
from anki.errors import NotFoundError
from anki.notes import Note
from aqt import mw
from aqt.operations.note import update_note

from ..app_state import is_capacity_remaining
from ..chat_provider import chat_provider
from ..field_resolver import field_resolver
from ..image_provider import image_provider
from ..markdown import convert_markdown_to_html
from ..media_utils import ext_from_content_type, get_media_path, write_media
from ..models.smart_fields import (
    ImagePromptTestRequest,
    SaveTestResultRequest,
    TextPromptTestRequest,
    TTSPromptTestRequest,
)
from ..prompt_fields import get_prompt_fields
from ..tts_provider import tts_provider

EXPIRED_TEST_RESULT_MESSAGE = "This result has expired — run the test again"


@dataclass(frozen=True)
class TextPromptTestContext:
    """Card data captured on Anki's main thread for an async prompt test.

    Both are None for a test run with no card picked, which the prompt is
    checked for beforehand."""

    note: Optional[Note]
    deck_id: Optional[DeckId]
    request: TextPromptTestRequest


@dataclass(frozen=True)
class ImagePromptTestContext:
    """Card data captured on Anki's main thread for an async image test.

    None for a test run with no card picked."""

    note: Optional[Note]
    request: ImagePromptTestRequest


@dataclass(frozen=True)
class TTSPromptTestContext:
    """Card data captured on Anki's main thread for an async voice test."""

    note: Optional[Note]
    request: TTSPromptTestRequest


@dataclass(frozen=True)
class TextTestArtifact:
    """A text test result, kept only so the user can save it to the card."""

    token: str
    card_id: CardId
    text: str


@dataclass(frozen=True)
class MediaTestArtifact:
    """An image or audio test result, kept only so it can be saved to the card."""

    token: str
    card_id: CardId
    kind: Literal["image", "audio"]
    data: bytes
    content_type: str


TestArtifact = Union[TextTestArtifact, MediaTestArtifact]

# One slot, deliberately: only the newest test result is savable. Every test
# overwrites it, and the web UI's result token is what proves a save request
# refers to the artifact still sitting here.
_last_test_artifact: Optional[TestArtifact] = None


def prepare_text_prompt_test(request: TextPromptTestRequest) -> TextPromptTestContext:
    """Refetch the requested card so tests never trust client-supplied note data.

    Checked before the collection is touched, since a cardless test never reads it."""
    if request.card_id is None:
        _reject_field_references_without_card(request.prompt)
        return TextPromptTestContext(note=None, deck_id=None, request=request)

    if not mw or not mw.col:
        raise ValueError("Anki collection is not available")

    try:
        card = mw.col.get_card(request.card_id)
    except NotFoundError as error:
        raise ValueError("The selected card no longer exists") from error

    return TextPromptTestContext(
        note=card.note(),
        deck_id=card.did,
        request=request,
    )


def prepare_image_prompt_test(
    request: ImagePromptTestRequest,
) -> ImagePromptTestContext:
    if request.card_id is None:
        _reject_field_references_without_card(request.prompt)
        return ImagePromptTestContext(note=None, request=request)

    return ImagePromptTestContext(
        note=_get_selected_card_note(request.card_id), request=request
    )


def prepare_tts_prompt_test(request: TTSPromptTestRequest) -> TTSPromptTestContext:
    if request.card_id is None:
        _reject_field_references_without_card(request.text)
        return TTSPromptTestContext(note=None, request=request)

    return TTSPromptTestContext(
        note=_get_selected_card_note(request.card_id), request=request
    )


def _reject_field_references_without_card(prompt: str) -> None:
    """A prompt that reads fields needs a card to read them from."""
    if get_prompt_fields(prompt):
        raise ValueError("Select a card to use field references in this test")


async def run_text_prompt_test(context: TextPromptTestContext) -> dict[str, str]:
    """Generate a text preview without writing anything back to the card."""
    if not is_capacity_remaining():
        raise ValueError("Generation is unavailable for this account")
    settings = context.request.settings
    if context.note is None or context.deck_id is None:
        # No card to read fields from, so nothing to interpolate — ask the provider
        # for the prompt as written.
        text = await chat_provider.async_get_chat_response(
            context.request.prompt,
            model=settings.model,
            provider=settings.provider,
            note_id=None,
            web_search=settings.web_search_enabled,
            reasoning_level=settings.reasoning_level,
            generation_source="prompt_test",
        )
    else:
        text = await field_resolver.get_chat_response(
            note=context.note,
            deck_id=context.deck_id,
            prompt=context.request.prompt,
            model=settings.model,
            provider=settings.provider,
            field_lower="smart-notes-test",
            should_convert_to_html=False,
            should_embed_images=False,
            web_search=settings.web_search_enabled,
            reasoning_level=settings.reasoning_level,
            show_error_box=False,
            generation_source="prompt_test",
        )
    if not text:
        raise ValueError("No response received")

    # A cardless run has no card to write back to, so it mints no savable artifact.
    result = {"text": text}
    if context.request.card_id is None:
        return result

    token = _remember_test_artifact(
        TextTestArtifact(
            token=_new_result_token(),
            card_id=context.request.card_id,
            text=text,
        )
    )
    return {**result, "resultToken": token}


async def run_image_prompt_test(context: ImagePromptTestContext) -> dict[str, str]:
    """Generate an image preview without adding media or changing the card."""
    if not is_capacity_remaining():
        raise ValueError("Generation is unavailable for this account")
    settings = context.request.settings
    if context.note is None:
        # No card to read fields from, so nothing to interpolate — ask the provider
        # for the prompt as written.
        response = await image_provider.async_get_image_response(
            prompt=context.request.prompt,
            model=settings.model,
            provider=settings.provider,
            note_id=None,
            generation_source="prompt_test",
        )
    else:
        response = await field_resolver.get_image_response(
            note=context.note,
            input_text=context.request.prompt,
            model=settings.model,
            provider=settings.provider,
            show_error_box=False,
            generation_source="prompt_test",
        )
    if not response:
        raise ValueError("No response received")

    # A cardless run has no card to write back to, so it mints no savable artifact.
    result = {"dataUrl": _data_url(response["data"], response["content_type"])}
    if context.request.card_id is None:
        return result

    token = _remember_test_artifact(
        MediaTestArtifact(
            token=_new_result_token(),
            card_id=context.request.card_id,
            kind="image",
            data=response["data"],
            content_type=response["content_type"],
        )
    )
    return {**result, "resultToken": token}


async def run_tts_prompt_test(context: TTSPromptTestContext) -> dict[str, str]:
    """Generate an audio preview without adding media or changing the card."""
    if not is_capacity_remaining():
        raise ValueError("Generation is unavailable for this account")
    settings = context.request.settings
    if context.note is None:
        audio = await tts_provider.async_get_tts_response(
            input=context.request.text,
            model=settings.model,
            provider=settings.provider,
            voice=settings.voice_id,
            generation_source="prompt_test",
        )
    else:
        audio = await field_resolver.get_tts_response(
            note=context.note,
            input_text=context.request.text,
            model=settings.model,
            provider=settings.provider,
            voice=settings.voice_id,
            show_error_box=False,
            generation_source="prompt_test",
        )
    if not audio:
        raise ValueError("No response received")

    content_type = _tts_content_type(settings.provider)
    result = {"dataUrl": _data_url(audio, content_type)}
    if context.request.card_id is None:
        return result

    token = _remember_test_artifact(
        MediaTestArtifact(
            token=_new_result_token(),
            card_id=context.request.card_id,
            kind="audio",
            data=audio,
            content_type=content_type,
        )
    )
    return {**result, "resultToken": token}


def save_test_result(request: SaveTestResultRequest) -> None:
    """Write the newest test result into a note field. Main thread only."""
    if not mw or not mw.col:
        raise ValueError("Anki collection is not available")

    artifact = _last_test_artifact
    if (
        artifact is None
        or not secrets.compare_digest(artifact.token, request.token)
        or artifact.card_id != request.card_id
    ):
        raise ValueError(EXPIRED_TEST_RESULT_MESSAGE)

    # Refetch by id so the write never trusts the client's copy of the note.
    note = _get_selected_card_note(request.card_id)
    if request.field_name not in note:
        raise ValueError(f"This note has no field named {request.field_name}")

    note[request.field_name] = _render_artifact(artifact, note, request.field_name)

    # CollectionOp gives the write an undo entry and refreshes every open Anki
    # window, which the local server has no handle on otherwise.
    update_note(parent=mw, note=note).run_in_background()


def _render_artifact(artifact: TestArtifact, note: Note, field_name: str) -> str:
    """Turn a test artifact into exactly what real generation would have written."""
    if isinstance(artifact, TextTestArtifact):
        # Tests render raw model output; generation writes converted HTML.
        return convert_markdown_to_html(artifact.text)

    extension = (
        ext_from_content_type(artifact.content_type)
        if artifact.kind == "image"
        else ("wav" if artifact.content_type == "audio/wav" else "mp3")
    )
    path = write_media(get_media_path(note, field_name, extension), artifact.data)
    if not path:
        raise ValueError("Could not write the media file")

    return f'<img src="{path}"/>' if artifact.kind == "image" else f"[sound:{path}]"


def _remember_test_artifact(artifact: TestArtifact) -> str:
    global _last_test_artifact
    _last_test_artifact = artifact
    return artifact.token


def _new_result_token() -> str:
    return secrets.token_urlsafe(16)


def _get_selected_card_note(card_id: CardId) -> Note:
    if not mw or not mw.col:
        raise ValueError("Anki collection is not available")
    try:
        return mw.col.get_card(card_id).note()
    except NotFoundError as error:
        raise ValueError("The selected card no longer exists") from error


def _data_url(data: bytes, content_type: str) -> str:
    return f"data:{content_type};base64,{base64.b64encode(data).decode('ascii')}"


def _tts_content_type(provider: str) -> str:
    return "audio/wav" if provider == "voicevox" else "audio/mpeg"
