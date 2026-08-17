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

from typing import Any, Literal, Optional, TypedDict, Union, cast

from aqt import (
    QAbstractListModel,
    QGridLayout,
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

from ..config import config
from ..logger import logger
from ..models import (
    OverrideableTTSOptionsDict,
    TTSGenerationSettings,
    TTSModels,
    TTSProviders,
    overridable_tts_options,
)
from ..sentry import run_async_in_background_with_sentry
from ..services.smart_field_service import smart_field_service
from ..tts_provider import TTSProvider
from ..tts_utils import play_audio
from ..voice_catalog import ALL_LANGUAGES as ALL, TTSVoice as TTSMeta, get_voice_catalog
from .reactive_combo_box import ReactiveComboBox
from .reactive_edit_text import ReactiveEditText
from .reactive_line_edit import ReactiveLineEdit
from .state_manager import StateManager
from .ui_utils import default_form_layout, font_bold, show_message_box

AllTTSProviders = Union[Literal["All"], TTSProviders]

voices = get_voice_catalog()

Gender = Literal["All", "Male", "Female"]
default_texts: dict[str, str] = {
    ALL: "I'm sorry Dave, I'm afraid I can't do that.",
    "Japanese": "こんにちは、今日はいい天気ですね。",
}

price_tier_copy = {
    "free": "Free",
    "low": "Low Cost",
    "standard": "Standard Cost",
    "high": "High Cost",
    "ultra-high": "Ultra High Cost",
}
TTS_PROVIDER_LABELS = {
    "google": "Google",
    "azure": "Azure",
    "openai": "OpenAI",
    "elevenLabs": "ElevenLabs",
    "voicevox": "VoiceVox",
}


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

    test_text: str
    test_enabled: bool
    search_text: str


languages: list[str] = [ALL] + sorted({voice["language"] for voice in voices} - {ALL})
providers: list[AllTTSProviders] = [
    ALL,
    "google",
    "openai",
    "elevenLabs",
    "azure",
    "voicevox",
]


def _format_voice(voice: TTSMeta) -> str:
    language_display = "Multilingual" if voice["language"] == ALL else voice["language"]
    return f"{voice['provider'].capitalize()} - {language_display} - {voice['gender'].capitalize()} - {voice['name']} ({price_tier_copy[voice['price_tier']]})"


voice_search_cache: dict[tuple[str, str, str], list[str]] = {
    (v["provider"], v["voice_id"], v["model"]): _format_voice(v).lower().split()
    for v in voices
}


def format_tts_voice_label(provider: object, model: object, voice_id: object) -> str:
    matching_voice = next(
        (
            voice
            for voice in voices
            if voice["provider"] == provider
            and voice["model"] == model
            and voice["voice_id"] == voice_id
        ),
        None,
    )

    voice_label = matching_voice["name"] if matching_voice else str(voice_id)
    return f"{TTS_PROVIDER_LABELS.get(str(provider), str(provider))} ({voice_label})"


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
        return _format_voice(self._data[row])

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
        self.setText(f" Current voice: {_format_voice(meta)}")
        self.setFont(font_bold)


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

        # Let TTSOptions soak up all the vertical space the parent tab gives
        # it, so the voices list can grow when the user resizes the dialog.
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout()

        # This shouldn't ever be none but being defensive
        current_selection = self.voices_list.selectedIndexes()
        selected_voice = self.voices_models.get_data()[
            current_selection[0].row() if current_selection else 0
        ]
        self.selected_voice_label = SelectedVoiceLabel(selected_voice)

        # Grid layout with both column-0 (filters) and column-1 (voices)
        # explicitly anchored at row 0, so their tops share the same baseline.
        # The voices panel spans all 4 rows in column 1; the filter sits in
        # row 0 of column 0, a fixed 12 px spacer in row 1, the test voice in
        # row 2, and an Expanding spacer in row 3 absorbs the slack while
        # letting the voices panel grow with the dialog.
        top_row = QWidget()
        top_row.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding
        )
        top_row_grid = QGridLayout()
        top_row_grid.setContentsMargins(0, 0, 0, 0)
        top_row_grid.setVerticalSpacing(0)
        top_row.setLayout(top_row_grid)

        top_row_grid.addWidget(self.render_filters(), 0, 0)
        top_row_grid.addItem(
            QSpacerItem(0, 12, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed),
            1,
            0,
        )
        top_row_grid.addWidget(self.render_test_voice(), 2, 0)
        top_row_grid.addItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding),
            3,
            0,
        )
        top_row_grid.addWidget(self.render_voices_list(), 0, 1, 4, 1)

        top_row_grid.setColumnStretch(0, 1)
        top_row_grid.setColumnStretch(1, 1)

        layout.addWidget(self.selected_voice_label)
        layout.addSpacerItem(QSpacerItem(0, 12))
        layout.addWidget(top_row, 1)

        if not self.extras_visible:
            self.test_voice_box.hide()

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
            render_map=TTS_PROVIDER_LABELS,
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
                    "voice": selected_voice["voice_id"],
                    "tts_provider": selected_voice["provider"],
                    "tts_voice": selected_voice["voice_id"],
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
                if v["voice_id"] == voice
                and v["provider"] == provider
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
                generation_source="prompt_test",
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
                or voice["provider"] == self.state.s["selected_provider"]
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
            # The voice_search_cache contains pre-split words from _format_voice() output.
            voice_key = (voice["provider"], voice["voice_id"], voice["model"])
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
        defaults = smart_field_service.get_tts_defaults()
        initial_tts_options = tts_options or cast(OverrideableTTSOptionsDict, {})
        ret = {
            "providers": providers,
            "selected_provider": ALL,
            "voice": defaults.voice_id,
            "genders": [ALL, "Male", "Female"],
            "selected_gender": ALL,
            "languages": languages,
            "selected_language": ALL,
            "test_text": default_texts[ALL],
            "test_enabled": True,
            "search_text": "",
        }

        for k in overridable_tts_options:
            ret[k] = _defaulted_tts_option(initial_tts_options, k, defaults)
        return cast("TTSState", ret)


def _defaulted_tts_option(
    tts_options: OverrideableTTSOptionsDict,
    key: str,
    defaults: TTSGenerationSettings,
) -> Any:
    if tts_options.get(key) is not None:
        return tts_options[key]  # type: ignore[literal-required]

    defaults_by_key = {
        "tts_provider": defaults.provider,
        "tts_model": defaults.model,
        "tts_voice": defaults.voice_id,
    }
    return defaults_by_key[key]
