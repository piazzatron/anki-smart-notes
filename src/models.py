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

from typing import Dict, List, Literal, Optional, TypedDict, Union

# Providers

TTSProviders = Literal["openai", "elevenLabs", "google"]
ChatProviders = Literal["openai", "anthropic", "deepseek"]

# Chat Models

OpenAIModels = Literal["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-4"]
DeepseekModels = Literal["deepseek-v3"]
AnthropicModels = Literal["claude-3-haiku", "claude-3-5-sonnet"]
ChatModels = Union[OpenAIModels, AnthropicModels, DeepseekModels]

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

deepseek_chat_models: List[ChatModels] = ["deepseek-v3"]

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

SmartFieldType = Literal["chat", "tts", "image"]

# Image Models

ReplicateImageModels = Literal["flux-dev", "flux-schnell"]
ImageModels = Union[ReplicateImageModels]

ImageProviders = Literal["replicate"]


class FieldExtras(TypedDict):

    automatic: bool
    type: SmartFieldType
    use_custom_model: bool

    # Chat
    chat_model: Optional[ChatModels]
    chat_provider: Optional[ChatProviders]
    chat_temperature: Optional[int]
    chat_markdown_to_html: Optional[bool]

    # TTS
    tts_provider: Optional[TTSProviders]
    tts_model: Optional[TTSModels]
    tts_voice: Optional[str]
    tts_strip_html: Optional[bool]

    # Images
    image_provider: Optional[ImageProviders]
    image_model: Optional[ImageModels]


# Any non-mandatory fields should default to none, and will be displayed from global config instead
DEFAULT_EXTRAS: FieldExtras = {
    "automatic": True,
    "type": "chat",
    "use_custom_model": False,
    # Overridable Chat Options
    "chat_markdown_to_html": None,
    "chat_model": None,
    "chat_provider": None,
    "chat_temperature": None,
    # Overridable TTS Options
    "tts_model": None,
    "tts_provider": None,
    "tts_voice": None,
    "tts_strip_html": None,
    # Overridable Image Options
    "image_provider": None,
    "image_model": None,
}


class NoteTypeMap(TypedDict):
    fields: Dict[str, str]
    extras: Dict[str, FieldExtras]


class PromptMap(TypedDict):
    note_types: Dict[str, Dict[str, NoteTypeMap]]


# Overridable Options

OverridableChatOptions = Union[
    Literal["chat_provider"],
    Literal["chat_model"],
    Literal["chat_temperature"],
    Literal["chat_markdown_to_html"],
]

overridable_chat_options: List[OverridableChatOptions] = [
    "chat_provider",
    "chat_model",
    "chat_temperature",
    "chat_markdown_to_html",
]


class OverridableChatOptionsDict(TypedDict):
    chat_provider: Optional[ChatProviders]
    chat_model: Optional[ChatModels]
    chat_temperature: Optional[int]
    chat_markdown_to_html: Optional[bool]


OverridableTTSOptions = Union[
    Literal["tts_model"],
    Literal["tts_provider"],
    Literal["tts_voice"],
    Literal["tts_strip_html"],
]

overridable_tts_options: List[OverridableTTSOptions] = [
    "tts_model",
    "tts_provider",
    "tts_voice",
    "tts_strip_html",
]


class OverrideableTTSOptionsDict(TypedDict):
    tts_model: Optional[TTSModels]
    tts_provider: Optional[TTSProviders]
    tts_voice: Optional[str]
    tts_strip_html: Optional[bool]


OverridableImageOptions = Union[Literal["image_provider"], Literal["image_model"]]
overridable_image_options: List[OverridableImageOptions] = [
    "image_model",
    "image_provider",
]


class OverridableImageOptionsDict(TypedDict):
    image_model: Optional[ImageModels]
    image_provider: Optional[ImageProviders]
