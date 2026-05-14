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

from typing import Literal, TypedDict, Union

GenerationSource = Literal["card_generation", "prompt_test", "custom_field"]


class GenerationExtra(TypedDict):
    generation_source: GenerationSource


TTSProviders = Literal["openai", "elevenLabs", "google", "azure", "voicevox"]
ChatProviders = Literal["auto", "openai", "anthropic", "deepseek", "google"]

OpenAIModels = Literal[
    "gpt-5",
    "gpt-5-mini",
    "gpt-5-nano",
    "gpt-5-chat-latest",
    "gpt-4o-mini",
]
AutoModels = Literal["auto"]
DeepseekModels = Literal["deepseek-v3"]
AnthropicModels = Literal["claude-haiku-4-5", "claude-sonnet-4-6", "claude-opus-4-6"]
GeminiModels = Literal["gemini-3.1-pro", "gemini-3.1-flash-lite", "gemini-3-flash"]
ChatModels = Union[
    AutoModels, OpenAIModels, AnthropicModels, DeepseekModels, GeminiModels
]

# Order that the models are displayed in the UI.
auto_chat_models: list[ChatModels] = ["auto"]

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
    "auto": auto_chat_models,
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

OpenAITTSModels = Literal["tts-1", "gpt-4o-mini-tts"]
ElevenTTSModels = Literal["eleven_multilingual_v2"]
GoogleModels = Literal["standard", "wavenet", "neural"]
AzureModels = Literal["standard", "neural"]
VoiceVoxModels = Literal["voicevox"]
TTSModels = Union[
    OpenAITTSModels, ElevenTTSModels, GoogleModels, AzureModels, VoiceVoxModels
]

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

ReplicateImageModels = Literal["flux-dev", "z-image-turbo"]
GoogleImageModels = Literal["nano-banana-2"]
OpenAIImageModels = Literal[
    "gpt-image-1.5-medium",
    "gpt-image-1.5-low",
    "gpt-image-2-medium",
    "gpt-image-2-low",
]
ImageModels = Union[ReplicateImageModels, GoogleImageModels, OpenAIImageModels]

ImageProviders = Literal["replicate", "google", "openai"]

openai_image_models: list[ImageModels] = [
    "gpt-image-1.5-low",
    "gpt-image-2-low",
    "gpt-image-1.5-medium",
    "gpt-image-2-medium",
]

google_image_models: list[ImageModels] = ["nano-banana-2"]

replicate_image_models: list[ImageModels] = ["z-image-turbo", "flux-dev"]

image_provider_model_map: dict[ImageProviders, list[ImageModels]] = {
    "openai": openai_image_models,
    "google": google_image_models,
    "replicate": replicate_image_models,
}

# Ordered from cheapest to most expensive.
all_image_models: list[ImageModels] = [
    "z-image-turbo",
    "gpt-image-1.5-low",
    "gpt-image-2-low",
    "flux-dev",
    "gpt-image-1.5-medium",
    "gpt-image-2-medium",
    "nano-banana-2",
]

image_model_to_provider: dict[ImageModels, ImageProviders] = {
    "flux-dev": "replicate",
    "z-image-turbo": "replicate",
    "nano-banana-2": "google",
    "gpt-image-1.5-low": "openai",
    "gpt-image-1.5-medium": "openai",
    "gpt-image-2-low": "openai",
    "gpt-image-2-medium": "openai",
}
