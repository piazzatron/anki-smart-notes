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

from .prompt_maps import (
    DEFAULT_EXTRAS,
    FieldExtras,
    NoteTypeMap,
    OverridableChatOptionsDict,
    OverridableImageOptionsDict,
    OverrideableTTSOptionsDict,
    PromptMap,
    overridable_chat_options,
    overridable_image_options,
    overridable_tts_options,
    typed_dict_keys,
)
from .providers import (
    AnthropicModels,
    AzureModels,
    ChatModels,
    ChatProviders,
    ChatReasoningLevel,
    ElevenTTSModels,
    ElevenVoices,
    GeminiModels,
    GenerationExtra,
    GenerationSource,
    GoogleImageModels,
    GoogleModels,
    ImageModels,
    ImageProviders,
    OpenAIImageModels,
    OpenAIModels,
    OpenAITTSModels,
    OpenAIVoices,
    ReplicateImageModels,
    SmartFieldType,
    TTSModels,
    TTSProviders,
    VoiceVoxModels,
    all_image_models,
    anthropic_chat_models,
    gemini_chat_models,
    google_image_models,
    image_model_to_provider,
    image_provider_model_map,
    legacy_openai_chat_models,
    openai_chat_models,
    openai_image_models,
    provider_model_map,
    replicate_image_models,
)
from .smart_fields import (
    ChatSmartFieldSettings,
    ImageSmartFieldSettings,
    SmartField,
    SmartFieldCreate,
    SmartFieldSettings,
    TTSSmartFieldSettings,
    smart_field_type,
)

__all__ = [
    "AnthropicModels",
    "AzureModels",
    "ChatModels",
    "ChatProviders",
    "ChatReasoningLevel",
    "ChatSmartFieldSettings",
    "DEFAULT_EXTRAS",
    "ElevenTTSModels",
    "ElevenVoices",
    "FieldExtras",
    "GeminiModels",
    "GenerationExtra",
    "GenerationSource",
    "GoogleImageModels",
    "GoogleModels",
    "ImageModels",
    "ImageProviders",
    "ImageSmartFieldSettings",
    "NoteTypeMap",
    "OpenAIImageModels",
    "OpenAIModels",
    "OpenAITTSModels",
    "OpenAIVoices",
    "OverridableChatOptionsDict",
    "OverridableImageOptionsDict",
    "OverrideableTTSOptionsDict",
    "PromptMap",
    "ReplicateImageModels",
    "SmartFieldType",
    "SmartField",
    "SmartFieldCreate",
    "SmartFieldSettings",
    "TTSModels",
    "TTSProviders",
    "TTSSmartFieldSettings",
    "VoiceVoxModels",
    "all_image_models",
    "anthropic_chat_models",
    "gemini_chat_models",
    "google_image_models",
    "image_model_to_provider",
    "image_provider_model_map",
    "legacy_openai_chat_models",
    "openai_chat_models",
    "openai_image_models",
    "overridable_chat_options",
    "overridable_image_options",
    "overridable_tts_options",
    "provider_model_map",
    "replicate_image_models",
    "smart_field_type",
    "typed_dict_keys",
]
