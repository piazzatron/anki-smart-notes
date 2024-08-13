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

TTSProviders = Literal["openai", "elevenLabs"]
ChatProviders = Literal["openai", "anthropic"]

# Chat Models

OpenAIModels = Literal["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-4"]
AnthropicModels = Literal["claude-3-opus", "claude-3-haiku", "claude-3-5-sonnet"]
ChatModels = Union[OpenAIModels, AnthropicModels]

openai_chat_models: List[ChatModels] = ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-4"]
anthropic_chat_models: List[ChatModels] = [
    "claude-3-5-sonnet",
    "claude-3-opus",
    "claude-3-haiku",
]

# TTS Models

OpenAITTSModels = Literal["tts-1"]
TTSModels = Union[OpenAITTSModels]

# TTS Voices

OpenAIVoices = Literal[
    "alloy",
    "echo",
    "fable",
    "onyx",
    "nova",
    "shimmer",
]
TTSVoices = Union[OpenAIVoices]
Languages = Literal["english", "japanese"]
