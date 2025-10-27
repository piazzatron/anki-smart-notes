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
from typing import Literal, Optional, TypedDict, Union, cast

from aqt import (
    QAbstractListModel,
    QGroupBox,
    QHBoxLayout,
    QItemSelection,
    QItemSelectionModel,
    QLabel,
    QListView,
    QModelIndex,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    Qt,
    QTimer,
    QVBoxLayout,
    QWidget,
)

from ..config import config, key_or_config_val
from ..logger import logger
from ..models import (
    OverrideableTTSOptionsDict,
    TTSModels,
    TTSProviders,
    overridable_tts_options,
)
from ..sentry import run_async_in_background_with_sentry
from ..tts_provider import TTSProvider
from ..tts_utils import play_audio
from ..utils import load_file, none_defaulting
from .reactive_check_box import ReactiveCheckBox
from .reactive_combo_box import ReactiveComboBox
from .reactive_edit_text import ReactiveEditText
from .reactive_line_edit import ReactiveLineEdit
from .state_manager import StateManager
from .ui_utils import default_form_layout, font_small, show_message_box

ALL: Literal["All"] = "All"

AllTTSProviders = Union[Literal["All"], TTSProviders]

Gender = Literal["All", "Male", "Female"]
default_texts: dict[str, str] = {
    ALL: "I'm sorry Dave, I'm afraid I can't do that.",
}

price_tier_copy = {
    "low": "Low Cost",
    "standard": "Standard Cost",
    "high": "High Cost",
    "ultra-high": "Ultra High Cost",
}

PriceTiers = Literal["low", "standard", "high", "ultra-high"]


class TTSMeta(TypedDict):
    tts_provider: TTSProviders
    voice: str
    model: str
    friendly_voice: str
    gender: Literal["Male", "Female", "All"]
    language: str
    price_tier: PriceTiers


class TTSState(TypedDict):
    # Combo box fields

    providers: list[AllTTSProviders]
    selected_provider: AllTTSProviders
    genders: list[Gender]
    selected_gender: Gender
    languages: list[str]
    selected_language: str

    voice: str

    # These are the actual values read from and written to config
    tts_provider: TTSProviders
    tts_voice: str
    tts_model: TTSModels
    tts_strip_html: bool

    test_text: str
    test_enabled: bool
    search_text: str


openai_voices: list[TTSMeta] = [
    {
        "tts_provider": "openai",
        "voice": "alloy",
        "model": "tts-1",
        "friendly_voice": "alloy",
        "gender": "Female",
        "language": ALL,
        "price_tier": "standard",
    },
    {
        "tts_provider": "openai",
        "voice": "echo",
        "model": "tts-1",
        "friendly_voice": "echo",
        "gender": "Male",
        "language": ALL,
        "price_tier": "standard",
    },
    {
        "tts_provider": "openai",
        "voice": "fable",
        "model": "tts-1",
        "friendly_voice": "fable",
        "gender": "Female",
        "language": ALL,
        "price_tier": "standard",
    },
    {
        "tts_provider": "openai",
        "voice": "onyx",
        "model": "tts-1",
        "friendly_voice": "onyx",
        "gender": "Male",
        "language": ALL,
        "price_tier": "standard",
    },
    {
        "tts_provider": "openai",
        "voice": "nova",
        "model": "tts-1",
        "friendly_voice": "nova",
        "gender": "Female",
        "language": ALL,
        "price_tier": "standard",
    },
    {
        "tts_provider": "openai",
        "voice": "shimmer",
        "model": "tts-1",
        "friendly_voice": "shimmer",
        "gender": "Female",
        "language": ALL,
        "price_tier": "standard",
    },
]


class GoogleVoice(TypedDict):
    gender: Literal["Male", "Female"]
    languageCode: str
    language: str
    name: str
    type: Literal["Standard", "Wavenet", "Neural", "Chirp"]


def get_google_voices() -> list[TTSMeta]:
    s = load_file("google_voices.json", test_override="[]")
    google_voices: list[GoogleVoice] = json.loads(s)
    voices: list[TTSMeta] = []
    tiers = {
        "Standard": "low",
        "Wavenet": "standard",
        "Neural": "standard",
        "Chirp": "standard",
    }
    for voice in google_voices:
        voices.append(
            {
                "tts_provider": "google",
                "language": voice["language"],
                "gender": voice["gender"],
                "voice": voice["name"],
                "model": voice["type"].lower(),
                "friendly_voice": f"{voice['language'].capitalize()} - {voice['gender'].capitalize()} ({voice['type']})",
                "price_tier": tiers[voice["type"]],  # type: ignore
            }
        )
    return voices


def get_eleven_voices() -> list[TTSMeta]:
    s = load_file("eleven_voices.json", test_override="[]")
    eleven_voices = json.loads(s)
    voices: list[TTSMeta] = []

    models: list[dict[str, str]] = [
        {"model": "eleven_v3", "price_tier": "ultra-high"},
        {"model": "eleven_multilingual_v2", "price_tier": "ultra-high"},
        {"model": "eleven_flash_v2_5", "price_tier": "high"},
    ]

    friendly_models = {
        "eleven_v3": "V3",
        "eleven_multilingual_v2": "Multilingual V2",
        "eleven_flash_v2_5": "Flash V2.5",
    }

    for voice in eleven_voices:
        for model in models:
            ttsMeta: TTSMeta = {
                "tts_provider": "elevenLabs",
                "language": voice["language"],
                "voice": voice["voice_id"],
                "model": model["model"],
                "friendly_voice": f"{voice['name'].capitalize()} ({friendly_models[model['model']]})",
                "gender": voice["gender"],
                "price_tier": cast(PriceTiers, model["price_tier"]),
            }

            voices.append(ttsMeta)

    return voices


class AzureVoice(TypedDict):
    name: str
    displayName: str
    locale: str
    language: str
    gender: Literal["Male", "Female"]
    voiceType: Literal["Neural", "NeuralHD"]
    styleList: list[str]
    sampleRateHertz: str


def get_azure_voices() -> list[TTSMeta]:
    s = load_file("azure_voices.json", test_override="[]")
    azure_voices: list[AzureVoice] = json.loads(s)
    voices: list[TTSMeta] = []
    tiers: dict[str, Literal["low", "standard", "high", "ultra-high"]] = {
        "Neural": "standard",
        "NeuralHD": "standard",
    }
    for voice in azure_voices:
        voices.append(
            {
                "tts_provider": "azure",
                "language": voice["language"],
                "gender": voice["gender"],
                "voice": voice["name"],
                "model": voice["voiceType"].lower(),
                "friendly_voice": f"{voice['displayName'].title()} ({voice['voiceType']})",
                "price_tier": tiers[voice["voiceType"]],
            }
        )
    return voices


# Combine all voices
voices = get_google_voices() + openai_voices + get_eleven_voices() + get_azure_voices()

languages: list[str] = [ALL] + sorted({voice["language"] for voice in voices} - {ALL})
providers: list[AllTTSProviders] = [ALL, "google", "openai", "elevenLabs", "azure"]


def format_voice(voice: TTSMeta) -> str:
    language_display = "Multilingual" if voice["language"] == ALL else voice["language"]
    return f"{voice['tts_provider'].capitalize()} - {language_display} - {voice['gender'].capitalize()} - {voice['friendly_voice'].title()} ({price_tier_copy[voice['price_tier']]})"


voice_search_cache: dict[tuple[str, str, str], list[str]] = {
    (v["tts_provider"], v["voice"], v["model"]): format_voice(v).lower().split()
    for v in voices
}


class CustomListModel(QAbstractListModel):
    def __init__(self, data: list[TTSMeta]):
        super().__init__()
        self._data = data

    def data(self, index, role):  # type: ignore
        if role == Qt.ItemDataRole.DisplayRole:
            return self.create_str(index.row())

    def rowCount(self, _: QModelIndex) -> int:  # type: ignore
        return len(self._data)

    def create_str(self, row: int) -> str:
        return format_voice(self._data[row])

    def update_data(self, new_data: list[TTSMeta]):
        self.beginResetModel()
        self._data = new_data
        self.endResetModel()

    def get_data(self) -> list[TTSMeta]:
        return self._data


class SelectedVoiceLabel(QLabel):
    def __init__(self, meta: TTSMeta):
        super().__init__()
        self.update_text(meta)

    def update_text(self, meta: TTSMeta):
        self.setText(f" Current voice: {format_voice(meta)}")
        self.setFont(font_small)


class TTSOptions(QWidget):
    extras_visible: bool

    def __init__(
        self,
        tts_options: Optional[OverrideableTTSOptionsDict] = None,
        extras_visible: bool = True,
    ):
        super().__init__()
        self.extras_visible = extras_visible

        self.state = StateManager[TTSState](self.get_initial_state(tts_options))
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.update_search)
        self.pending_search_text = ""
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

        # This shouldn't ever be none but being defensive
        current_selection = self.voices_list.selectedIndexes()
        selected_voice = self.voices_models.get_data()[
            current_selection[0].row() if current_selection else 0
        ]
        self.selected_voice_label = SelectedVoiceLabel(selected_voice)
        top_row_layout.addWidget(self.render_filters())
        top_row_layout.addWidget(self.render_voices_list())

        layout.addWidget(self.selected_voice_label)
        layout.addSpacerItem(QSpacerItem(0, 12))
        layout.addWidget(top_row)
        layout.addSpacerItem(QSpacerItem(0, 12))
        layout.addWidget(self.render_test_voice())
        layout.addSpacerItem(QSpacerItem(0, 12))
        layout.addWidget(self.render_processing_rules())

        if not self.extras_visible:
            self.test_voice_box.hide()
            self.processing_box.hide()

        self.state.state_changed.connect(self.update_ui)
        self.update_ui()

        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def render_filters(self) -> QWidget:
        filters_box = QGroupBox("Filter Voice List")
        filters_layout = default_form_layout()
        filters_box.setLayout(filters_layout)

        language = ReactiveComboBox(self.state, "languages", "selected_language")
        language.on_change.connect(
            lambda langauge: self.state.update(
                {"test_text": default_texts.get(langauge, default_texts[ALL])}
            )
        )
        gender = ReactiveComboBox(self.state, "genders", "selected_gender")
        provider = ReactiveComboBox(
            self.state,
            "providers",
            "selected_provider",
            render_map={
                "google": "Google",
                "azure": "Azure",
                "openai": "OpenAI",
                "elevenLabs": "ElevenLabs",
            },
        )

        filters_layout.addRow("Language:", language)
        filters_layout.addRow("Gender:", gender)
        filters_layout.addRow("Provider:", provider)

        return filters_box

    def render_voices_list(self) -> QWidget:
        self.voice_box = QGroupBox(f"🗣️ Voices ({len(voices)})")
        voice_box_layout = QVBoxLayout()
        self.voice_box.setLayout(voice_box_layout)

        search_layout = QHBoxLayout()
        search_input = ReactiveLineEdit(self.state, "search_text")
        search_input.setPlaceholderText("🔎 Search Voices")
        search_input.setMinimumHeight(36)
        search_input.setStyleSheet("padding: 0px 8px;")
        search_input.on_change.connect(self.debounced_search)
        search_layout.addWidget(search_input)
        voice_box_layout.addLayout(search_layout)

        self.voices_list = QListView()
        self.voices_models = CustomListModel(self.get_visible_voice_filters())
        self.voices_list.setModel(self.voices_models)
        selection_model = self.voices_list.selectionModel()
        if selection_model:
            selection_model.selectionChanged.connect(self.voice_did_change)
        voice_box_layout.addWidget(self.voices_list)
        return self.voice_box

    def voice_did_change(self, selected: QItemSelection):
        indexes = selected.indexes()
        if indexes:
            selected_index = indexes[0]
            selected_voice = self.voices_models.get_data()[selected_index.row()]
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
            self.selected_voice_label.update_text(selected_voice)

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
        self.voice_box.setTitle(f"🗣️ Voices ({len(self.voices_models.get_data())})")

        # Get the new location after updating
        voice_location = (
            self.voices_models.get_data().index(selected_voice)
            if selected_voice and selected_voice in self.voices_models.get_data()
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
        self.test_voice_box = QGroupBox("🔈Test Voice")
        layout = QHBoxLayout()
        edit_text = ReactiveEditText(self.state, "test_text")
        edit_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        edit_text.setFixedHeight(26)
        edit_text.on_change.connect(lambda text: self.state.update({"test_text": text}))
        self.test_button = QPushButton("Test")
        self.test_button.clicked.connect(self.test_and_play)
        layout.addWidget(edit_text)
        layout.addWidget(self.test_button)

        self.test_voice_box.setLayout(layout)

        return self.test_voice_box

    def render_processing_rules(self) -> QWidget:
        self.processing_box = QGroupBox("⚙️Voice Processing")
        layout = default_form_layout()
        self.processing_box.setLayout(layout)
        strip_html_box = ReactiveCheckBox(self.state, "tts_strip_html")
        layout.addRow("Strip HTML from text before speaking:", strip_html_box)
        return self.processing_box

    def test_and_play(self) -> None:
        def on_success(audio: bytes):
            play_audio(audio)
            self.state.update({"test_enabled": True})

        provider = self.state.s["tts_provider"]
        voice = self.state.s["tts_voice"]
        model = self.state.s["tts_model"]
        if not (provider and voice and model):
            return

        def on_failure(err: Exception):
            show_message_box(f"Something went wrong testing audio: {err}")
            self.state.update({"test_enabled": True})

        async def fetch_audio() -> bytes:
            tts_provider = TTSProvider()
            resp = await tts_provider.async_get_tts_response(
                input=self.state.s["test_text"],
                model=model,
                provider=provider,
                voice=voice,
                strip_html=(none_defaulting(self.state.s, "tts_strip_html", True)),
            )
            return resp

        self.state.update({"test_enabled": False})
        run_async_in_background_with_sentry(
            fetch_audio, on_success=on_success, on_failure=on_failure
        )

    def debounced_search(self, text: str) -> None:
        self.pending_search_text = text
        self.search_timer.stop()
        self.search_timer.start(100)

    def update_search(self) -> None:
        self.state.update({"search_text": self.pending_search_text})

    def get_visible_voice_filters(self) -> list[TTSMeta]:
        filtered = []
        search_terms = self.state.s["search_text"].lower().strip().split()

        for voice in voices:
            matches_provider = (
                self.state.s["selected_provider"] == ALL
                or voice["tts_provider"] == self.state.s["selected_provider"]
            )
            if not matches_provider:
                continue

            matches_gender = (
                self.state.s["selected_gender"] == ALL
                or voice["gender"] == self.state.s["selected_gender"]
            )
            if not matches_gender:
                continue

            matches_language = (
                self.state.s["selected_language"] == ALL
                or voice["language"]
                == ALL  # Or maybe don't want generic ones to appear?
                or voice["language"] == self.state.s["selected_language"]
            )

            if not matches_language:
                continue

            # Search works by splitting the user's input into terms and the formatted
            # voice display text into words. Each search term must match (via substring)
            # at least one word in the voice. All search terms must match for inclusion.
            # The voice_search_cache contains pre-split words from format_voice() output.
            voice_key = (voice["tts_provider"], voice["voice"], voice["model"])
            voice_words = voice_search_cache[voice_key]
            matches_search = not search_terms or all(
                any(term in word for word in voice_words) for term in search_terms
            )
            if not matches_search:
                continue
            filtered.append(voice)
        return filtered

    def get_initial_state(
        self, tts_options: Optional[OverrideableTTSOptionsDict]
    ) -> TTSState:
        ret = {
            "providers": providers,
            "selected_provider": ALL,
            "voice": config.tts_voice,
            "genders": [ALL, "Male", "Female"],
            "selected_gender": ALL,
            "languages": languages,
            "selected_language": ALL,
            "test_text": default_texts[ALL],
            "test_enabled": True,
            "search_text": "",
        }

        for k in overridable_tts_options:
            ret[k] = key_or_config_val(tts_options, k)
        return cast("TTSState", ret)
