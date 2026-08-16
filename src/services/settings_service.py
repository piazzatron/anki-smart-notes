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

from __future__ import annotations

from dataclasses import dataclass

from ..config import config
from ..event_bus import republish_state


@republish_state
def save_settings(settings: Settings) -> None:
    """Persist the complete web settings form and refresh connected webviews."""
    config.generate_at_review = settings.generate_at_review
    config.regenerate_notes_when_batching = settings.regenerate_when_batching
    config.debug = settings.debug
    config.openai_api_key = settings.legacy_openai_key
    config.legacy_openai_model = settings.legacy_openai_model
    config.openai_endpoint = settings.legacy_openai_host
    config.show_wizard_completion = settings.show_wizard_completion
    config.did_dismiss_review_prompt = settings.did_dismiss_review_prompt
    config.did_dismiss_discord_prompt = settings.did_dismiss_discord_prompt


@dataclass(frozen=True)
class Settings:
    generate_at_review: bool
    regenerate_when_batching: bool
    debug: bool
    legacy_openai_key: str | None
    legacy_openai_model: str
    legacy_openai_host: str | None
    show_wizard_completion: bool
    did_dismiss_review_prompt: bool
    did_dismiss_discord_prompt: bool
