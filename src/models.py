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

from typing import List, Literal, Union

# Providers

TTSProviders = Literal["openai", "elevenLabs", "google"]
ChatProviders = Literal["openai", "anthropic"]

# Chat Models

OpenAIModels = Literal["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-4"]
AnthropicModels = Literal["claude-3-haiku", "claude-3-5-sonnet"]
ChatModels = Union[OpenAIModels, AnthropicModels]

legacy_openai_chat_models: List[OpenAIModels] = [
    "gpt-4o-mini",
    "gpt-4o",
    "gpt-4-turbo",
    "gpt-4",
]
openai_chat_models: List[ChatModels] = ["gpt-4o", "gpt-4o-mini"]
anthropic_chat_models: List[ChatModels] = [
    "claude-3-5-sonnet",
    "claude-3-haiku",
]

# TTS Models

OpenAITTSModels = Literal["tts-1"]
ElevenTTSModels = Literal["eleven_multilingual_v2"]
GoogleModels = Literal["standard", "wavenet", "neural"]
TTSModels = Union[OpenAITTSModels, ElevenTTSModels, GoogleModels]

# TTS Voices

OpenAIVoices = Literal[
    "alloy",
    "echo",
    "fable",
    "onyx",
    "nova",
    "shimmer",
]

ElevenVoices = Literal["male-1", "male-2", "female-1", "female-2"]
