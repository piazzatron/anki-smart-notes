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
from pathlib import Path
from typing import cast

import pytest

from src.ui import tts_options
from src.ui.tts_options import TTSMeta


@pytest.mark.parametrize(
    ("provider", "model", "voice_id", "expected"),
    [
        ("openai", "gpt-4o-mini-tts", "alloy", "OpenAI (Alloy (4o-mini))"),
        (
            "google",
            "standard",
            "en-US-Standard-C",
            "Google (English - Female (Standard))",
        ),
        (
            "elevenLabs",
            "eleven_multilingual_v2",
            "EXAVITQu4vr4xnSDxMaL",
            "ElevenLabs (Sarah (Multilingual V2))",
        ),
        ("azure", "neural", "en-US-JennyNeural", "Azure (Jenny (Neural))"),
        ("voicevox", "voicevox", "2", "VoiceVox (Shikoku Metan (Normal))"),
    ],
)
def test_format_tts_voice_label_uses_selected_voice(
    monkeypatch: pytest.MonkeyPatch,
    provider: str,
    model: str,
    voice_id: str,
    expected: str,
) -> None:
    monkeypatch.setattr(tts_options, "voices", _sample_voices())

    assert tts_options.format_tts_voice_label(provider, model, voice_id) == expected


def test_format_tts_voice_label_falls_back_to_voice_id_for_stale_data(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(tts_options, "voices", _sample_voices())

    assert (
        tts_options.format_tts_voice_label("google", "standard", "missing-voice")
        == "Google (missing-voice)"
    )


def test_eleven_voice_catalog_includes_stefanos() -> None:
    catalog_path = Path(__file__).parents[1] / "eleven_voices.json"
    voices = json.loads(catalog_path.read_text(encoding="utf-8"))

    assert {
        "voice_id": "20zUtLxCwVzsFDWub4sB",
        "name": "Stefanos (Athenian)",
        "gender": "male",
        "country": "el",
        "preview_url": "",
        "language": "Greek",
    } in voices


def _sample_voices() -> list[TTSMeta]:
    return [
        cast(
            TTSMeta,
            {
                "tts_provider": "openai",
                "voice": "alloy",
                "model": "gpt-4o-mini-tts",
                "friendly_voice": "Alloy (4o-mini)",
                "gender": "Female",
                "language": "All",
                "price_tier": "standard",
            },
        ),
        cast(
            TTSMeta,
            {
                "tts_provider": "google",
                "voice": "en-US-Standard-C",
                "model": "standard",
                "friendly_voice": "English - Female (Standard)",
                "gender": "Female",
                "language": "English",
                "price_tier": "low",
            },
        ),
        cast(
            TTSMeta,
            {
                "tts_provider": "elevenLabs",
                "voice": "EXAVITQu4vr4xnSDxMaL",
                "model": "eleven_multilingual_v2",
                "friendly_voice": "Sarah (Multilingual V2)",
                "gender": "Female",
                "language": "English (United States)",
                "price_tier": "ultra-high",
            },
        ),
        cast(
            TTSMeta,
            {
                "tts_provider": "azure",
                "voice": "en-US-JennyNeural",
                "model": "neural",
                "friendly_voice": "Jenny (Neural)",
                "gender": "Female",
                "language": "English",
                "price_tier": "standard",
            },
        ),
        cast(
            TTSMeta,
            {
                "tts_provider": "voicevox",
                "voice": "2",
                "model": "voicevox",
                "friendly_voice": "Shikoku Metan (Normal)",
                "gender": "Female",
                "language": "Japanese",
                "price_tier": "free",
            },
        ),
    ]
