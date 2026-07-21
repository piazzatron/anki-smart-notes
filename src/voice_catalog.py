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
from typing import Literal, TypedDict, cast

from .models import TTSProviders
from .utils import load_file

ALL_LANGUAGES: Literal["All"] = "All"

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
    type: Literal["Standard", "Wavenet", "Neural", "Chirp"]


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
    price_tiers: dict[str, VoicePriceTier] = {
        "Standard": "low",
        "Wavenet": "standard",
        "Neural": "standard",
        "Chirp": "standard",
    }
    return [
        {
            "provider": "google",
            "language": voice["language"],
            "gender": voice["gender"],
            "voice_id": voice["name"],
            "model": voice["type"].lower(),
            "name": (
                f"{voice['language'].capitalize()} - "
                f"{voice['gender'].capitalize()} ({voice['type']})"
            ),
            "price_tier": price_tiers[voice["type"]],
        }
        for voice in raw_voices
    ]


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
