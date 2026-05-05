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

from typing import Any, Literal, Optional, TypedDict, Union

GenerationSource = Literal["card_generation", "prompt_test", "custom_field"]


class GenerationExtra(TypedDict):
    generation_source: GenerationSource


# Providers

TTSProviders = Literal["openai", "elevenLabs", "google", "azure", "voicevox"]
ChatProviders = Literal["openai", "anthropic", "deepseek", "google"]

# Chat Models

OpenAIModels = Literal[
    "gpt-5",
    "gpt-5-mini",
    "gpt-5-nano",
    "gpt-5-chat-latest",
    "gpt-4o-mini",
]
DeepseekModels = Literal["deepseek-v3"]
AnthropicModels = Literal["claude-haiku-4-5", "claude-sonnet-4-6", "claude-opus-4-6"]
GeminiModels = Literal["gemini-3.1-pro", "gemini-3.1-flash-lite", "gemini-3-flash"]
ChatModels = Union[OpenAIModels, AnthropicModels, DeepseekModels, GeminiModels]

# Order that the models are displayed in the UI
openai_chat_models: list[ChatModels] = [
    "gpt-5-nano",
    "gpt-4o-mini",
    "gpt-5-mini",
    "gpt-5-chat-latest",
    "gpt-5",
]

anthropic_chat_models: list[ChatModels] = [
    "claude-haiku-4-5",
    "claude-sonnet-4-6",
    "claude-opus-4-6",
]

deepseek_chat_models: list[ChatModels] = ["deepseek-v3"]

gemini_chat_models: list[ChatModels] = [
    "gemini-3.1-flash-lite",
    "gemini-3-flash",
    "gemini-3.1-pro",
]

provider_model_map: dict[ChatProviders, list[ChatModels]] = {
    "openai": openai_chat_models,
    "anthropic": anthropic_chat_models,
    "deepseek": deepseek_chat_models,
    "google": gemini_chat_models,
}


legacy_openai_chat_models: list[str] = [
    "gpt-5-chat-latest",
    "gpt-5",
    "gpt-5-nano",
    "gpt-5-mini",
    "gpt-4o-mini",
    "gpt-4o",
    "gpt-4-turbo",
    "gpt-4",
    "o3-mini",
    "o1-mini",
    "gpt-4.1",
    "gpt-4.1-mini",
    "gpt-4.1-nano",
    "o3",
    "o4-mini",
]

# TTS Models

OpenAITTSModels = Literal["tts-1", "gpt-4o-mini-tts"]
ElevenTTSModels = Literal["eleven_multilingual_v2"]
GoogleModels = Literal["standard", "wavenet", "neural"]
AzureModels = Literal["standard", "neural"]
VoiceVoxModels = Literal["voicevox"]
TTSModels = Union[
    OpenAITTSModels, ElevenTTSModels, GoogleModels, AzureModels, VoiceVoxModels
]

# TTS Voices

OpenAIVoices = Literal[
    "alloy",
    "ash",
    "coral",
    "echo",
    "fable",
    "nova",
    "onyx",
    "sage",
    "shimmer",
]

ElevenVoices = Literal["male-1", "male-2", "female-1", "female-2"]

SmartFieldType = Literal["chat", "tts", "image"]

# Image Models

ReplicateImageModels = Literal["flux-dev", "z-image-turbo"]
GoogleImageModels = Literal["nano-banana-2"]
OpenAIImageModels = Literal["gpt-image-1.5-medium", "gpt-image-1.5-low"]
ImageModels = Union[ReplicateImageModels, GoogleImageModels, OpenAIImageModels]

ImageProviders = Literal["replicate", "google", "openai"]

# Ordered from cheapest -> most expensive
all_image_models: list[ImageModels] = [
    "z-image-turbo",
    "gpt-image-1.5-low",
    "flux-dev",
    "gpt-image-1.5-medium",
    "nano-banana-2",
]

image_model_to_provider: dict[ImageModels, ImageProviders] = {
    "flux-dev": "replicate",
    "z-image-turbo": "replicate",
    "nano-banana-2": "google",
    "gpt-image-1.5-low": "openai",
    "gpt-image-1.5-medium": "openai",
}


class FieldExtras(TypedDict):
    automatic: bool
    type: SmartFieldType
    use_custom_model: bool

    # Chat
    chat_model: Optional[ChatModels]
    chat_provider: Optional[ChatProviders]
    chat_temperature: Optional[int]
    chat_markdown_to_html: Optional[bool]
    chat_web_search: Optional[bool]

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
    "chat_web_search": None,
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
    fields: dict[str, str]
    extras: dict[str, FieldExtras]


class PromptMap(TypedDict):
    note_types: dict[str, dict[str, NoteTypeMap]]


# Overridable Options
#
# Each field type (chat, tts, image) has a TypedDict defining its overridable
# options. The runtime key lists are derived automatically from these TypedDicts,
# so adding a new option only requires updating the TypedDict (plus FieldExtras
# and DEFAULT_EXTRAS).


def _typed_dict_keys(td: Any) -> list[str]:
    return list(td.__annotations__.keys())


class OverridableChatOptionsDict(TypedDict):
    chat_provider: Optional[ChatProviders]
    chat_model: Optional[ChatModels]
    chat_temperature: Optional[int]
    chat_markdown_to_html: Optional[bool]
    chat_web_search: Optional[bool]


overridable_chat_options: list[str] = _typed_dict_keys(OverridableChatOptionsDict)


class OverrideableTTSOptionsDict(TypedDict):
    tts_model: Optional[TTSModels]
    tts_provider: Optional[TTSProviders]
    tts_voice: Optional[str]
    tts_strip_html: Optional[bool]


overridable_tts_options: list[str] = _typed_dict_keys(OverrideableTTSOptionsDict)


class OverridableImageOptionsDict(TypedDict):
    image_model: Optional[ImageModels]
    image_provider: Optional[ImageProviders]


overridable_image_options: list[str] = _typed_dict_keys(OverridableImageOptionsDict)
