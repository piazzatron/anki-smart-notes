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
from typing import Dict, List, Literal, TypedDict, Union

from aqt import (
    QAbstractListModel,
    QGroupBox,
    QHBoxLayout,
    QItemSelection,
    QItemSelectionModel,
    QListView,
    QModelIndex,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    Qt,
    QVBoxLayout,
    QWidget,
)

from ..config import config
from ..logger import logger
from ..models import TTSProviders
from ..sentry import run_async_in_background_with_sentry
from ..tts_provider import TTSProvider
from ..tts_utils import play_audio
from ..utils import load_file
from .reactive_combo_box import ReactiveComboBox
from .reactive_edit_text import ReactiveEditText
from .state_manager import StateManager
from .ui_utils import default_form_layout, show_message_box

ALL: Literal["All"] = "All"

AllTTSProviders = Union[Literal["All"], TTSProviders]

Gender = Literal["All", "Male", "Female"]
default_texts: Dict[str, str] = {
    ALL: "I'm sorry Dave, I'm afraid I can't do that.",
}

price_tier_copy = {
    "standard": "Standard Quality",
    "best": "Good Quality",
    "premium": "Premium Quality",
    "ultra-premium": "Ultra Premium Quality",
}


class TTSMeta(TypedDict):
    tts_provider: TTSProviders
    voice: str
    model: str
    friendly_voice: str
    gender: Literal["Male", "Female", "All"]
    language: str
    price_tier: Literal["standard", "best", "premium", "ultra-premium"]


class TTSState(TypedDict):
    # Combo box fields

    providers: List[AllTTSProviders]
    selected_provider: AllTTSProviders
    genders: List[Gender]
    selected_gender: Gender
    languages: List[str]
    selected_language: str

    voice: str

    # These are the actual values read from and written to config
    tts_provider: Union[TTSProviders, None]
    tts_voice: Union[str, None]
    tts_model: Union[str, None]

    test_text: str
    test_enabled: bool


openai_voices: List[TTSMeta] = [
    {
        "tts_provider": "openai",
        "voice": "alloy",
        "model": "tts-1",
        "friendly_voice": "alloy",
        "gender": "Female",
        "language": ALL,
        "price_tier": "best",
    },
    {
        "tts_provider": "openai",
        "voice": "echo",
        "model": "tts-1",
        "friendly_voice": "echo",
        "gender": "Male",
        "language": ALL,
        "price_tier": "best",
    },
    {
        "tts_provider": "openai",
        "voice": "fable",
        "model": "tts-1",
        "friendly_voice": "fable",
        "gender": "Female",
        "language": ALL,
        "price_tier": "best",
    },
    {
        "tts_provider": "openai",
        "voice": "onyx",
        "model": "tts-1",
        "friendly_voice": "onyx",
        "gender": "Male",
        "language": ALL,
        "price_tier": "best",
    },
    {
        "tts_provider": "openai",
        "voice": "nova",
        "model": "tts-1",
        "friendly_voice": "nova",
        "gender": "Female",
        "language": ALL,
        "price_tier": "best",
    },
    {
        "tts_provider": "openai",
        "voice": "shimmer",
        "model": "tts-1",
        "friendly_voice": "shimmer",
        "gender": "Female",
        "language": ALL,
        "price_tier": "best",
    },
]


class GoogleVoice(TypedDict):
    gender: Literal["Male", "Female"]
    languageCode: str
    language: str
    name: str
    type: Literal["Standard", "Wavenet", "Neural"]


def get_google_voices() -> List[TTSMeta]:
    s = load_file("google_voices.json")
    google_voices: List[GoogleVoice] = json.loads(s)
    voices: List[TTSMeta] = []
    tiers = {"Standard": "standard", "Wavenet": "best", "Neural": "best"}
    for voice in google_voices:
        voices.append(
            {
                "tts_provider": "google",
                "language": voice["language"],
                "gender": voice["gender"],
                "voice": voice["name"],
                "model": voice["type"].lower(),
                "friendly_voice": f'{voice["language"].capitalize()} - {voice["gender"].capitalize()}',
                "price_tier": tiers[voice["type"]],  # type: ignore
            }
        )
    return voices


def get_eleven_voices() -> List[TTSMeta]:
    s = load_file("eleven_voices.json")
    eleven_voices = json.loads(s)
    voices: List[TTSMeta] = []
    for voice in eleven_voices:
        premium: TTSMeta = {
            "tts_provider": "elevenLabs",
            "language": voice["language"],
            "voice": voice["voice_id"],
            "model": "eleven_turbo_v2_5",
            "friendly_voice": f'{voice["language"].capitalize()} - {voice["gender"].capitalize()} - {voice["name"].capitalize()}',
            "gender": voice["gender"],
            "price_tier": "premium",
        }
        ultra_premium = premium.copy()
        ultra_premium["model"] = "eleven_multilingual_v2"
        ultra_premium["price_tier"] = "ultra-premium"
        voices.extend([premium, ultra_premium])

    return voices


# Combine all voices
voices = get_google_voices() + openai_voices + get_eleven_voices()

languages: List[str] = [ALL] + sorted(
    list(set([voice["language"] for voice in voices]) - {ALL})
)
providers: List[AllTTSProviders] = [ALL, "google", "openai", "elevenLabs"]


class CustomListModel(QAbstractListModel):
    def __init__(self, data: List[TTSMeta]):
        super().__init__()
        self._data = data

    def data(self, index, role):  # type: ignore
        if role == Qt.ItemDataRole.DisplayRole:
            return self.create_str(index.row())

    def rowCount(self, _: QModelIndex) -> int:  # type: ignore
        return len(self._data)

    def create_str(self, row: int) -> str:
        data = self._data[row]
        return f'{data["tts_provider"].capitalize()} - {data["friendly_voice"].capitalize()} ({price_tier_copy[data["price_tier"]]})'

    def update_data(self, new_data: List[TTSMeta]):
        self.beginResetModel()
        self._data = new_data
        self.endResetModel()


class TTSOptions(QWidget):
    def __init__(self, state: Union[StateManager[TTSState], None] = None):
        super().__init__()

        self.state = (
            state if state else StateManager[TTSState](self.get_initial_state())
        )
        self.setup_ui()

    def setup_ui(self) -> None:

        self.voices_list = QListView()
        self.voices_models = CustomListModel(self.get_visible_voice_filters())
        self.voices_list.setModel(self.voices_models)

        layout = QVBoxLayout()
        top_row = QWidget()
        top_row_layout = QHBoxLayout()
        top_row_layout.setContentsMargins(0, 0, 0, 0)
        top_row.setLayout(top_row_layout)
        top_row_layout.addWidget(self.render_filters())
        top_row_layout.addWidget(self.render_voices_list())
        layout.addWidget(top_row)
        layout.addSpacerItem(QSpacerItem(0, 12))
        layout.addWidget(self.render_test_voice())
        self.state.state_changed.connect(self.update_ui)
        self.update_ui()

        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def render_filters(self) -> QWidget:
        filters_box = QGroupBox("Filter Voice List")
        filters_layout = default_form_layout()
        filters_box.setLayout(filters_layout)

        language = ReactiveComboBox(self.state, "languages", "selected_language")
        language.onChange.connect(
            lambda langauge: self.state.update(
                {"test_text": default_texts.get(langauge, default_texts[ALL])}
            )
        )
        gender = ReactiveComboBox(self.state, "genders", "selected_gender")
        provider = ReactiveComboBox(self.state, "providers", "selected_provider")

        filters_layout.addRow("Language:", language)
        filters_layout.addRow("Gender:", gender)
        filters_layout.addRow("Provider:", provider)

        return filters_box

    def render_voices_list(self) -> QWidget:
        voice_box = QGroupBox(f"🗣️ Voices ({len(voices)})")
        voice_box_layout = QVBoxLayout()
        voice_box.setLayout(voice_box_layout)
        voice_box_layout.setContentsMargins(0, 0, 0, 0)
        self.voices_list = QListView()
        self.voices_models = CustomListModel(self.get_visible_voice_filters())
        self.voices_list.setModel(self.voices_models)
        selection_model = self.voices_list.selectionModel()
        if selection_model:
            selection_model.selectionChanged.connect(self.voice_did_change)
        voice_box_layout.addWidget(self.voices_list)
        return voice_box

    def voice_did_change(self, selected: QItemSelection):
        indexes = selected.indexes()
        if indexes:
            selected_index = indexes[0]
            selected_voice = self.voices_models._data[selected_index.row()]
            logger.debug(f"Selected voice: {selected_voice}")
            self.state.update(
                {
                    "voice": selected_voice["voice"],
                    "tts_provider": selected_voice["tts_provider"],
                    "tts_voice": selected_voice["voice"],
                    "tts_model": selected_voice["model"],
                }
            )
            # TODO: do I need to call this?
            self.voices_list.update()

    def update_ui(self) -> None:
        self.update_list_ui()
        self.test_button.setEnabled(self.state.s["test_enabled"])

    def update_list_ui(self) -> None:
        """Handle updating the list and preserving selection"""
        # Store the selection state
        voice = self.state.s.get("tts_voice")
        provider = self.state.s.get("tts_provider")
        model = self.state.s.get("tts_model")
        if not (voice and provider):
            return

        selection_model = self.voices_list.selectionModel()
        if not selection_model:
            return

        selected_voice = next(
            (
                v
                for v in voices
                if v["voice"] == voice
                and v["tts_provider"] == provider
                and v["model"] == model
            ),
            None,
        )
        if not selected_voice:
            return

        self.voices_models.update_data(self.get_visible_voice_filters())

        # Get the new location after updating
        voice_location = (
            self.voices_models._data.index(selected_voice)
            if selected_voice and selected_voice in self.voices_models._data
            else None
        )

        # Restore selection
        # Sneaky: it can be 0
        if voice_location is not None:
            selection_model.select(
                self.voices_models.index(voice_location, 0, QModelIndex()),
                QItemSelectionModel.SelectionFlag.Select,
            )

        if provider == "elevenLabs" and not config.did_show_premium_tts_dialog:
            show_message_box(
                "Heads up: you've selected a premium voice. These voices are extremely high quality and can exhaust a small plan extremely quickly!"
            )
            config.did_show_premium_tts_dialog = True

    def render_test_voice(self) -> QWidget:
        box = QGroupBox("Test Voice 🔈")
        layout = QHBoxLayout()
        edit_text = ReactiveEditText(self.state, "test_text")
        edit_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        edit_text.setFixedHeight(26)
        edit_text.onChange.connect(lambda text: self.state.update({"test_text": text}))
        self.test_button = QPushButton("Test")
        self.test_button.clicked.connect(self.test_and_play)
        layout.addWidget(edit_text)
        layout.addWidget(self.test_button)

        box.setLayout(layout)

        return box

    def test_and_play(self) -> None:

        def on_success(audio: bytes):
            play_audio(audio)
            self.state.update({"test_enabled": True})

        provider = self.state.s["tts_provider"]
        voice = self.state.s["tts_voice"]
        model = self.state.s["tts_model"]
        if not (provider and voice):
            return

        def on_failure(err):
            show_message_box(f"Something went wrong testing audio: {err}")
            self.state.update({"test_enabled": True})

        async def fetch_audio() -> bytes:
            tts_provider = TTSProvider()
            resp = await tts_provider.async_get_tts_response(
                input=self.state.s["test_text"],
                model=model,
                provider=provider,
                voice=voice,
            )
            return resp

        self.state.update({"test_enabled": False})
        run_async_in_background_with_sentry(
            fetch_audio, on_success=on_success, on_failure=on_failure
        )

    def get_visible_voice_filters(self) -> List[TTSMeta]:
        filtered = []
        for voice in voices:
            matches_provider = (
                self.state.s["selected_provider"] == ALL
                or voice["tts_provider"] == self.state.s["selected_provider"]
            )
            matches_gender = (
                self.state.s["selected_gender"] == ALL
                or voice["gender"] == self.state.s["selected_gender"]
            )
            matches_language = (
                self.state.s["selected_language"] == ALL
                or voice["language"]
                == ALL  # Or maybe don't want generic ones to appear?
                or voice["language"] == self.state.s["selected_language"]
            )
            if matches_provider and matches_gender and matches_language:
                filtered.append(voice)
        return filtered

    def get_initial_state(self) -> TTSState:
        return {
            "providers": providers,
            "selected_provider": ALL,
            "voice": config.tts_voice,
            "genders": [ALL, "Male", "Female"],
            "selected_gender": ALL,
            "languages": languages,
            "selected_language": ALL,
            "test_text": default_texts[ALL],
            "test_enabled": True,
            "tts_provider": config.tts_provider,
            "tts_voice": config.tts_voice,
            "tts_model": config.tts_model,
        }
