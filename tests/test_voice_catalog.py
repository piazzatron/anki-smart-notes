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

from typing import Any, Optional, cast

import pytest
from fixtures import FREE_PLAN_VOICES, sample_voice

from src.models.smart_fields import TTSGenerationSettings
from src.voice_catalog import TTSVoice, plan_voice

CATALOG = cast(
    list[TTSVoice],
    [
        sample_voice("google", "neural", "ja-JP-Neural2-C", "Japanese", "Male"),
        sample_voice("google", "standard", "ja-JP-Standard-A", "Japanese", "Female"),
        sample_voice("google", "standard", "ja-JP-Standard-C", "Japanese", "Male"),
        sample_voice("voicevox", "voicevox", "3", "Japanese", "Female"),
        # Google files this Premium voice under Standard; it isn't free.
        sample_voice(
            "google", "standard", "en-US-Casual-K", "English (United States)", "Male"
        ),
        sample_voice(
            "google",
            "standard",
            "en-US-Standard-C",
            "English (United States)",
            "Female",
        ),
        sample_voice("openai", "tts-1", "alloy", "All", "Female"),
        sample_voice("google", "chirp", "sw-KE-Chirp3-HD-Achird", "Swahili", "Male"),
    ],
)


def voice(provider: str, model: str, voice_id: str) -> TTSGenerationSettings:
    return TTSGenerationSettings(
        provider=cast(Any, provider), model=cast(Any, model), voice_id=voice_id
    )


@pytest.mark.parametrize(
    ("saved", "rules", "expected"),
    [
        # Paid plans allow every voice.
        (voice("voicevox", "voicevox", "3"), None, voice("voicevox", "voicevox", "3")),
        # An allowed voice is kept.
        (
            voice("google", "standard", "ja-JP-Standard-C"),
            FREE_PLAN_VOICES,
            voice("google", "standard", "ja-JP-Standard-C"),
        ),
        # Another voice falls back to an allowed one in its language and gender.
        (
            voice("google", "neural", "ja-JP-Neural2-C"),
            FREE_PLAN_VOICES,
            voice("google", "standard", "ja-JP-Standard-C"),
        ),
        (
            voice("voicevox", "voicevox", "3"),
            FREE_PLAN_VOICES,
            voice("google", "standard", "ja-JP-Standard-A"),
        ),
        # With no allowed voice of its gender, any in its language.
        (
            voice("google", "standard", "en-US-Casual-K"),
            FREE_PLAN_VOICES,
            voice("google", "standard", "en-US-Standard-C"),
        ),
        # No allowed voice in its language, or no language at all: US English.
        (
            voice("google", "chirp", "sw-KE-Chirp3-HD-Achird"),
            FREE_PLAN_VOICES,
            voice("google", "standard", "en-US-Standard-C"),
        ),
        (
            voice("openai", "tts-1", "alloy"),
            FREE_PLAN_VOICES,
            voice("google", "standard", "en-US-Standard-C"),
        ),
        # A plan that allows no voices.
        (voice("google", "neural", "ja-JP-Neural2-C"), [], None),
    ],
)
def test_plan_voice(
    saved: TTSGenerationSettings,
    rules: Optional[list[Any]],
    expected: Optional[TTSGenerationSettings],
) -> None:
    assert plan_voice(saved, rules, CATALOG) == expected
