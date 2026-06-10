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

# The single write path for domain state (see specs/web-ui-architecture.md in
# the top-level repo). Both the HTTP command routes and the Qt dialogs call
# these functions — never the services directly — so every mutation publishes
# an invalidation and any open webview stays live. Services stay pure; event
# publication is this layer's job.
#
# All functions must run on Anki's main thread.

from anki.decks import DeckId

from ..models.smart_fields import GenerationDefaults, SmartFieldCreate
from ..services.smart_field_service import smart_field_service
from .event_bus import StateInvalidated, event_bus


def save_smart_field(create: SmartFieldCreate) -> None:
    smart_field_service.save_smart_field(create)
    event_bus.publish(StateInvalidated())


def replace_all_smart_fields(creates: list[SmartFieldCreate]) -> None:
    smart_field_service.replace_all_smart_fields(creates)
    event_bus.publish(StateInvalidated())


def delete_smart_field(
    note_type_id: int, deck_id: DeckId, target_field_name: str
) -> None:
    smart_field_service.delete_smart_field(note_type_id, deck_id, target_field_name)
    event_bus.publish(StateInvalidated())


def save_generation_defaults(defaults: GenerationDefaults) -> None:
    smart_field_service.save_chat_defaults(defaults.chat)
    smart_field_service.save_tts_defaults(defaults.tts)
    smart_field_service.save_image_defaults(defaults.image)
    event_bus.publish(StateInvalidated())


def restore_generation_defaults() -> None:
    smart_field_service.restore_generation_defaults()
    event_bus.publish(StateInvalidated())
