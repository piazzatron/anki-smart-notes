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

from yoyo import step

# The Google catalog now offers only Standard and Chirp 3 HD voices. Each retired
# voice moves to one in its locale, of its gender where there is one: the
# premium families (WaveNet, Neural2, Chirp HD) to Chirp 3 HD, or Standard where
# the locale has no Chirp 3 HD, and the ones billed as Standard (Casual, News,
# Journey, Polyglot) to Standard. That includes the old default, en-US-Casual-K.
# Standard and Chirp 3 HD voices Google no longer lists (still synthesizing, or
# gone like ru-RU-Chirp3-HD-Achernar) move to a listed voice of the same family.
RETIRED_GOOGLE_VOICES = {
    "am-ET-Wavenet-A": ("standard", "am-ET-Standard-A"),
    "am-ET-Wavenet-B": ("standard", "am-ET-Standard-B"),
    "ar-XA-Wavenet-A": ("chirp", "ar-XA-Chirp3-HD-Achernar"),
    "ar-XA-Wavenet-B": ("chirp", "ar-XA-Chirp3-HD-Achird"),
    "bg-BG-Standard-A": ("standard", "bg-BG-Standard-B"),
    "bn-IN-Wavenet-A": ("chirp", "bn-IN-Chirp3-HD-Achernar"),
    "bn-IN-Wavenet-B": ("chirp", "bn-IN-Chirp3-HD-Achird"),
    "ca-ES-Standard-A": ("standard", "ca-ES-Standard-B"),
    "cmn-CN-Wavenet-A": ("chirp", "cmn-CN-Chirp3-HD-Achernar"),
    "cmn-CN-Wavenet-B": ("chirp", "cmn-CN-Chirp3-HD-Achird"),
    "cmn-TW-Wavenet-A": ("standard", "cmn-TW-Standard-A"),
    "cmn-TW-Wavenet-B": ("standard", "cmn-TW-Standard-B"),
    "cs-CZ-Standard-A": ("standard", "cs-CZ-Standard-B"),
    "cs-CZ-Wavenet-A": ("chirp", "cs-CZ-Chirp3-HD-Achernar"),
    "da-DK-Neural2-D": ("chirp", "da-DK-Chirp3-HD-Achernar"),
    "da-DK-Standard-A": ("standard", "da-DK-Standard-F"),
    "da-DK-Standard-C": ("standard", "da-DK-Standard-G"),
    "da-DK-Wavenet-A": ("chirp", "da-DK-Chirp3-HD-Achernar"),
    "da-DK-Wavenet-C": ("chirp", "da-DK-Chirp3-HD-Achird"),
    "de-DE-Chirp-HD-D": ("chirp", "de-DE-Chirp3-HD-Achird"),
    "de-DE-Chirp-HD-F": ("chirp", "de-DE-Chirp3-HD-Achernar"),
    "de-DE-Neural2-A": ("chirp", "de-DE-Chirp3-HD-Achernar"),
    "de-DE-Neural2-B": ("chirp", "de-DE-Chirp3-HD-Achird"),
    "de-DE-Polyglot-1": ("standard", "de-DE-Standard-G"),
    "de-DE-Standard-A": ("standard", "de-DE-Standard-G"),
    "de-DE-Wavenet-A": ("chirp", "de-DE-Chirp3-HD-Achernar"),
    "de-DE-Wavenet-B": ("chirp", "de-DE-Chirp3-HD-Achird"),
    "el-GR-Standard-A": ("standard", "el-GR-Standard-B"),
    "el-GR-Wavenet-A": ("chirp", "el-GR-Chirp3-HD-Achernar"),
    "en-AU-Chirp-HD-D": ("chirp", "en-AU-Chirp3-HD-Achird"),
    "en-AU-Chirp-HD-F": ("chirp", "en-AU-Chirp3-HD-Achernar"),
    "en-AU-Neural2-A": ("chirp", "en-AU-Chirp3-HD-Achernar"),
    "en-AU-Neural2-B": ("chirp", "en-AU-Chirp3-HD-Achird"),
    "en-AU-News-E": ("standard", "en-AU-Standard-A"),
    "en-AU-News-G": ("standard", "en-AU-Standard-B"),
    "en-AU-Wavenet-A": ("chirp", "en-AU-Chirp3-HD-Achernar"),
    "en-AU-Wavenet-B": ("chirp", "en-AU-Chirp3-HD-Achird"),
    "en-GB-Chirp-HD-D": ("chirp", "en-GB-Chirp3-HD-Achird"),
    "en-GB-Chirp-HD-F": ("chirp", "en-GB-Chirp3-HD-Achernar"),
    "en-GB-Neural2-A": ("chirp", "en-GB-Chirp3-HD-Achernar"),
    "en-GB-Neural2-B": ("chirp", "en-GB-Chirp3-HD-Achird"),
    "en-GB-News-G": ("standard", "en-GB-Standard-A"),
    "en-GB-News-J": ("standard", "en-GB-Standard-B"),
    "en-GB-Wavenet-A": ("chirp", "en-GB-Chirp3-HD-Achernar"),
    "en-GB-Wavenet-B": ("chirp", "en-GB-Chirp3-HD-Achird"),
    "en-IN-Chirp-HD-D": ("chirp", "en-IN-Chirp3-HD-Achird"),
    "en-IN-Chirp-HD-F": ("chirp", "en-IN-Chirp3-HD-Achernar"),
    "en-IN-Neural2-A": ("chirp", "en-IN-Chirp3-HD-Achernar"),
    "en-IN-Neural2-B": ("chirp", "en-IN-Chirp3-HD-Achird"),
    "en-IN-Wavenet-A": ("chirp", "en-IN-Chirp3-HD-Achernar"),
    "en-IN-Wavenet-B": ("chirp", "en-IN-Chirp3-HD-Achird"),
    "en-US-Casual-K": ("standard", "en-US-Standard-A"),
    "en-US-Journey-F": ("standard", "en-US-Standard-C"),
    "en-US-Neural2-A": ("chirp", "en-US-Chirp3-HD-Achird"),
    "en-US-Neural2-C": ("chirp", "en-US-Chirp3-HD-Achernar"),
    "en-US-Wavenet-A": ("chirp", "en-US-Chirp3-HD-Achird"),
    "en-US-Wavenet-C": ("chirp", "en-US-Chirp3-HD-Achernar"),
    "es-ES-Chirp-HD-D": ("chirp", "es-ES-Chirp3-HD-Achird"),
    "es-ES-Chirp-HD-F": ("chirp", "es-ES-Chirp3-HD-Achernar"),
    "es-ES-Neural2-A": ("chirp", "es-ES-Chirp3-HD-Achernar"),
    "es-ES-Neural2-B": ("chirp", "es-ES-Chirp3-HD-Achird"),
    "es-ES-Polyglot-1": ("standard", "es-ES-Standard-F"),
    "es-ES-Standard-A": ("standard", "es-ES-Standard-F"),
    "es-ES-Wavenet-B": ("chirp", "es-ES-Chirp3-HD-Achird"),
    "es-ES-Wavenet-C": ("chirp", "es-ES-Chirp3-HD-Achernar"),
    "es-US-Chirp-HD-D": ("chirp", "es-US-Chirp3-HD-Achird"),
    "es-US-Chirp-HD-F": ("chirp", "es-US-Chirp3-HD-Achernar"),
    "es-US-Neural2-A": ("chirp", "es-US-Chirp3-HD-Achernar"),
    "es-US-Neural2-B": ("chirp", "es-US-Chirp3-HD-Achird"),
    "es-US-News-D": ("standard", "es-US-Standard-B"),
    "es-US-News-F": ("standard", "es-US-Standard-A"),
    "es-US-Wavenet-A": ("chirp", "es-US-Chirp3-HD-Achernar"),
    "es-US-Wavenet-B": ("chirp", "es-US-Chirp3-HD-Achird"),
    "eu-ES-Standard-A": ("standard", "eu-ES-Standard-B"),
    "fi-FI-Standard-A": ("standard", "fi-FI-Standard-B"),
    "fi-FI-Wavenet-A": ("chirp", "fi-FI-Chirp3-HD-Achernar"),
    "fil-PH-Wavenet-A": ("standard", "fil-PH-Standard-A"),
    "fil-PH-Wavenet-C": ("standard", "fil-PH-Standard-C"),
    "fil-ph-Neural2-A": ("standard", "fil-PH-Standard-A"),
    "fil-ph-Neural2-D": ("standard", "fil-PH-Standard-C"),
    "fr-CA-Chirp-HD-D": ("chirp", "fr-CA-Chirp3-HD-Achird"),
    "fr-CA-Chirp-HD-F": ("chirp", "fr-CA-Chirp3-HD-Achernar"),
    "fr-CA-Neural2-A": ("chirp", "fr-CA-Chirp3-HD-Achernar"),
    "fr-CA-Neural2-B": ("chirp", "fr-CA-Chirp3-HD-Achird"),
    "fr-CA-Wavenet-A": ("chirp", "fr-CA-Chirp3-HD-Achernar"),
    "fr-CA-Wavenet-B": ("chirp", "fr-CA-Chirp3-HD-Achird"),
    "fr-FR-Chirp-HD-D": ("chirp", "fr-FR-Chirp3-HD-Achird"),
    "fr-FR-Chirp-HD-F": ("chirp", "fr-FR-Chirp3-HD-Achernar"),
    "fr-FR-Neural2-A": ("chirp", "fr-FR-Chirp3-HD-Achernar"),
    "fr-FR-Neural2-B": ("chirp", "fr-FR-Chirp3-HD-Achird"),
    "fr-FR-Polyglot-1": ("standard", "fr-FR-Standard-F"),
    "fr-FR-Standard-A": ("standard", "fr-FR-Standard-F"),
    "fr-FR-Wavenet-A": ("chirp", "fr-FR-Chirp3-HD-Achernar"),
    "fr-FR-Wavenet-B": ("chirp", "fr-FR-Chirp3-HD-Achird"),
    "gl-ES-Standard-A": ("standard", "gl-ES-Standard-B"),
    "gu-IN-Wavenet-A": ("chirp", "gu-IN-Chirp3-HD-Achernar"),
    "gu-IN-Wavenet-B": ("chirp", "gu-IN-Chirp3-HD-Achird"),
    "he-IL-Wavenet-A": ("chirp", "he-IL-Chirp3-HD-Achernar"),
    "he-IL-Wavenet-B": ("chirp", "he-IL-Chirp3-HD-Achird"),
    "hi-IN-Neural2-A": ("chirp", "hi-IN-Chirp3-HD-Achernar"),
    "hi-IN-Neural2-B": ("chirp", "hi-IN-Chirp3-HD-Achird"),
    "hi-IN-Wavenet-A": ("chirp", "hi-IN-Chirp3-HD-Achernar"),
    "hi-IN-Wavenet-B": ("chirp", "hi-IN-Chirp3-HD-Achird"),
    "hu-HU-Standard-A": ("standard", "hu-HU-Standard-B"),
    "hu-HU-Wavenet-A": ("chirp", "hu-HU-Chirp3-HD-Achernar"),
    "id-ID-Wavenet-A": ("chirp", "id-ID-Chirp3-HD-Achernar"),
    "id-ID-Wavenet-B": ("chirp", "id-ID-Chirp3-HD-Achird"),
    "is-IS-Standard-A": ("standard", "is-IS-Standard-B"),
    "it-IT-Chirp-HD-D": ("chirp", "it-IT-Chirp3-HD-Achird"),
    "it-IT-Chirp-HD-F": ("chirp", "it-IT-Chirp3-HD-Achernar"),
    "it-IT-Neural2-A": ("chirp", "it-IT-Chirp3-HD-Achernar"),
    "it-IT-Neural2-C": ("chirp", "it-IT-Chirp3-HD-Achird"),
    "it-IT-Standard-A": ("standard", "it-IT-Standard-E"),
    "it-IT-Standard-C": ("standard", "it-IT-Standard-F"),
    "it-IT-Wavenet-A": ("chirp", "it-IT-Chirp3-HD-Achernar"),
    "it-IT-Wavenet-C": ("chirp", "it-IT-Chirp3-HD-Achird"),
    "ja-JP-Neural2-B": ("chirp", "ja-JP-Chirp3-HD-Achernar"),
    "ja-JP-Neural2-C": ("chirp", "ja-JP-Chirp3-HD-Achird"),
    "ja-JP-Wavenet-A": ("chirp", "ja-JP-Chirp3-HD-Achernar"),
    "ja-JP-Wavenet-C": ("chirp", "ja-JP-Chirp3-HD-Achird"),
    "kn-IN-Wavenet-A": ("chirp", "kn-IN-Chirp3-HD-Achernar"),
    "kn-IN-Wavenet-B": ("chirp", "kn-IN-Chirp3-HD-Achird"),
    "ko-KR-Neural2-A": ("chirp", "ko-KR-Chirp3-HD-Achernar"),
    "ko-KR-Neural2-C": ("chirp", "ko-KR-Chirp3-HD-Achird"),
    "ko-KR-Wavenet-A": ("chirp", "ko-KR-Chirp3-HD-Achernar"),
    "ko-KR-Wavenet-C": ("chirp", "ko-KR-Chirp3-HD-Achird"),
    "lt-LT-Standard-A": ("standard", "lt-LT-Standard-B"),
    "lv-LV-Standard-A": ("standard", "lv-LV-Standard-B"),
    "ml-IN-Wavenet-A": ("chirp", "ml-IN-Chirp3-HD-Achernar"),
    "ml-IN-Wavenet-B": ("chirp", "ml-IN-Chirp3-HD-Achird"),
    "mr-IN-Wavenet-A": ("chirp", "mr-IN-Chirp3-HD-Achernar"),
    "mr-IN-Wavenet-B": ("chirp", "mr-IN-Chirp3-HD-Achird"),
    "ms-MY-Wavenet-A": ("standard", "ms-MY-Standard-A"),
    "ms-MY-Wavenet-B": ("standard", "ms-MY-Standard-B"),
    "nb-NO-Standard-A": ("standard", "nb-NO-Standard-F"),
    "nb-NO-Standard-B": ("standard", "nb-NO-Standard-G"),
    "nb-NO-Wavenet-A": ("chirp", "nb-NO-Chirp3-HD-Achernar"),
    "nb-NO-Wavenet-B": ("chirp", "nb-NO-Chirp3-HD-Achird"),
    "nl-BE-Standard-A": ("standard", "nl-BE-Standard-C"),
    "nl-BE-Standard-B": ("standard", "nl-BE-Standard-D"),
    "nl-BE-Wavenet-A": ("chirp", "nl-BE-Chirp3-HD-Achernar"),
    "nl-BE-Wavenet-B": ("chirp", "nl-BE-Chirp3-HD-Achird"),
    "nl-NL-Standard-A": ("standard", "nl-NL-Standard-F"),
    "nl-NL-Standard-B": ("standard", "nl-NL-Standard-G"),
    "nl-NL-Wavenet-A": ("chirp", "nl-NL-Chirp3-HD-Achernar"),
    "nl-NL-Wavenet-B": ("chirp", "nl-NL-Chirp3-HD-Achird"),
    "pa-IN-Wavenet-A": ("chirp", "pa-IN-Chirp3-HD-Achernar"),
    "pa-IN-Wavenet-B": ("chirp", "pa-IN-Chirp3-HD-Achird"),
    "pl-PL-Standard-A": ("standard", "pl-PL-Standard-F"),
    "pl-PL-Standard-B": ("standard", "pl-PL-Standard-G"),
    "pl-PL-Wavenet-A": ("chirp", "pl-PL-Chirp3-HD-Achernar"),
    "pl-PL-Wavenet-B": ("chirp", "pl-PL-Chirp3-HD-Achird"),
    "pt-BR-Neural2-A": ("chirp", "pt-BR-Chirp3-HD-Achernar"),
    "pt-BR-Neural2-B": ("chirp", "pt-BR-Chirp3-HD-Achird"),
    "pt-BR-Wavenet-A": ("chirp", "pt-BR-Chirp3-HD-Achernar"),
    "pt-BR-Wavenet-B": ("chirp", "pt-BR-Chirp3-HD-Achird"),
    "pt-PT-Standard-A": ("standard", "pt-PT-Standard-E"),
    "pt-PT-Standard-B": ("standard", "pt-PT-Standard-F"),
    "pt-PT-Wavenet-A": ("standard", "pt-PT-Standard-E"),
    "pt-PT-Wavenet-B": ("standard", "pt-PT-Standard-F"),
    "ro-RO-Standard-A": ("standard", "ro-RO-Standard-B"),
    "ro-RO-Wavenet-A": ("chirp", "ro-RO-Chirp3-HD-Achernar"),
    "ru-RU-Chirp3-HD-Achernar": ("chirp", "ru-RU-Chirp3-HD-Kore"),
    "ru-RU-Chirp3-HD-Achird": ("chirp", "ru-RU-Chirp3-HD-Fenrir"),
    "ru-RU-Wavenet-A": ("chirp", "ru-RU-Chirp3-HD-Kore"),
    "ru-RU-Wavenet-B": ("chirp", "ru-RU-Chirp3-HD-Fenrir"),
    "sk-SK-Standard-A": ("standard", "sk-SK-Standard-B"),
    "sk-SK-Wavenet-A": ("chirp", "sk-SK-Chirp3-HD-Achernar"),
    "sr-RS-Standard-A": ("standard", "sr-RS-Standard-B"),
    "sv-SE-Wavenet-A": ("chirp", "sv-SE-Chirp3-HD-Achernar"),
    "sv-SE-Wavenet-C": ("chirp", "sv-SE-Chirp3-HD-Achird"),
    "ta-IN-Wavenet-A": ("chirp", "ta-IN-Chirp3-HD-Achernar"),
    "ta-IN-Wavenet-B": ("chirp", "ta-IN-Chirp3-HD-Achird"),
    "th-TH-Neural2-C": ("chirp", "th-TH-Chirp3-HD-Achernar"),
    "tr-TR-Wavenet-A": ("chirp", "tr-TR-Chirp3-HD-Achernar"),
    "tr-TR-Wavenet-B": ("chirp", "tr-TR-Chirp3-HD-Achird"),
    "uk-UA-Standard-A": ("standard", "uk-UA-Standard-B"),
    "uk-UA-Wavenet-A": ("chirp", "uk-UA-Chirp3-HD-Achernar"),
    "ur-IN-Wavenet-A": ("chirp", "ur-IN-Chirp3-HD-Achernar"),
    "ur-IN-Wavenet-B": ("chirp", "ur-IN-Chirp3-HD-Achird"),
    "vi-VN-Neural2-A": ("chirp", "vi-VN-Chirp3-HD-Achernar"),
    "vi-VN-Neural2-D": ("chirp", "vi-VN-Chirp3-HD-Achird"),
    "vi-VN-Wavenet-A": ("chirp", "vi-VN-Chirp3-HD-Achernar"),
    "vi-VN-Wavenet-B": ("chirp", "vi-VN-Chirp3-HD-Achird"),
}


def _remap(table: str, extra_where: str) -> str:
    models = " ".join(
        f"WHEN '{old}' THEN '{model}'"
        for old, (model, _) in RETIRED_GOOGLE_VOICES.items()
    )
    voices = " ".join(
        f"WHEN '{old}' THEN '{new}'" for old, (_, new) in RETIRED_GOOGLE_VOICES.items()
    )
    retired = ", ".join(f"'{old}'" for old in RETIRED_GOOGLE_VOICES)
    return f"""
        UPDATE {table}
        SET model = CASE voice_id {models} END,
            voice_id = CASE voice_id {voices} END
        WHERE provider = 'google' AND voice_id IN ({retired}){extra_where};
    """


steps = [
    step(_remap("default_tts_generation_settings", ""), "SELECT 1;"),
    step(
        _remap("tts_smart_field_settings", " AND uses_default_generation_settings = 0"),
        "SELECT 1;",
    ),
]
