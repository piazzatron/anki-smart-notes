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

from dataclasses import dataclass

from anki.decks import DeckId
from anki.errors import NotFoundError
from anki.notes import Note
from aqt import mw

from ..field_resolver import field_resolver
from ..models.smart_fields import TextPromptTestRequest


@dataclass(frozen=True)
class TextPromptTestContext:
    """Card data captured on Anki's main thread for an async prompt test."""

    note: Note
    deck_id: DeckId
    request: TextPromptTestRequest


def prepare_text_prompt_test(request: TextPromptTestRequest) -> TextPromptTestContext:
    """Refetch the requested card so tests never trust client-supplied note data."""
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


async def run_text_prompt_test(context: TextPromptTestContext) -> dict[str, str]:
    """Generate a text preview without writing anything back to the card."""
    settings = context.request.settings
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

    return {"text": text}
