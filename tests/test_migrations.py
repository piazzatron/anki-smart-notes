# type: ignore

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

from typing import Any
from unittest.mock import MagicMock

import pytest
from attr import dataclass


@dataclass
class MockConfig:
    prompts_map: Any
    chat_provider: str = "openai"
    chat_model: str = "gpt-4o-mini"
    tts_model: str = "tts-1"
    tts_voice: str = "alloy"

    def __setattr__(self, name: str, value: Any) -> None:
        object.__setattr__(self, name, value)


@pytest.fixture
def mock_config(monkeypatch):
    config = MockConfig(
        prompts_map={
            "note_types": {
                "Basic": {
                    "All": {
                        "fields": {"Front": "test", "Back": "test"},
                        "extras": {
                            "Front": {
                                "type": "chat",
                                "chat_model": None,
                                "tts_model": None,
                                "tts_voice": None,
                            },
                            "Back": {
                                "type": "tts",
                                "chat_model": None,
                                "tts_model": None,
                                "tts_voice": None,
                            },
                        },
                    }
                }
            }
        }
    )
    monkeypatch.setattr("src.migrations.config", config)
    return config


@pytest.fixture
def mock_logger(monkeypatch):
    logger = MagicMock()
    monkeypatch.setattr("src.migrations.logger", logger)
    return logger


def test_migrate_chat_models_global(mock_config, mock_logger, monkeypatch):
    from src.migrations import migrate_models

    monkeypatch.setattr("src.migrations.DEFAULT_CHAT_MODEL", "gpt-5-mini")
    monkeypatch.setattr("src.migrations.DEFAULT_CHAT_PROVIDER", "openai")

    mock_config.chat_model = "gpt-4o"
    migrate_models()

    assert mock_config.chat_model == "gpt-5-chat-latest"


def test_migrate_tts_models_global(mock_config, mock_logger):
    from src.migrations import migrate_models

    mock_config.tts_model = "eleven_turbo_v2_5"
    migrate_models()

    assert mock_config.tts_model == "eleven_flash_v2_5"


def test_migrate_chat_models_custom_prompts(mock_config, mock_logger, monkeypatch):
    from src.migrations import migrate_models

    monkeypatch.setattr("src.migrations.DEFAULT_CHAT_MODEL", "gpt-5-mini")
    monkeypatch.setattr("src.migrations.DEFAULT_CHAT_PROVIDER", "openai")

    mock_config.prompts_map["note_types"]["Basic"]["All"]["extras"]["Front"][
        "chat_model"
    ] = "o1-mini"

    migrate_models()

    assert (
        mock_config.prompts_map["note_types"]["Basic"]["All"]["extras"]["Front"][
            "chat_model"
        ]
        == "gpt-5-mini"
    )


def test_migrate_tts_models_custom_prompts(mock_config, mock_logger):
    from src.migrations import migrate_models

    mock_config.prompts_map["note_types"]["Basic"]["All"]["extras"]["Back"][
        "tts_model"
    ] = "eleven_turbo_v2_5"

    migrate_models()

    assert (
        mock_config.prompts_map["note_types"]["Basic"]["All"]["extras"]["Back"][
            "tts_model"
        ]
        == "eleven_flash_v2_5"
    )


def test_migrate_multiple_models(mock_config, mock_logger, monkeypatch):
    from src.migrations import migrate_models

    monkeypatch.setattr("src.migrations.DEFAULT_CHAT_MODEL", "gpt-5-mini")
    monkeypatch.setattr("src.migrations.DEFAULT_CHAT_PROVIDER", "openai")

    mock_config.chat_model = "gpt-4"
    mock_config.tts_model = "eleven_turbo_v2_5"
    mock_config.prompts_map["note_types"]["Basic"]["All"]["extras"]["Front"][
        "chat_model"
    ] = "o3-mini"
    mock_config.prompts_map["note_types"]["Basic"]["All"]["extras"]["Back"][
        "tts_model"
    ] = "eleven_turbo_v2_5"

    migrate_models()

    assert mock_config.chat_model == "gpt-5-chat-latest"
    assert mock_config.tts_model == "eleven_flash_v2_5"
    assert (
        mock_config.prompts_map["note_types"]["Basic"]["All"]["extras"]["Front"][
            "chat_model"
        ]
        == "gpt-5-mini"
    )
    assert (
        mock_config.prompts_map["note_types"]["Basic"]["All"]["extras"]["Back"][
            "tts_model"
        ]
        == "eleven_flash_v2_5"
    )


def test_no_migration_needed(mock_config, mock_logger):
    from src.migrations import migrate_models

    mock_config.chat_model = "gpt-5-mini"
    mock_config.tts_model = "eleven_flash_v2_5"

    migrate_models()

    assert mock_config.chat_model == "gpt-5-mini"
    assert mock_config.tts_model == "eleven_flash_v2_5"


def test_migrate_tts_voice_global(mock_config, mock_logger):
    from src.migrations import migrate_models, migration_map

    migration_map["tts"]["voices"]["old_voice_id"] = "new_voice_id"  # type: ignore

    mock_config.tts_voice = "old_voice_id"
    migrate_models()

    assert mock_config.tts_voice == "new_voice_id"


def test_migrate_tts_voice_custom_prompts(mock_config, mock_logger):
    from src.migrations import migrate_models, migration_map

    migration_map["tts"]["voices"]["old_voice_id"] = "new_voice_id"  # type: ignore

    mock_config.prompts_map["note_types"]["Basic"]["All"]["extras"]["Back"][
        "tts_voice"
    ] = "old_voice_id"

    migrate_models()

    assert (
        mock_config.prompts_map["note_types"]["Basic"]["All"]["extras"]["Back"][
            "tts_voice"
        ]
        == "new_voice_id"
    )
