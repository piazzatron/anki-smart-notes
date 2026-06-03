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

from typing import cast

from aqt import mw

from . import config as config_module
from .logger import logger
from .models import (
    ChatGenerationSettings,
    ChatModels,
    ChatProviders,
    ChatReasoningLevel,
    ImageGenerationSettings,
    ImageModels,
    ImageProviders,
    TTSGenerationSettings,
    TTSModels,
    TTSProviders,
)
from .services.smart_field_service import (
    DEFAULT_IMAGE_GENERATION_SETTINGS,
    DEFAULT_TEXT_GENERATION_SETTINGS,
    DEFAULT_TTS_GENERATION_SETTINGS,
    smart_field_service,
)


def migrate_legacy_generation_defaults_config() -> None:
    if not mw:
        return
    addon_config = mw.addonManager.getConfig(config_module.__name__)
    if addon_config is None:
        return
    if addon_config.get("did_migrate_smart_fields_to_sqlite"):
        logger.debug("Generation defaults DB migration: already completed")
        return

    # Global generation defaults used to live in config.json while Smart Fields
    # lived in prompts_map. Import the defaults into SQL before importing fields
    # so any non-custom field rows can point at these rows immediately. Model
    # data migrations run after both imports, so later model backfills update the
    # default row first and inherited fields automatically see the new value.
    logger.info("Generation defaults DB migration: importing config defaults")
    chat_reasoning_level = addon_config.get("chat_reasoning_level")
    if chat_reasoning_level not in {"off", "low", "high"}:
        chat_reasoning_level = DEFAULT_TEXT_GENERATION_SETTINGS.reasoning_level

    smart_field_service.save_chat_defaults(
        ChatGenerationSettings(
            provider=cast(
                ChatProviders,
                addon_config.get("chat_provider")
                or DEFAULT_TEXT_GENERATION_SETTINGS.provider,
            ),
            model=cast(
                ChatModels,
                addon_config.get("chat_model")
                or DEFAULT_TEXT_GENERATION_SETTINGS.model,
            ),
            reasoning_level=cast(ChatReasoningLevel, chat_reasoning_level),
            web_search_enabled=bool(
                addon_config.get("chat_web_search")
                if addon_config.get("chat_web_search") is not None
                else DEFAULT_TEXT_GENERATION_SETTINGS.web_search_enabled
            ),
        )
    )
    smart_field_service.save_tts_defaults(
        TTSGenerationSettings(
            provider=cast(
                TTSProviders,
                addon_config.get("tts_provider")
                or DEFAULT_TTS_GENERATION_SETTINGS.provider,
            ),
            model=cast(
                TTSModels,
                addon_config.get("tts_model") or DEFAULT_TTS_GENERATION_SETTINGS.model,
            ),
            voice_id=str(
                addon_config.get("tts_voice")
                or DEFAULT_TTS_GENERATION_SETTINGS.voice_id
            ),
        )
    )
    smart_field_service.save_image_defaults(
        ImageGenerationSettings(
            provider=cast(
                ImageProviders,
                addon_config.get("image_provider")
                or DEFAULT_IMAGE_GENERATION_SETTINGS.provider,
            ),
            model=cast(
                ImageModels,
                addon_config.get("image_model")
                or DEFAULT_IMAGE_GENERATION_SETTINGS.model,
            ),
        )
    )
