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

from .config import config
from .constants import DEFAULT_CHAT_MODEL, DEFAULT_CHAT_PROVIDER
from .logger import logger
from .models import provider_model_map


def migrate_models() -> None:
    logger.info("Migrating chat models...")
    migration_map = {
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
    }

    # Migrate base model
    for old_model, new_model in migration_map.items():
        if config.chat_model == old_model:
            logger.debug(f"Migration: {old_model} -> {new_model}")
            config.chat_model = new_model  # type: ignore

    # Set defaults
    valid_models = {
        model for models_list in provider_model_map.values() for model in models_list
    }

    if config.chat_model not in valid_models:
        logger.warning(f"Invalid chat model: {config.chat_model}, setting to default")
        config.chat_model = DEFAULT_CHAT_MODEL
        config.chat_provider = DEFAULT_CHAT_PROVIDER

    # Migrate any custom models
    prompts_map = deepcopy(config.prompts_map)
    # Notes
    for _, decks in prompts_map["note_types"].items():
        # Decks
        for _, fields_and_extras in decks.items():
            # Fields
            for _, extras in fields_and_extras["extras"].items():
                chat_model = extras.get("chat_model")
                if chat_model and migration_map.get(chat_model):
                    new_model = migration_map[chat_model]
                    logger.debug(
                        f"Custom prompt migration: {extras['chat_model']} -> {new_model}"
                    )
                    extras["chat_model"] = new_model  # type: ignore
                elif chat_model and chat_model not in valid_models:
                    logger.warning(
                        f"Invalid custom chat model in extras: {extras['chat_model']}, setting to default"
                    )
                    extras["chat_model"] = DEFAULT_CHAT_MODEL

    config.prompts_map = prompts_map
    logger.info("Chat models migration completed.")
