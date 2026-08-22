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

from pathlib import Path
from typing import get_args

import pytest

import src.ui.i18n as native_i18n
from src.ui.i18n import NativeActionKey
from src.ui.native_action_translations import NATIVE_ACTION_TRANSLATIONS


@pytest.mark.parametrize(
    ("requested_locale", "expected_catalog"),
    [
        ("en_US", "en"),
        ("JA_jp", "ja"),
        ("pt_BR", "pt-BR"),
        ("pt-PT", "pt-PT"),
        ("es_MX", "es"),
        ("unsupported", "en"),
    ],
)
def test_native_action_text_matches_anki_locale(
    monkeypatch: pytest.MonkeyPatch,
    requested_locale: str,
    expected_catalog: str,
) -> None:
    monkeypatch.setattr(native_i18n.lang, "current_lang", requested_locale)

    assert (
        native_i18n.native_action_text("open_smart_notes")
        == NATIVE_ACTION_TRANSLATIONS[expected_catalog]["open_smart_notes"]
    )


def test_native_action_catalogs_match_web_locales() -> None:
    locale_directory = (
        Path(__file__).parents[1] / "web" / "src" / "lib" / "i18n" / "locales"
    )
    web_locales = {path.stem for path in locale_directory.glob("*.json")}

    assert set(NATIVE_ACTION_TRANSLATIONS) == web_locales


def test_native_action_catalogs_are_complete_and_preserve_product_terms() -> None:
    english_keys = set(NATIVE_ACTION_TRANSLATIONS["en"])
    assert english_keys == set(get_args(NativeActionKey))

    for catalog in NATIVE_ACTION_TRANSLATIONS.values():
        assert set(catalog) == english_keys
        assert all(catalog.values())
        assert "Smart Notes" in catalog["open_smart_notes"]
        assert "Smart Fields" in catalog["generate_smart_fields"]
        assert "Smart Field" in catalog["generate_smart_field"]
        assert "TTS" in catalog["custom_tts"]
