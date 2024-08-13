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

from anki.sound import play
from aqt import QAbstractListModel, QGroupBox, QListView, QPushButton, Qt, QWidget, mw

from ..logger import logger
from ..models import Languages, TTSProviders, TTSVoices
from ..sentry import run_async_in_background_with_sentry
from ..tts_provider import TTSProvider
from .reactive_combo_box import ReactiveComboBox
from .reactive_edit_text import ReactiveEditText
from .state_manager import StateManager
from .ui_utils import default_form_layout

AllLanguages = Union[Literal["all"], Languages]
AllTTSProviders = Union[Literal["all"], TTSProviders]


class State(TypedDict):
    tts_provider: AllTTSProviders
    voice: Union[Literal["all"], TTSVoices]
    gender: Literal["all", "male", "female"]
    languages: AllLanguages
    selected_language: AllLanguages
    test_text: str
    test_enabled: bool


class Voice(TypedDict):
    tts_provider: TTSProviders
    voice: TTSVoices
    friendly_voice: str
    gender: Literal["male", "female", "all"]
    language: AllLanguages


voices: List[Voice] = [
    {
        "tts_provider": "openai",
        "voice": "alloy",
        "friendly_voice": "Alloy",
        "gender": "male",
        "language": "all",
    },
    {
        "tts_provider": "openai",
        "voice": "echo",
        "friendly_voice": "echo",
        "gender": "female",
        "language": "english",
    },
]

languages: List[AllLanguages] = ["all", "english", "japanese"]
providers: List[AllTTSProviders] = ["all", "openai", "elevenLabs"]


class CustomListModel(QAbstractListModel):
    def __init__(self, data: List[Voice]):
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

    def update_data(self, new_data: List[Voice]):
        self.beginResetModel()
        self._data = new_data
        self.endResetModel()


class TTSSettings(QWidget):
    def __init__(self, state: StateManager[State]):
        super().__init__()

        self.state = state
        self.setup_ui()

    def setup_ui(self) -> None:

        self.voices_list = QListView()
        self.voices_models = CustomListModel(self.get_voices())
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
        language.onChange.connect(
            lambda lang: self.state.update({"selected_language": lang})
        )
        filters_layout.addRow("Language:", language)
        return filters_box

    def render_voices_list(self) -> QWidget:
        self.voices_list = QListView()
        self.voices_models = CustomListModel(self.get_voices())
        self.voices_list.setModel(self.voices_models)
        return self.voices_list

    def update_ui(self) -> None:
        self.voices_models.update_data(self.get_voices())
        self.test_button.setEnabled(self.state.s["test_enabled"])

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
        async def _async_play_audio() -> bytes:

            provider = TTSProvider()
            resp = await provider.async_get_tts_response(
                input=self.state.s["test_text"],
                # TODO: Model!!! fuck. Do we even need to support this?
                model="tts-1",
                # TODO
                # provider=self.state.s["tts_provider"],
                # voice=self.state.s["voice"],
                provider="openai",
                voice="alloy",
            )
            return resp

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
        # TODO: why's this type wrong

        self.state.update({"test_enabled": False})
        run_async_in_background_with_sentry(_async_play_audio, on_success=on_success)  # type: ignore

    def get_voices(self) -> List[Voice]:
        filtered = []
        for voice in voices:
            matches_provider = (
                self.state.s["tts_provider"] == "all"
                or voice["tts_provider"] == self.state.s["tts_provider"]
            )
            matches_gender = (
                self.state.s["gender"] == "all"
                or voice["gender"] == self.state.s["gender"]
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
