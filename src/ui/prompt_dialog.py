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

from collections.abc import Callable
from typing import Any, Literal, Optional, TypedDict, Union, cast

from anki.decks import DeckId
from anki.notes import Note
from aqt import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    Qt,
    QTabWidget,
    QTextEdit,
    QTextOption,
    QTimer,
    QVBoxLayout,
    QWidget,
    mw,
)

from ..app_state import (
    is_app_legacy,
    is_capacity_remaining,
    is_capacity_remaining_or_legacy,
)
from ..config import config, key_or_config_val
from ..constants import GLOBAL_DECK_ID, UNPAID_PROVIDER_ERROR
from ..dag import prompt_has_error
from ..decks import deck_id_to_name_map, get_all_deck_ids
from ..logger import logger
from ..models import (
    DEFAULT_EXTRAS,
    OverrideableTTSOptionsDict,
    PromptMap,
    SmartFieldType,
    overridable_chat_options,
    overridable_image_options,
    overridable_tts_options,
)
from ..note_proccessor import NoteProcessor
from ..notes import get_note_types, get_random_note, get_valid_fields_for_prompt
from ..prompts import (
    add_or_update_prompts,
    get_extras,
    get_prompt_fields,
    get_prompts_for_note,
    interpolate_prompt,
)
from ..sentry import run_async_in_background_with_sentry
from ..tts_utils import play_audio
from ..utils import get_fields, none_defaulting, to_lowercase_dict
from .chat_options import ChatOptions
from .image_displayer import ImageDisplayer
from .image_options import ImageOptions
from .reactive_check_box import ReactiveCheckBox
from .reactive_combo_box import ReactiveComboBox
from .reactive_edit_text import ReactiveEditText
from .state_manager import StateManager
from .tts_options import TTSOptions
from .ui_utils import default_form_layout, font_bold, font_small, show_message_box

explanation = """Write a prompt to help the chat model generate your Smart Field.

Your prompt may reference other fields via {{double curly braces}}. Valid fields are listed below for convenience.

Test out your prompt with the test button before saving it!
"""


class State(TypedDict):
    prompt: str
    note_types: list[str]
    selected_note_type: str
    note_fields: list[str]
    tts_source_fields: list[str]
    selected_tts_source_field: str
    selected_note_field: str
    is_loading_prompt: bool
    generate_automatically: bool

    use_custom_model: bool
    type: SmartFieldType

    selected_deck: DeckId
    decks: list[DeckId]


class PartialState(TypedDict):
    prompt: str
    note_fields: list[str]
    selected_note_field: str
    tts_source_fields: list[str]
    selected_tts_source_field: str
    selected_note_type: str
    selected_deck: DeckId


class PromptDialog(QDialog):
    prompt_text_box: QTextEdit
    test_button: QPushButton
    valid_fields: QLabel
    note_combo_box: QComboBox
    state: StateManager[State]
    prompts_map: PromptMap
    chat_options: ChatOptions
    image_options: ImageOptions
    tts_options: TTSOptions
    mode: Literal["new", "edit"]
    field_type: SmartFieldType

    def __init__(
        self,
        prompts_map: PromptMap,
        processor: NoteProcessor,
        on_accept_callback: Callable[[PromptMap], None],
        field_type: SmartFieldType,
        deck_id: DeckId,
        card_type: Optional[str] = None,
        field: Optional[str] = None,
        prompt: Optional[str] = None,
    ):
        super().__init__()

        self.processor = processor
        self.on_accept_callback = on_accept_callback
        self.prompts_map = prompts_map
        self.mode = "edit" if card_type else "new"
        self.field_type = field_type
        note_types = self._get_note_types(deck_id=deck_id)
        selected_note_type = card_type or note_types[0]

        # Ensure there are valid fields to select
        if not len(note_types):
            show_message_box(
                "No valid note types left. Edit or delete some fields to continue!"
            )
            QTimer.singleShot(0, self.close)
            return

        default_note_state = self._state_for_new_card_type(
            selected_note_type, field_type, deck_id=deck_id
        )
        selected_target_field = field or default_note_state["selected_note_field"]

        extras = (
            get_extras(
                note_type=selected_note_type,
                field=selected_target_field,
                prompts=self.prompts_map,
                deck_id=deck_id,
            )
            or DEFAULT_EXTRAS
        )

        # Only if it's a new card, we need to get the fields for the selected card type
        target_fields = (
            default_note_state["note_fields"]
            if self.mode == "new"
            else get_fields(selected_note_type)
        )

        # If it's an edit, we need to get the source field from the prompt
        selected_tts_source_field = (
            (self._attempt_to_parse_source_field(prompt) or "")
            if prompt
            else default_note_state["selected_tts_source_field"]
        )

        initial_state: State = {
            "prompt": prompt or default_note_state["prompt"],
            # Note types
            "selected_note_type": selected_note_type,
            "note_types": note_types,
            # tts
            "tts_source_fields": default_note_state["tts_source_fields"],
            "selected_tts_source_field": selected_tts_source_field,
            # target fields
            "note_fields": target_fields,
            "selected_note_field": selected_target_field,
            # other
            "is_loading_prompt": False,
            "decks": get_all_deck_ids(),
            "selected_deck": deck_id,
            "type": field_type,
            "generate_automatically": extras["automatic"],
            "use_custom_model": extras["use_custom_model"],
        }
        self.state = StateManager[State](initial_state)

        self.enabled_box = ReactiveCheckBox(
            self.state,
            "generate_automatically",
            text="Enabled",
        )
        self.standard_buttons = self.create_buttons()

        tabs = QTabWidget()
        tabs.addTab(self.render_main_tab(), "General")
        tabs.addTab(self.render_options_tab(), "Options")

        container = QVBoxLayout()
        container.addWidget(tabs)

        container.addWidget(self.standard_buttons)
        self.setLayout(container)
        self.setup_ui()

    def setup_ui(self) -> None:
        self.render_ui()

    def render_ui(self) -> None:
        self.render_buttons()
        self.render_valid_fields()
        self.render_automatic_button()

    def render_main_tab(self) -> QWidget:
        layout = QVBoxLayout()

        field_type = self.state.s["type"]
        text = {
            "title": {
                "chat": "💬 New Text Field",
                "tts": "🔈️ New Text to Speech Field",
                "image": " 🖼️ New Image Field",
            },
            "explanation": {
                "chat": "The note that will have the Smart Field",
                "tts": "The note type that will have the TTS field",
                "image": "The note type that will have the image field",
            },
            "destination": {
                "chat": "Target Field",
                "tts": "Target Field",
                "image": "Target Field",
            },
            "destination_explanation": {
                "chat": "The AI generated Smart Field.",
                "tts": "The field that will store and play the audio file.",
                "image": "The field that will display the image.",
            },
        }

        self.setWindowTitle(text["title"][field_type])

        self.note_combo_box = ReactiveComboBox(
            self.state, "note_types", "selected_note_type"
        )
        card_label = QLabel("Note Type")
        card_label.setFont(font_bold)
        card_explanation = QLabel(text["explanation"][field_type])
        card_explanation.setFont(font_small)
        layout.addWidget(card_label)
        layout.addWidget(self.note_combo_box)
        layout.addWidget(card_explanation)
        layout.addSpacerItem(QSpacerItem(0, 20))

        deck_label = QLabel("Deck")
        deck_label.setFont(font_bold)
        self.deck_subtitle = QLabel(
            "Optionally apply this field only to a specific deck (useful for sharing note types between decks)."
        )
        self.deck_subtitle.setMaximumWidth(500)
        self.deck_subtitle.setFont(font_small)
        self.deck_combo_box = ReactiveComboBox(
            self.state,
            "decks",
            "selected_deck",
            render_map={str(k): v for k, v in deck_id_to_name_map().items()},
            int_keys=True,
        )
        layout.addWidget(deck_label)
        layout.addWidget(self.deck_combo_box)
        layout.addWidget(self.deck_subtitle)
        layout.addSpacerItem(QSpacerItem(0, 20))

        if self.state.s["type"] == "tts":
            self.tts_source_combo_box = ReactiveComboBox(
                self.state, "tts_source_fields", "selected_tts_source_field"
            )
            self.tts_source_combo_box.on_change.connect(self.on_source_changed)
            source_label = QLabel("Source Field")
            source_label.setFont(font_bold)
            source_explainer = QLabel("The field that will be spoken.")
            source_explainer.setFont(font_small)
            layout.addWidget(source_label)
            layout.addWidget(self.tts_source_combo_box)
            layout.addWidget(source_explainer)
            layout.addItem(QSpacerItem(0, 20))

        self.field_combo_box = ReactiveComboBox(
            self.state, "note_fields", "selected_note_field"
        )
        field_label = QLabel(text["destination"][field_type])
        field_label.setFont(font_bold)
        field_explanation = QLabel(text["destination_explanation"][field_type])
        field_explanation.setFont(font_small)
        layout.addWidget(field_label)
        layout.addWidget(self.field_combo_box)
        layout.addWidget(field_explanation)
        layout.addSpacerItem(QSpacerItem(0, 20))

        self.test_button = QPushButton("✨ Test Smart Field ✨")

        text_only_container = QWidget()
        text_only_layout = QVBoxLayout()
        text_only_container.setLayout(text_only_layout)
        text_only_layout.setContentsMargins(0, 0, 0, 0)
        text_only_container.setHidden(self.state.s["type"] == "tts")

        prompt_label = QLabel("Prompt")
        prompt_label.setFont(font_bold)
        self.prompt_text_box = ReactiveEditText(self.state, "prompt")
        self.prompt_text_box.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.prompt_text_box.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.prompt_text_box.setWordWrapMode(
            QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere
        )
        self.prompt_text_box.setPlaceholderText(explanation)
        self.valid_fields = QLabel("")
        self.valid_fields.setMinimumWidth(500)
        size_policy = QSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding
        )
        size_policy.setHorizontalStretch(1)
        self.valid_fields.setSizePolicy(size_policy)
        self.valid_fields.setWordWrap(True)
        small_font = self.valid_fields.font()
        small_font.setPointSize(10)
        self.valid_fields.setFont(small_font)

        self.setLayout(layout)
        text_only_layout.addWidget(prompt_label)
        text_only_layout.addWidget(self.prompt_text_box)
        text_only_layout.addWidget(self.valid_fields)
        layout.addWidget(text_only_container)
        layout.addSpacerItem(QSpacerItem(0, 12))

        layout.addWidget(self.test_button)
        layout.addSpacerItem(
            QSpacerItem(
                0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
            )
        )

        self.state.state_changed.connect(self.render_ui)
        self.note_combo_box.on_change.connect(self._on_new_card_type_selected)
        self.field_combo_box.on_change.connect(self.on_target_field_changed)
        self.deck_combo_box.on_change.connect(self.on_deck_selected)
        self.prompt_text_box.on_change.connect(
            lambda text: self.state.update({"prompt": text})
        )

        self.test_button.clicked.connect(self.on_test)

        field_options = QGroupBox()
        field_layout = QVBoxLayout()
        field_options.setLayout(field_layout)
        automatic_explanation = QLabel(
            "Enable or disable this field. Disabled fields can be generated via right clicking a field in the editor."
        )
        automatic_explanation.setFont(font_small)
        field_layout.addWidget(self.enabled_box)
        field_layout.addWidget(automatic_explanation)

        layout.addItem(QSpacerItem(0, 24))
        layout.addWidget(field_options)

        # On small screens, make it a proportion of screen height. Otherwise set a fixed height
        FIXED_HEIGHT = 800
        screen = mw and mw.screen()
        screen_height = FIXED_HEIGHT if not screen else screen.geometry().height()

        min_height = min(FIXED_HEIGHT, int(screen_height * 0.8))
        self.setMinimumHeight(min_height)
        container = QWidget()
        container.setLayout(layout)

        # Control visibility depending on mode
        if self.mode == "edit":
            self.note_combo_box.setEnabled(False)
            self.field_combo_box.setEnabled(False)
            self.deck_combo_box.setEnabled(False)
            if hasattr(self, "tts_source_combo_box"):
                self.tts_source_combo_box.setEnabled(False)
        if is_app_legacy():
            self.deck_combo_box.setEnabled(False)
            self.deck_subtitle.setText(
                "🔒 Deck based Smart Fields are only available on paid plans!"
            )
        return container

    def render_options_tab(self) -> QWidget:
        models_layout = default_form_layout()
        self.model_options = self.render_custom_model()
        self.model_options.setEnabled(self.state.s["use_custom_model"])
        self.custom_model = ReactiveCheckBox(self.state, "use_custom_model")
        self.state.state_changed.connect(self.on_state_update)
        override_box = QWidget()
        override_layout = QHBoxLayout()
        override_layout.setContentsMargins(0, 0, 0, 0)
        override_box.setLayout(override_layout)
        override_layout.addWidget(QLabel("Override Default Settings"))
        override_layout.addWidget(self.custom_model)
        models_layout.addWidget(override_box)
        models_layout.addWidget(self.model_options)
        model_box = QGroupBox("⚙️ Model Settings")
        is_legacy = is_app_legacy()
        model_box.setEnabled(not is_legacy)
        if is_legacy:
            model_box.setToolTip(
                "Model settings are only available in the full version."
            )

        model_box.setLayout(models_layout)
        model_box.setContentsMargins(0, 24, 0, 24)

        container_layout = default_form_layout()
        container_layout.addRow(QLabel(""), None)
        container_layout.addRow(model_box)
        container = QWidget()
        container.setLayout(container_layout)
        return container

    def create_buttons(self) -> QWidget:
        standard_buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.Save
        )

        standard_buttons.accepted.connect(self.on_accept)
        standard_buttons.rejected.connect(self.reject)
        return standard_buttons

    def render_custom_model(self) -> QWidget:
        # TODO: could use a refactor
        # Setup the dummy options; only one will be used
        self.tts_options = TTSOptions()
        self.chat_options = ChatOptions()
        self.image_options = ImageOptions()

        extras = get_extras(
            note_type=self.state.s["selected_note_type"],
            field=self.state.s["selected_note_field"],
            deck_id=self.state.s["selected_deck"],
            prompts=self.prompts_map,
            fallback_to_global_deck=False,
        )

        use_custom_model = extras and extras["use_custom_model"]

        if self.state.s["type"] == "tts":
            if extras and use_custom_model:
                self.tts_options = TTSOptions(
                    {
                        "tts_provider": extras.get("tts_provider"),
                        "tts_voice": extras.get("tts_voice"),
                        "tts_model": extras.get("tts_model"),
                        "tts_strip_html": extras.get("tts_strip_html"),
                    }
                )
            return self.tts_options

        elif self.state.s["type"] == "chat":
            if extras and use_custom_model:
                self.chat_options = ChatOptions(
                    {
                        "chat_provider": extras.get("chat_provider"),
                        "chat_model": extras.get("chat_model"),
                        "chat_temperature": extras.get("chat_temperature"),
                        "chat_markdown_to_html": extras.get("chat_markdown_to_html"),
                    }
                )
            return self.chat_options

        elif self.state.s["type"] == "image":
            if extras and use_custom_model:
                self.image_options = ImageOptions(
                    {
                        "image_model": extras.get("image_model"),
                        "image_provider": "replicate",
                    }
                )
            return self.image_options

        # Should never get here
        return QWidget()

    def on_state_update(self):
        self.model_options.setEnabled(self.state.s["use_custom_model"])

    def _get_note_types(self, deck_id: DeckId) -> list[str]:
        """Returns note types for which there are valid target fields remaining"""
        note_types = get_note_types()
        # Need to find a note type where there are valid field
        return [
            note_type
            for note_type in note_types
            if self._valid_fields_remain(note_type, deck_id=deck_id)
        ]

    def _valid_fields_remain(self, note_type: str, deck_id: DeckId) -> bool:
        target_fields = self._get_valid_target_fields(note_type, deck_id=deck_id)
        return len(target_fields) > 0

    def _state_for_new_card_type(
        self, note_type: str, type: SmartFieldType, deck_id: DeckId
    ) -> PartialState:
        target_fields = self._get_valid_target_fields(note_type, deck_id=deck_id)
        target_field = target_fields[0] if len(target_fields) else "None"

        source_fields = get_valid_fields_for_prompt(
            note_type, deck_id=deck_id, prompts_map=self.prompts_map
        )
        source_field = self._get_initial_source_field(note_type, deck_id=deck_id)
        prompt = self.get_tts_prompt(source_field) if type == "tts" else ""

        return {
            "selected_note_type": note_type,
            "prompt": prompt,
            "selected_deck": deck_id,
            "selected_note_field": target_field,
            "note_fields": target_fields,
            "tts_source_fields": source_fields,
            "selected_tts_source_field": source_field,
        }

    def _on_new_card_type_selected(self, note_type: str) -> None:
        new_state = self._state_for_new_card_type(
            note_type=note_type, type=self.state.s["type"], deck_id=GLOBAL_DECK_ID
        )
        self.state.update(cast("dict[str, Any]", new_state))
        # Force re-layout every time
        self.adjustSize()

    def on_deck_selected(self, deck: str) -> None:
        # Dumb hack bc of leaky abstraction reactive combo box + int keys
        deck_id = DeckId(int(deck))
        note_type = self.state.s["selected_note_type"]
        new_state = self._state_for_new_card_type(
            note_type=note_type, type=self.state.s["type"], deck_id=deck_id
        )

        self.state.update(cast("dict[str, Any]", new_state))

    def on_source_changed(self, source: str) -> None:
        self.state.update({"prompt": self.get_tts_prompt(source)})

    def get_tts_prompt(self, source: str) -> str:
        return f"{{{{{source}}}}}"

    def on_target_field_changed(self, field: Optional[str]) -> None:
        # This shouldn't happen
        if not field:
            return

        prompt = (
            self.get_tts_prompt(self.state.s["selected_tts_source_field"])
            if self.state.s["type"] == "tts"
            else ""
        )

        self.state.update(
            {
                "prompt": prompt,
                "selected_note_field": field,
            }
        )

    def render_buttons(self) -> None:
        is_enabled = (
            bool(self.state.s["prompt"]) and not self.state.s["is_loading_prompt"]
        )

        self.test_button.setEnabled(is_enabled)
        self.standard_buttons.button(QDialogButtonBox.StandardButton.Save).setEnabled(  # type: ignore
            is_enabled
        )

        if self.state.s["is_loading_prompt"]:
            self.test_button.setText("Loading...")
        else:
            self.test_button.setText("Test With Random Note✨")

    def on_test(self) -> None:
        if self.state.s["type"] == "chat":
            if not is_capacity_remaining_or_legacy(True):
                return
        else:
            if not is_capacity_remaining(True):
                return

        prompt = self.state.s["prompt"]

        if not mw or not self.state.s["prompt"]:
            return

        selected_note_type = self.state.s["selected_note_type"]
        sample_note = get_random_note(
            selected_note_type, deck_id=self.state.s["selected_deck"]
        )

        if not sample_note:
            show_message_box("Smart Notes: need at least one note of this note type!")
            return
        new_prompts_map = self._create_new_prompts_map()

        error = prompt_has_error(
            prompt,
            note=sample_note,
            target_field=self.state.s["selected_note_field"],
            prompts_map=new_prompts_map,
            deck_id=self.state.s["selected_deck"],
        )

        if error:
            show_message_box(f"Invalid prompt: {error}")
            return

        self.state["is_loading_prompt"] = True

        # TODO: this part could use some simplification
        chat_provider = (
            self.chat_options.state.s["chat_provider"]
            if self.state.s["use_custom_model"]
            else config.chat_provider
        )
        chat_model = (
            self.chat_options.state.s["chat_model"]
            if self.state.s["use_custom_model"]
            else config.chat_model
        )

        tts_provider = (
            self.tts_options.state.s["tts_provider"]
            if self.state.s["use_custom_model"]
            else config.tts_provider
        ) or config.tts_provider

        tts_voice = (
            self.tts_options.state.s["tts_voice"]
            if self.state.s["use_custom_model"]
            else config.tts_voice
        ) or config.tts_voice

        tts_model = (
            self.tts_options.state.s["tts_model"]
            if self.state.s["use_custom_model"]
            else config.tts_model
        ) or config.tts_model

        def on_success(arg: Union[str, bytes, None]):
            prompt = self.state.s["prompt"]
            if not prompt:
                return

            prompt_fields = get_prompt_fields(prompt)

            # clumsy stuff to make it work with lowercase fields...
            fields = to_lowercase_dict(sample_note)  # type: ignore
            field_map = {
                prompt_field: fields[prompt_field] for prompt_field in prompt_fields
            }

            stringified_vals = "\n".join([f"{k}: {v}" for k, v in field_map.items()])
            self.state["is_loading_prompt"] = False
            field_type = self.state.s["type"]
            if field_type == "chat":
                if arg is None:
                    msg = f"Ran with fields: \n{stringified_vals}.\n Model: {chat_model}\n\n Response: No response received"
                else:
                    msg = f"Ran with fields: \n{stringified_vals}.\n Model: {chat_model}\n\n Response: {arg}"
                show_message_box(msg, custom_ok="Close")
            elif field_type == "tts":
                msg = f"Ran with fields: \n{stringified_vals}.\n Voice: {tts_provider} - {tts_voice}\n\n"
                if arg is not None and isinstance(arg, bytes):
                    play_audio(arg)
                else:
                    msg += "No audio response received"
                show_message_box(msg, custom_ok="Close")
            else:
                if arg is not None and isinstance(arg, bytes):
                    test_window = ImageTestDialog(
                        arg, interpolate_prompt(prompt, sample_note) or ""
                    )
                    test_window.exec()
                else:
                    show_message_box("No image response received", custom_ok="Close")

        def on_failure(e: Exception) -> None:
            show_message_box(f"Failed to get response: {e}")
            self.state["is_loading_prompt"] = False

        if self.state.s["type"] == "chat":

            def chat_fn():
                return self.processor.field_processor.get_chat_response(
                    prompt=prompt,
                    note=sample_note,
                    provider=chat_provider,
                    model=chat_model,
                    field_lower=self.state.s["selected_note_field"].lower(),
                    deck_id=self.state.s["selected_deck"],
                    temperature=key_or_config_val(
                        self.chat_options.state.s, "chat_temperature"
                    ),
                    should_convert_to_html=False,  # Don't show HTML here bc it's confusing
                )

            run_async_in_background_with_sentry(chat_fn, on_success, on_failure)
        elif self.state.s["type"] == "tts":

            def tts_fn():
                return self.processor.field_processor.get_tts_response(
                    input_text=prompt,
                    note=sample_note,
                    provider=tts_provider,
                    model=tts_model,
                    voice=tts_voice,
                    strip_html=none_defaulting(
                        self.tts_options.state.s, "tts_strip_html", True
                    ),
                )

            run_async_in_background_with_sentry(tts_fn, on_success, on_failure)
        else:

            def img_fn():
                return self.processor.field_processor.get_image_response(
                    input_text=prompt,
                    note=sample_note,
                    model="flux-dev",
                    provider="replicate",
                )

            run_async_in_background_with_sentry(img_fn, on_success, on_failure)

    def render_automatic_button(self) -> None:
        self.enabled_box.setChecked(self.state.s["generate_automatically"])

    def render_valid_fields(self) -> None:
        fields = get_valid_fields_for_prompt(
            selected_note_type=self.state.s["selected_note_type"],
            selected_note_field=self.state.s["selected_note_field"],
            deck_id=self.state.s["selected_deck"],
            prompts_map=self.prompts_map,
        )
        fields = ["{{" + field + "}}" for field in fields]
        text = f"Valid fields to include in prompt: {', '.join(fields)}"
        self.valid_fields.setText(text)

    def _get_valid_target_fields(
        self,
        selected_note_type: str,
        deck_id: DeckId,
        selected_note_field: Optional[str] = None,
    ) -> list[str]:
        """Gets all fields excluding selected and existing prompts"""
        all_valid_fields = get_valid_fields_for_prompt(
            selected_note_type=selected_note_type,
            selected_note_field=selected_note_field,
            deck_id=deck_id,
            prompts_map=self.prompts_map,
        )
        existing_prompts = set(
            (
                get_prompts_for_note(
                    note_type=selected_note_type,
                    override_prompts_map=self.prompts_map,
                    deck_id=deck_id,
                    fallback_to_global_deck=False,
                )
                or {}
            ).keys()
        )

        return [field for field in all_valid_fields if field not in existing_prompts]

    def _get_initial_source_field(self, note_type: str, deck_id: DeckId) -> str:
        """Get the first valid source field for a note type by finding the first field that isn't the default target field"""
        fields = get_fields(note_type)
        # Strange case of cards with a single field
        if (len(fields)) == 1:
            logger.debug(f"Note type {note_type} has no valid fields")
            return fields[0]

        valid_target_fields = get_valid_fields_for_prompt(
            note_type, deck_id=deck_id, prompts_map=self.prompts_map
        )
        default_target_field = (
            valid_target_fields[0] if len(valid_target_fields) > 0 else None
        )
        return next(
            (f for f in fields if f != default_target_field),
            "No valid source fields remaining",
        )

    def _attempt_to_parse_source_field(self, prompt: str) -> Optional[str]:
        fields = get_prompt_fields(prompt, lower=False)

        if len(fields) != 1:
            return None

        return fields[0]

    def on_accept(self):
        if not mw or not mw.col:
            return

        prompt = self.state.s["prompt"]
        selected_card_type = self.state.s["selected_note_type"]
        selected_field = self.state.s["selected_note_field"]

        if not prompt:
            return

        new_prompts_map = self._create_new_prompts_map()
        logger.debug("Created new prompts map")
        logger.debug(new_prompts_map)

        # Make an ephemeral note
        note_type = next(
            (e for e in mw.col.models.all() if e["name"] == selected_card_type), None
        )

        if not note_type:
            logger.error("Unexpectedly find note type in prompt_dialog")
            return

        sample_note = Note(mw.col, note_type)

        err = prompt_has_error(
            prompt,
            note=sample_note,
            target_field=selected_field,
            prompts_map=new_prompts_map,
            deck_id=self.state.s["selected_deck"],
        )

        if err:
            show_message_box(f"Invalid prompt: {err}")
            return

        # Ensure only openai for legacy
        if (
            not is_capacity_remaining()
            and self.state.s["use_custom_model"]
            and self.chat_options.state.s["chat_provider"] != "openai"
        ):
            show_message_box(UNPAID_PROVIDER_ERROR)
            return

        self.on_accept_callback(new_prompts_map)
        self.accept()

    def _create_new_prompts_map(self) -> PromptMap:
        s = self.state.s

        return add_or_update_prompts(
            prompts_map=self.prompts_map,
            note_type=s["selected_note_type"],
            deck_id=s["selected_deck"],
            field=s["selected_note_field"],
            prompt=s["prompt"],
            is_automatic=s["generate_automatically"],
            is_custom_model=s["use_custom_model"],
            type=s["type"],
            tts_options=cast(
                "OverrideableTTSOptionsDict",
                {k: self.tts_options.state.s[k] for k in overridable_tts_options},
            ),
            chat_options={
                k: self.chat_options.state.s[k] for k in overridable_chat_options
            },
            image_options={
                k: self.image_options.state.s[k] for k in overridable_image_options
            },
        )


class ImageTestDialog(QDialog):
    def __init__(self, image: bytes, prompt: str):
        super().__init__()
        self.setWindowTitle("Image Previewer")
        layout = QVBoxLayout()
        self.setLayout(layout)
        explainer = QLabel(f"Ran with prompt: {prompt}")
        explainer.setWordWrap(True)
        explainer.setMaximumWidth(480)
        layout.addWidget(explainer)
        displayer = ImageDisplayer(image=image)
        layout.addWidget(displayer)
