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

# The web UI wire format, defined in one place (see specs/web-ui-architecture.md
# in the top-level repo). `models` holds the typed wire shapes, `builders` maps
# domain objects to them, and `parsers` maps command payloads back to domain
# objects. Callers use the package as `dto.<name>`.

from ...constants import GLOBAL_DECK_ID
from .builders import (
    build_catalog,
    build_generation_defaults,
    build_selection_changed,
    build_selection_cleared,
    build_settings,
    build_state,
    build_voice_catalog,
)
from .models import (
    CHAT_REASONING_LEVELS,
    PromptGenerateRequest,
    SettingsDto,
    SmartFieldDto,
    StateDto,
    VoiceCatalogDto,
)
from .parsers import (
    parse_account_refresh,
    parse_analytics_event,
    parse_auth_exchange_code,
    parse_auth_logout,
    parse_chat_generation_settings,
    parse_feedback_message,
    parse_generation_defaults,
    parse_image_generation_settings,
    parse_image_prompt_test,
    parse_prompt_generate,
    parse_save_test_result,
    parse_settings,
    parse_smart_field_create,
    parse_smart_field_id,
    parse_smart_field_update,
    parse_text_prompt_test,
    parse_tts_generation_settings,
    parse_tts_prompt_test,
    parse_ui_open_browser,
)

__all__ = [
    "GLOBAL_DECK_ID",
    "CHAT_REASONING_LEVELS",
    "PromptGenerateRequest",
    "SettingsDto",
    "SmartFieldDto",
    "StateDto",
    "VoiceCatalogDto",
    "build_catalog",
    "build_generation_defaults",
    "build_selection_changed",
    "build_selection_cleared",
    "build_settings",
    "build_state",
    "build_voice_catalog",
    "parse_account_refresh",
    "parse_analytics_event",
    "parse_auth_exchange_code",
    "parse_auth_logout",
    "parse_chat_generation_settings",
    "parse_feedback_message",
    "parse_generation_defaults",
    "parse_image_generation_settings",
    "parse_image_prompt_test",
    "parse_prompt_generate",
    "parse_save_test_result",
    "parse_settings",
    "parse_smart_field_create",
    "parse_smart_field_id",
    "parse_smart_field_update",
    "parse_text_prompt_test",
    "parse_tts_generation_settings",
    "parse_tts_prompt_test",
    "parse_ui_open_browser",
]
