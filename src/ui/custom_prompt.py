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

# Note to future self / contributors:
# these classes are fairly brittle & tightly coupled, and deviate a good bit from
# existing patterns in the codebase (making heavy use of inheritance, using StateManager in an adhoc-way, etc)

from typing import Callable, TypedDict, Union

from anki.decks import DeckId
from anki.notes import Note
from aqt import (
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpacerItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    mw,
)

from ..field_processor import field_processor
from ..logger import logger
from ..media_utils import get_media_path, write_media
from ..notes import get_note_type, get_valid_fields_for_prompt
from ..prompts import get_prompts_for_note
from ..sentry import run_async_in_background_with_sentry
from ..tts_utils import play_audio
from .chat_options import ChatOptions
from .image_displayer import ImageDisplayer
from .image_options import ImageOptions
from .reactive_combo_box import ReactiveComboBox
from .state_manager import StateManager
from .tts_options import TTSOptions
from .ui_utils import font_small, show_message_box


class CustomPrompt(QDialog):
    _initial_prompt: Union[str, None]
    _generate_button: QPushButton
    _save_button: QPushButton
    _loading: bool = False
    _prompt_window: QTextEdit
    _note: Note
    _deck_id: DeckId
    _on_success: Callable[[], None]
    _field_upper: str

    def __init__(
        self,
        note: Note,
        deck_id: DeckId,
        field_upper: str,
        on_success: Callable[[], None],
        parent: Union[QWidget, None] = None,
    ) -> None:
        super().__init__(parent=parent)
        all_prompts = get_prompts_for_note(
            note_type=get_note_type(note),
            deck_id=deck_id,
            to_lower=False,
            fallback_to_global_deck=True,
        )
        self._initial_prompt = (
            all_prompts.get(field_upper, None) if all_prompts else None
        )
        self._note = note
        self._deck_id = deck_id
        self._field_upper = field_upper
        self._on_success = on_success

        self._setup_ui()

    def on_generate(self) -> None:
        raise Exception("Not Implemented")

    def render_custom_model(self) -> QWidget:
        raise Exception("Not implemented")

    def on_save_result(self) -> Union[str, None]:
        raise Exception("Not Implemented")

    def render_response_box(self) -> QWidget:
        raise Exception("Not Implemented")

    def has_output(self) -> bool:
        raise Exception("Not Implemented")

    def update_ui_states(self) -> None:
        raise Exception("Not implemented")

    def setup_ui(self) -> None:
        pass

    def _setup_ui(self) -> None:
        container = QVBoxLayout()

        box_layout = QHBoxLayout()
        box = QGroupBox()
        box.setLayout(box_layout)
        self.setWindowTitle("⚙️ Prompt Palette")
        self.setMinimumWidth(600)

        # Left
        left_container = QWidget()
        self.left_layout = QVBoxLayout()
        left_container.setLayout(self.left_layout)
        self._prompt_window = QTextEdit()
        self._prompt_window.setText(self._initial_prompt)
        self._prompt_window.textChanged.connect(self._on_prompt_changed)
        self._generate_button = QPushButton("Generate")
        self._generate_button.clicked.connect(self._on_generate)

        valid_fields = QLabel(
            "Valid fields: "
            + ", ".join(
                [
                    "{{" + field + "}} "
                    for field in get_valid_fields_for_prompt(
                        get_note_type(self._note), self._deck_id, self._field_upper
                    )
                ]
            )
        )
        valid_fields.setWordWrap(True)
        valid_fields.setFont(font_small)
        valid_fields.setMaximumWidth(600)

        self.left_layout.addWidget(QLabel("💬 Prompt"))
        self.left_layout.addWidget(self._prompt_window)
        self.left_layout.addWidget(valid_fields)
        self.left_layout.addWidget(self._generate_button)

        # Right
        self.right_container = QWidget()
        right_layout = QVBoxLayout()
        self.right_container.setLayout(right_layout)

        self._response_edit = QTextEdit()
        self._response_edit.setReadOnly(True)

        right_layout.addWidget(QLabel("✨ Response"))
        right_layout.addWidget(self.render_response_box())

        box_layout.addWidget(left_container)
        box_layout.addWidget(self.right_container)

        # Custom model

        container.addWidget(box)
        container.addItem(QSpacerItem(0, 16))
        container.addWidget(self._render_custom_model())

        self._save_button = QPushButton("Save Result")
        self._save_button.setEnabled(False)

        standard_buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)

        standard_buttons.addButton(
            self._save_button, QDialogButtonBox.ButtonRole.AcceptRole
        )

        standard_buttons.accepted.connect(self._on_save_result)
        standard_buttons.rejected.connect(self.close)
        container.addWidget(standard_buttons)

        self.setLayout(container)
        self.setup_ui()

    def _render_custom_model(self) -> QWidget:
        container = QGroupBox("⚙️ Custom Settings")
        layout = QVBoxLayout()
        container.setLayout(layout)
        layout.addWidget(self.render_custom_model())

        return container

    def _on_save_result(self) -> None:
        res = self.on_save_result()
        if not res:
            self.accept()
            return

        self._note[self._field_upper] = res
        mw.col.update_note(self._note)  # type: ignore
        self._on_success()
        self.accept()

    def _on_prompt_changed(self) -> None:
        self._update_ui_states()

    def reject(self):
        if not self.has_output() or show_message_box(
            "Close and lose results?", show_cancel=True
        ):
            QDialog.reject(self)

    def _on_generate(self) -> None:
        self._loading = True
        self._update_ui_states()
        self.on_generate()

    def _update_ui_states(self) -> None:
        self._save_button.setEnabled(not self._loading and self.has_output())
        self._generate_button.setEnabled(
            not self._loading and bool(self._prompt_window.toPlainText())
        )
        self.update_ui_states()


class CustomTextPrompt(CustomPrompt):

    _response_edit: QTextEdit
    _chat_options: ChatOptions

    def render_response_box(self) -> QWidget:
        self._response_edit = QTextEdit()
        self._response_edit.setReadOnly(True)
        return self._response_edit

    def on_generate(self) -> None:

        prompt = self._prompt_window.toPlainText()

        def on_success(text: str):
            self._loading = False
            self._response_edit.setText(text)
            self._update_ui_states()

        def on_error(error: Exception):
            msg = f"Error generating text: {error}"
            logger.error(msg)
            show_message_box(msg)
            self._loading = False
            self._update_ui_states()

        async def generate_text():
            return await field_processor.get_chat_response(
                note=self._note,
                deck_id=self._deck_id,
                prompt=prompt,
                field_lower=self._field_upper.lower(),
                temperature=self._chat_options.state.s["chat_temperature"],
                model=self._chat_options.state.s["chat_model"],
                provider=self._chat_options.state.s["chat_provider"],
                should_convert_to_html=True,
            )

        run_async_in_background_with_sentry(generate_text, on_success, on_error)

    def render_custom_model(self) -> QWidget:
        self._chat_options = ChatOptions(show_text_processing=False)
        return self._chat_options

    def has_output(self) -> bool:
        return bool(self._response_edit.toPlainText())

    def on_save_result(self) -> Union[str, None]:
        return self._response_edit.toPlainText()

    def update_ui_states(self) -> None:
        self._response_edit.setReadOnly(self._loading)


class CustomImagePrompt(CustomPrompt):
    response_image: ImageDisplayer
    raw_image: Union[bytes, None] = None
    image_options: ImageOptions

    def render_response_box(self) -> QWidget:
        self.response_image = ImageDisplayer(parent=self)
        return self.response_image

    def on_generate(self) -> None:
        prompt = self._prompt_window.toPlainText()

        def on_success(image: bytes):
            logger.debug("Got image")
            self._loading = False
            self.raw_image = image
            self._update_ui_states()

        def on_error(error: Exception):
            logger.error(f"Error generating image: {error}")
            show_message_box("Error generating image: " + str(error))
            self._loading = False
            self._update_ui_states()

        async def generate_image():
            return await field_processor.get_image_response(
                note=self._note,
                input_text=prompt,
                model=self.image_options.state.s["image_model"],
                provider=self.image_options.state.s["image_provider"],
            )

        run_async_in_background_with_sentry(generate_image, on_success, on_error)

    def render_custom_model(self) -> QWidget:
        self.image_options = ImageOptions()
        return self.image_options

    def has_output(self) -> bool:
        return bool(self.raw_image)

    def on_save_result(self) -> Union[str, None]:
        if not self.raw_image:
            return None
        file_name = get_media_path(self._note, self._field_upper, "webp")
        path = write_media(file_name, self.raw_image)
        return f'<img src="{path}"/>'

    def update_ui_states(self) -> None:
        if self.raw_image:
            self.response_image.set_image(self.raw_image)


class TTSPromptState(TypedDict):
    source_field: str
    source_fields: list[str]


class CustomTTSPrompt(CustomPrompt):
    audio: Union[bytes, None] = None

    def __init__(
        self,
        note: Note,
        deck_id: DeckId,
        field_upper: str,
        on_success: Callable[[], None],
    ) -> None:
        self._note = note
        self._deck_id = deck_id
        self._field_upper = field_upper

        source_fields = get_valid_fields_for_prompt(
            get_note_type(self._note), self._deck_id, self._field_upper
        )
        self.state = StateManager[TTSPromptState](
            {"source_fields": source_fields, "source_field": source_fields[0]}
        )

        super().__init__(
            note=note, deck_id=deck_id, field_upper=field_upper, on_success=on_success
        )

    def render_response_box(self) -> QWidget:
        # Create a play button from a QIcon
        self.play_button = QPushButton("▶️ Play")
        self.play_button.setEnabled(False)
        return self.play_button

    def on_generate(self) -> None:
        prompt = self._prompt_window.toPlainText()

        async def get_tts_response():
            return await field_processor.get_tts_response(
                note=self._note,
                input_text=prompt,
                model=self.tts_options.state.s["tts_model"],
                provider=self.tts_options.state.s["tts_provider"],
                voice=self.tts_options.state.s["tts_voice"],
                strip_html=True,
            )

        def on_success(audio: Union[bytes, None]):
            self._loading = False
            self.audio = audio

            self._update_ui_states()

            if not audio:
                logger.error("Custom prompt: no audio returned")
                return

            play_audio(audio)

        def on_failure(error: Exception):
            self._loading = False
            self._update_ui_states()

        run_async_in_background_with_sentry(
            get_tts_response, on_success=on_success, on_failure=on_failure
        )

    def render_custom_model(self) -> QWidget:
        self.tts_options = TTSOptions(extras_visible=False)
        return self.tts_options

    def has_output(self) -> bool:
        return bool(self.audio)

    def on_save_result(self) -> Union[None, str]:
        if not self.audio:
            return None
        file_name = get_media_path(self._note, self._field_upper, "mp3")
        path = write_media(file_name, self.audio)
        return f"[sound: {path}]"

    def update_ui_states(self) -> None:
        self.play_button.setEnabled(not self._loading and self.has_output())

    def setup_ui(self) -> None:
        self.source_combo = ReactiveComboBox(
            self.state, "source_fields", "source_field"
        )

        def update_source_combo(pick: str):
            self._prompt_window.setText(f"{{{{{pick}}}}}")

        update_source_combo(self.state.s["source_field"])

        self.source_combo.onChange.connect(update_source_combo)
        self.left_layout.addItem(QSpacerItem(0, 16))
        self.left_layout.addWidget(QLabel("Source Field"))
        self.left_layout.addWidget(self.source_combo)
        self.right_container.hide()
