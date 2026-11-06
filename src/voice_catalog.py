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

import json
from functools import cache
from typing import TYPE_CHECKING, Literal, Optional, TypedDict, cast

from .models import TTSModels, TTSProviders
from .models.smart_fields import TTSGenerationSettings
from .utils import load_file

if TYPE_CHECKING:
    from .subscription_provider import VoiceRule

ALL_LANGUAGES: Literal["All"] = "All"
# A free voice reads in this language when the field's own language has none.
FALLBACK_LANGUAGE = "English (United States)"

VoiceGender = Literal["Male", "Female", "All"]
VoicePriceTier = Literal["free", "low", "standard", "high", "ultra-high"]


class TTSVoice(TypedDict):
    provider: TTSProviders
    voice_id: str
    model: str
    name: str
    gender: VoiceGender
    language: str
    price_tier: VoicePriceTier


class GoogleVoice(TypedDict):
    gender: Literal["Male", "Female"]
    languageCode: str
    language: str
    name: str
    type: Literal["Standard", "Chirp"]


class ElevenVoice(TypedDict):
    voice_id: str
    name: str
    gender: str
    country: str
    preview_url: str
    language: str


class AzureVoice(TypedDict):
    name: str
    displayName: str
    locale: str
    language: str
    gender: Literal["Male", "Female"]
    voiceType: Literal["Neural", "NeuralHD"]
    styleList: list[str]
    sampleRateHertz: str


class VoiceVoxVoice(TypedDict):
    name: str
    styleId: int
    styleName: str
    gender: Literal["Male", "Female"]


@cache
def get_voice_catalog() -> list[TTSVoice]:
    return [
        *_get_google_voices(),
        *_get_openai_voices(),
        *_get_eleven_voices(),
        *_get_azure_voices(),
        *_get_voicevox_voices(),
    ]


def is_voice_allowed(
    voice: TTSGenerationSettings, rules: Optional[list["VoiceRule"]]
) -> bool:
    """Whether a plan with these voice rules can use a voice. None allows every
    voice."""
    return rules is None or any(
        rule["provider"] == voice.provider
        and rule["model"] == voice.model
        and rule["voiceIdIncludes"] in voice.voice_id
        for rule in rules
    )


def plan_voice(
    voice: TTSGenerationSettings,
    rules: Optional[list["VoiceRule"]],
    catalog: list[TTSVoice],
) -> Optional[TTSGenerationSettings]:
    """The voice a plan with these rules generates with: this one when it's
    allowed, else an allowed voice in its language, or in US English when its
    language has none (OpenAI's voices have no single language), of its gender
    when there is one. None when the plan allows neither."""
    if is_voice_allowed(voice, rules):
        return voice

    current = next((entry for entry in catalog if settings_of(entry) == voice), None)
    allowed = [
        entry for entry in catalog if is_voice_allowed(settings_of(entry), rules)
    ]
    language = current["language"] if current else None
    candidates = [entry for entry in allowed if entry["language"] == language] or [
        entry for entry in allowed if entry["language"] == FALLBACK_LANGUAGE
    ]
    match = next(
        (
            entry
            for entry in candidates
            if current and entry["gender"] == current["gender"]
        ),
        next(iter(candidates), None),
    )
    return None if match is None else settings_of(match)


def settings_of(voice: TTSVoice) -> TTSGenerationSettings:
    """The settings that generate with a catalog voice."""
    return TTSGenerationSettings(
        provider=voice["provider"],
        model=cast(TTSModels, voice["model"]),
        voice_id=voice["voice_id"],
    )


def _get_openai_voices() -> list[TTSVoice]:
    voice_defs = [
        ("alloy", "Female"),
        ("ash", "Male"),
        ("coral", "Female"),
        ("echo", "Male"),
        ("fable", "Female"),
        ("nova", "Female"),
        ("onyx", "Male"),
        ("sage", "Female"),
        ("shimmer", "Female"),
    ]
    models = [
        ("gpt-4o-mini-tts", "4o-mini"),
        ("tts-1", "TTS-1"),
    ]
    return [
        {
            "provider": "openai",
            "voice_id": voice_id,
            "model": model,
            "name": f"{voice_id.capitalize()} ({friendly_model})",
            "gender": cast(VoiceGender, gender),
            "language": ALL_LANGUAGES,
            "price_tier": "standard",
        }
        for voice_id, gender in voice_defs
        for model, friendly_model in models
    ]


def _get_google_voices() -> list[TTSVoice]:
    raw_voices: list[GoogleVoice] = json.loads(
        load_file("google_voices.json", test_override="[]")
    )
    price_tiers: dict[str, VoicePriceTier] = {"Standard": "low", "Chirp": "standard"}
    return [
        {
            "provider": "google",
            "language": voice["language"],
            "gender": voice["gender"],
            "voice_id": voice["name"],
            "model": voice["type"].lower(),
            "name": (
                f"{voice['language'].capitalize()} - "
                f"{voice['gender'].capitalize()}{_google_voice_label(voice)}"
            ),
            "price_tier": price_tiers[voice["type"]],
        }
        for voice in raw_voices
    ]


def _google_voice_label(voice: GoogleVoice) -> str:
    # A locale has one Standard voice per gender but several Chirp 3 HD ones, so
    # those lead with the speaker, which pickers then show before truncating:
    # " Achernar (Chirp 3 HD)".
    if voice["type"] == "Standard":
        return " (Standard)"
    return f" {voice['name'].split('-')[-1]} (Chirp 3 HD)"


def _get_eleven_voices() -> list[TTSVoice]:
    raw_voices: list[ElevenVoice] = json.loads(
        load_file("eleven_voices.json", test_override="[]")
    )
    models: list[tuple[str, str, VoicePriceTier]] = [
        ("eleven_v3", "V3", "ultra-high"),
        ("eleven_multilingual_v2", "Multilingual V2", "ultra-high"),
        ("eleven_flash_v2_5", "Flash V2.5", "high"),
    ]
    return [
        {
            "provider": "elevenLabs",
            "language": voice["language"],
            "voice_id": voice["voice_id"],
            "model": model,
            "name": f"{voice['name'].capitalize()} ({friendly_model})",
            "gender": cast(VoiceGender, voice["gender"].capitalize()),
            "price_tier": price_tier,
        }
        for voice in raw_voices
        for model, friendly_model, price_tier in models
    ]


def _get_azure_voices() -> list[TTSVoice]:
    raw_voices: list[AzureVoice] = json.loads(
        load_file("azure_voices.json", test_override="[]")
    )
    return [
        {
            "provider": "azure",
            "language": voice["language"],
            "gender": voice["gender"],
            "voice_id": voice["name"],
            "model": voice["voiceType"].lower(),
            "name": f"{voice['displayName'].title()} ({voice['voiceType']})",
            "price_tier": "standard",
        }
        for voice in raw_voices
    ]


def _get_voicevox_voices() -> list[TTSVoice]:
    raw_voices: list[VoiceVoxVoice] = json.loads(
        load_file("voicevox_voices.json", test_override="[]")
    )
    return [
        {
            "provider": "voicevox",
            "language": "Japanese",
            "gender": voice["gender"],
            "voice_id": str(voice["styleId"]),
            "model": "voicevox",
            "name": f"{voice['name']} ({voice['styleName']})",
            "price_tier": "free",
        }
        for voice in raw_voices
    ]
