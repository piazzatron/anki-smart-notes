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

from copy import deepcopy
from typing import Literal, TypedDict, Union

from .config import config
from .constants import DEFAULT_CHAT_MODEL, DEFAULT_CHAT_PROVIDER
from .logger import logger
from .models import provider_model_map

ModelType = Literal["chat", "tts"]


class TTSMigrations(TypedDict):
    models: dict[str, str]
    voices: dict[str, str]


migration_map: dict[str, Union[dict[str, str], TTSMigrations]] = {
    "chat": {
        "o1-mini": "gpt-5-mini",
        "gpt-4o": "gpt-5-chat-latest",
        "gpt-4-turbo": "gpt-5-chat-latest",
        "gpt-4": "gpt-5-chat-latest",
        "o3-mini": "gpt-5-mini",
        "gpt-4.1": "gpt-5-chat-latest",
        "gpt-4.1-mini": "gpt-5-mini",
        "gpt-4.1-nano": "gpt-5-nano",
        "o3": "gpt-5",
        "o4-mini": "gpt-5-mini",
    },
    "tts": {
        "models": {
            "eleven_turbo_v2_5": "eleven_flash_v2_5",
        },
        "voices": {},
    },
}


def migrate_models() -> None:
    logger.info("Migrating models...")

    chat_migration_map_raw = migration_map["chat"]
    tts_migrations_raw = migration_map["tts"]

    chat_migration_map: dict[str, str] = chat_migration_map_raw  # type: ignore
    tts_migrations: TTSMigrations = tts_migrations_raw  # type: ignore
    tts_model_migration_map = tts_migrations["models"]
    tts_voice_migration_map = tts_migrations["voices"]

    # Migrate base chat model
    for old_model, new_model in chat_migration_map.items():
        if config.chat_model == old_model:
            logger.debug(f"Chat migration: {old_model} -> {new_model}")
            config.chat_model = new_model  # type: ignore

    # Migrate base TTS model
    for old_model, new_model in tts_model_migration_map.items():
        if config.tts_model == old_model:
            logger.debug(f"TTS model migration: {old_model} -> {new_model}")
            config.tts_model = new_model  # type: ignore

    # Migrate base TTS voice
    for old_voice, new_voice in tts_voice_migration_map.items():
        if config.tts_voice == old_voice:
            logger.debug(f"TTS voice migration: {old_voice} -> {new_voice}")
            config.tts_voice = new_voice  # type: ignore

    # Set defaults for chat
    valid_models = {
        model for models_list in provider_model_map.values() for model in models_list
    }

    if config.chat_model not in valid_models:
        logger.warning(f"Invalid chat model: {config.chat_model}, setting to default")
        config.chat_model = DEFAULT_CHAT_MODEL
        config.chat_provider = DEFAULT_CHAT_PROVIDER

    # Migrate any custom models in prompts_map
    prompts_map = deepcopy(config.prompts_map)
    for _, decks in prompts_map["note_types"].items():
        for _, fields_and_extras in decks.items():
            for _, extras in fields_and_extras["extras"].items():
                chat_model = extras.get("chat_model")
                if chat_model and chat_migration_map.get(chat_model):
                    new_model = chat_migration_map[chat_model]
                    logger.debug(
                        f"Custom chat prompt migration: {extras['chat_model']} -> {new_model}"
                    )
                    extras["chat_model"] = new_model  # type: ignore
                elif chat_model and chat_model not in valid_models:
                    logger.warning(
                        f"Invalid custom chat model in extras: {extras['chat_model']}, setting to default"
                    )
                    extras["chat_model"] = DEFAULT_CHAT_MODEL

                tts_model = extras.get("tts_model")
                if tts_model and tts_model in tts_model_migration_map:
                    new_model = tts_model_migration_map[tts_model]
                    logger.debug(
                        f"Custom TTS model migration: {tts_model} -> {new_model}"
                    )
                    extras["tts_model"] = new_model  # type: ignore

                tts_voice = extras.get("tts_voice")
                if tts_voice and tts_voice in tts_voice_migration_map:
                    new_voice = tts_voice_migration_map[tts_voice]
                    logger.debug(
                        f"Custom TTS voice migration: {tts_voice} -> {new_voice}"
                    )
                    extras["tts_voice"] = new_voice  # type: ignore

    config.prompts_map = prompts_map
    logger.info("Models migration completed.")
