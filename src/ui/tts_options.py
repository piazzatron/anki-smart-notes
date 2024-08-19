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

from typing import List, Literal, TypedDict, Union

from anki.sound import play  # type: ignore
from aqt import (
    QAbstractListModel,
    QGroupBox,
    QItemSelection,
    QItemSelectionModel,
    QListView,
    QModelIndex,
    QPushButton,
    Qt,
    QWidget,
    mw,
)

from ..config import config
from ..logger import logger
from ..models import Languages, TTSProviders, TTSVoices, default_tts_models_map
from ..sentry import run_async_in_background_with_sentry
from ..tts_provider import TTSProvider
from .reactive_combo_box import ReactiveComboBox
from .reactive_edit_text import ReactiveEditText
from .state_manager import StateManager
from .ui_utils import default_form_layout

AllLanguages = Union[Literal["all"], Languages]
AllTTSProviders = Union[Literal["all"], TTSProviders]

Gender = Literal["all", "male", "female"]


class TTSMeta(TypedDict):
    tts_provider: TTSProviders
    voice: TTSVoices
    friendly_voice: str
    gender: Literal["male", "female", "all"]
    language: AllLanguages


class TTSState(TypedDict):
    # Combo box fields

    providers: List[AllTTSProviders]
    selected_provider: AllTTSProviders
    genders: List[Gender]
    selected_gender: Gender
    languages: List[AllLanguages]
    selected_language: AllLanguages

    voice: Union[Literal["all"], TTSVoices]

    # These are the actual values read from and written to config
    tts_provider: Union[TTSProviders, None]
    tts_voice: Union[TTSVoices, None]

    test_text: str
    test_enabled: bool


openai_voices: List[TTSMeta] = [
    {
        "tts_provider": "openai",
        "voice": "alloy",
        "friendly_voice": "alloy",
        "gender": "female",
        "language": "all",
    },
    {
        "tts_provider": "openai",
        "voice": "echo",
        "friendly_voice": "echo",
        "gender": "male",
        "language": "all",
    },
    {
        "tts_provider": "openai",
        "voice": "fable",
        "friendly_voice": "fable",
        "gender": "female",
        "language": "all",
    },
    {
        "tts_provider": "openai",
        "voice": "onyx",
        "friendly_voice": "onyx",
        "gender": "male",
        "language": "all",
    },
    {
        "tts_provider": "openai",
        "voice": "nova",
        "friendly_voice": "nova",
        "gender": "female",
        "language": "all",
    },
    {
        "tts_provider": "openai",
        "voice": "shimmer",
        "friendly_voice": "shimmer",
        "gender": "female",
        "language": "all",
    },
]

eleven_voices: List[TTSMeta] = [
    {
        "tts_provider": "elevenLabs",
        "voice": "male-1",
        "friendly_voice": "male #1",
        "gender": "male",
        "language": "all",
    },
    {
        "tts_provider": "elevenLabs",
        "voice": "male-2",
        "friendly_voice": "male #2",
        "gender": "male",
        "language": "all",
    },
    {
        "tts_provider": "elevenLabs",
        "voice": "female-1",
        "friendly_voice": "female #1",
        "gender": "female",
        "language": "all",
    },
    {
        "tts_provider": "elevenLabs",
        "voice": "female-2",
        "friendly_voice": "female #2",
        "gender": "female",
        "language": "all",
    },
]

# Combine all voices
voices = openai_voices + eleven_voices

languages: List[AllLanguages] = ["all", "english", "japanese"]
providers: List[AllTTSProviders] = ["all", "openai", "elevenLabs"]


class CustomListModel(QAbstractListModel):
    def __init__(self, data: List[TTSMeta]):
        super().__init__()
        self._data = data

    def data(self, index, role):
        if role == Qt.ItemDataRole.DisplayRole:
            return self.create_str(index.row())

    def rowCount(self, index):
        return len(self._data)

    def create_str(self, row: int) -> str:
        data = self._data[row]
        return f'{data["tts_provider"]} - {data["friendly_voice"]}'

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

        layout = default_form_layout()
        layout.addRow(self.render_filters())
        layout.addRow(self.render_voices_list())
        layout.addRow(self.render_test_voice())
        self.state.state_changed.connect(self.update_ui)

        self.setLayout(layout)

    def render_filters(self) -> QWidget:
        filters_box = QGroupBox("TTS Filters")
        filters_layout = default_form_layout()
        filters_box.setLayout(filters_layout)

        language = ReactiveComboBox(self.state, "languages", "selected_language")
        gender = ReactiveComboBox(self.state, "genders", "selected_gender")
        provider = ReactiveComboBox(self.state, "providers", "selected_provider")

        filters_layout.addRow("Language:", language)
        filters_layout.addRow("Gender:", gender)
        filters_layout.addRow("Provider:", provider)

        return filters_box

    def render_voices_list(self) -> QWidget:
        self.voices_list = QListView()
        self.voices_models = CustomListModel(self.get_visible_voice_filters())
        self.voices_list.setModel(self.voices_models)
        selection_model = self.voices_list.selectionModel()
        if selection_model:
            selection_model.selectionChanged.connect(self.voice_did_change)
        return self.voices_list

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
        if not (voice and provider):
            return

        selection_model = self.voices_list.selectionModel()
        if not selection_model:
            return

        selected_voice = next(
            (
                v
                for v in voices
                if v["voice"] == voice and v["tts_provider"] == provider
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

    def render_test_voice(self) -> QWidget:
        box = QGroupBox("Voice Testing")
        layout = default_form_layout()
        edit_text = ReactiveEditText(self.state, "test_text")
        edit_text.onChange.connect(lambda text: self.state.update({"test_text": text}))
        self.test_button = QPushButton("Test")
        self.test_button.clicked.connect(self.play_audio)

        layout.addRow("Text to test:", edit_text)
        layout.addRow(self.test_button)
        box.setLayout(layout)

        return box

    def play_audio(self) -> None:

        def on_success(audio: bytes):
            logger.debug("Successfully got audio!")
            if not mw or not mw.col.media:
                logger.error("No mw")
                return
            path = mw.col.media.write_data("smart-notes-test", audio)
            play(path)

            # Cleanup
            mw.col.media.trash_files([path])
            self.state.update({"test_enabled": True})

        # TODO: add on failure

        provider = self.state.s["tts_provider"]
        voice = self.state.s["tts_voice"]
        if not (provider and voice):
            return

        async def _async_play_audio() -> bytes:

            tts_provider = TTSProvider()
            resp = await tts_provider.async_get_tts_response(
                input=self.state.s["test_text"],
                model=default_tts_models_map[provider],
                provider=provider,
                voice=voice,
            )
            return resp

        self.state.update({"test_enabled": False})
        run_async_in_background_with_sentry(_async_play_audio, on_success=on_success)

    def get_visible_voice_filters(self) -> List[TTSMeta]:
        filtered = []
        for voice in voices:
            matches_provider = (
                self.state.s["selected_provider"] == "all"
                or voice["tts_provider"] == self.state.s["selected_provider"]
            )
            matches_gender = (
                self.state.s["selected_gender"] == "all"
                or voice["gender"] == self.state.s["selected_gender"]
            )
            matches_language = (
                self.state.s["selected_language"] == "all"
                or voice["language"]
                == "all"  # Or maybe don't want generic ones to appear?
                or voice["language"] == self.state.s["selected_language"]
            )
            if matches_provider and matches_gender and matches_language:
                filtered.append(voice)
        return filtered

    def get_initial_state(self) -> TTSState:
        return {
            "providers": providers,
            "selected_provider": "all",
            "voice": config.tts_voice,
            "genders": ["all", "male", "female"],
            "selected_gender": "all",
            "languages": languages,
            "selected_language": "all",
            "test_text": "",
            "test_enabled": True,
            "tts_provider": config.tts_provider,
            "tts_voice": config.tts_voice,
        }
