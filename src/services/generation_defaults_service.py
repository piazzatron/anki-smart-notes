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

import sqlite3
from collections.abc import Mapping
from typing import Any, cast

from ..database import open_database
from ..models import (
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

DEFAULT_TEXT_GENERATION_SETTINGS = ChatGenerationSettings(
    provider="auto",
    model="auto",
    reasoning_level="off",
    web_search_enabled=False,
)
DEFAULT_TTS_GENERATION_SETTINGS = TTSGenerationSettings(
    provider="google",
    model="standard",
    voice_id="en-US-Casual-K",
)
DEFAULT_IMAGE_GENERATION_SETTINGS = ImageGenerationSettings(
    provider="openai",
    model="gpt-image-1.5-low",
)


class GenerationDefaultsService:
    """Reads and writes the global generation defaults stored in SQLite."""

    def get_chat_defaults(self) -> ChatGenerationSettings:
        with open_database() as conn:
            row = conn.execute(
                """
                SELECT provider, model, reasoning_level, web_search_enabled
                FROM default_text_generation_settings
                WHERE id = 1
                """
            ).fetchone()
        if not row:
            return DEFAULT_TEXT_GENERATION_SETTINGS
        return _chat_generation_settings_from_row(row)

    def save_chat_defaults(self, settings: ChatGenerationSettings) -> None:
        with open_database() as conn:
            conn.execute(
                """
                INSERT INTO default_text_generation_settings (
                    id, provider, model, reasoning_level, web_search_enabled
                )
                VALUES (1, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    provider = excluded.provider,
                    model = excluded.model,
                    reasoning_level = excluded.reasoning_level,
                    web_search_enabled = excluded.web_search_enabled
                """,
                (
                    settings.provider,
                    settings.model,
                    settings.reasoning_level,
                    int(settings.web_search_enabled),
                ),
            )
            conn.commit()

    def get_tts_defaults(self) -> TTSGenerationSettings:
        with open_database() as conn:
            row = conn.execute(
                """
                SELECT provider, model, voice_id
                FROM default_tts_generation_settings
                WHERE id = 1
                """
            ).fetchone()
        if not row:
            return DEFAULT_TTS_GENERATION_SETTINGS
        return _tts_generation_settings_from_row(row)

    def save_tts_defaults(self, settings: TTSGenerationSettings) -> None:
        with open_database() as conn:
            conn.execute(
                """
                INSERT INTO default_tts_generation_settings (
                    id, provider, model, voice_id
                )
                VALUES (1, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    provider = excluded.provider,
                    model = excluded.model,
                    voice_id = excluded.voice_id
                """,
                (settings.provider, settings.model, settings.voice_id),
            )
            conn.commit()

    def get_image_defaults(self) -> ImageGenerationSettings:
        with open_database() as conn:
            row = conn.execute(
                """
                SELECT provider, model
                FROM default_image_generation_settings
                WHERE id = 1
                """
            ).fetchone()
        if not row:
            return DEFAULT_IMAGE_GENERATION_SETTINGS
        return _image_generation_settings_from_row(row)

    def save_image_defaults(self, settings: ImageGenerationSettings) -> None:
        with open_database() as conn:
            conn.execute(
                """
                INSERT INTO default_image_generation_settings (
                    id, provider, model
                )
                VALUES (1, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    provider = excluded.provider,
                    model = excluded.model
                """,
                (settings.provider, settings.model),
            )
            conn.commit()

    def restore_defaults(self) -> None:
        self.save_chat_defaults(DEFAULT_TEXT_GENERATION_SETTINGS)
        self.save_tts_defaults(DEFAULT_TTS_GENERATION_SETTINGS)
        self.save_image_defaults(DEFAULT_IMAGE_GENERATION_SETTINGS)

    def import_from_legacy_config(self, addon_config: Mapping[str, Any]) -> None:
        self.save_chat_defaults(
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
                reasoning_level=_validated_reasoning_level(
                    addon_config.get("chat_reasoning_level")
                ),
                web_search_enabled=bool(
                    addon_config.get("chat_web_search")
                    if addon_config.get("chat_web_search") is not None
                    else DEFAULT_TEXT_GENERATION_SETTINGS.web_search_enabled
                ),
            )
        )
        self.save_tts_defaults(
            TTSGenerationSettings(
                provider=cast(
                    TTSProviders,
                    addon_config.get("tts_provider")
                    or DEFAULT_TTS_GENERATION_SETTINGS.provider,
                ),
                model=cast(
                    TTSModels,
                    addon_config.get("tts_model")
                    or DEFAULT_TTS_GENERATION_SETTINGS.model,
                ),
                voice_id=str(
                    addon_config.get("tts_voice")
                    or DEFAULT_TTS_GENERATION_SETTINGS.voice_id
                ),
            )
        )
        self.save_image_defaults(
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


def _validated_reasoning_level(value: object) -> ChatReasoningLevel:
    if value in {"off", "low", "high"}:
        return cast(ChatReasoningLevel, value)
    return DEFAULT_TEXT_GENERATION_SETTINGS.reasoning_level


def _chat_generation_settings_from_row(row: sqlite3.Row) -> ChatGenerationSettings:
    return ChatGenerationSettings(
        provider=cast(ChatProviders, row["provider"]),
        model=cast(ChatModels, row["model"]),
        reasoning_level=cast(ChatReasoningLevel, row["reasoning_level"]),
        web_search_enabled=bool(row["web_search_enabled"]),
    )


def _tts_generation_settings_from_row(row: sqlite3.Row) -> TTSGenerationSettings:
    return TTSGenerationSettings(
        provider=cast(TTSProviders, row["provider"]),
        model=cast(TTSModels, row["model"]),
        voice_id=cast(str, row["voice_id"]),
    )


def _image_generation_settings_from_row(row: sqlite3.Row) -> ImageGenerationSettings:
    return ImageGenerationSettings(
        provider=cast(ImageProviders, row["provider"]),
        model=cast(ImageModels, row["model"]),
    )


generation_defaults_service = GenerationDefaultsService()
