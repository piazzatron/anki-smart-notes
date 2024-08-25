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

from typing import Callable, List, Literal, TypedDict, Union

from aqt import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QLabel,
    QPushButton,
    QSizePolicy,
    Qt,
    QTabWidget,
    QTextEdit,
    QTextOption,
    QTimer,
    QVBoxLayout,
    QWidget,
    mw,
)
from PyQt6.QtCore import Qt

from ..app_state import is_app_unlocked
from ..config import FieldExtras, PromptMap, config
from ..constants import UNPAID_PROVIDER_ERROR
from ..logger import logger
from ..models import ChatModels
from ..notes import get_note_types
from ..processor import Processor
from ..prompts import (
    get_extras,
    get_generate_automatically,
    get_prompt_fields,
    get_prompts,
    prompt_has_error,
)
from ..utils import get_fields, to_lowercase_dict
from .chat_options import (
    ChatOptions,
    ReadableChatProvider,
    chat_provider_to_ui_map,
    chat_ui_to_provider_map,
    default_form_layout,
    provider_model_map,
)
from .reactive_check_box import ReactiveCheckBox
from .reactive_combo_box import ReactiveComboBox
from .reactive_edit_text import ReactiveEditText
from .state_manager import StateManager
from .tts_options import TTSOptions
from .ui_utils import font_small, show_message_box

explanation = """Write a "prompt" to help the chat model generate your target smart field.

You may reference any other field via enclosing it in {{double curly braces}}. Valid fields are listed below for convenience.

Test out your prompt with the test button before saving it!
"""


class State(TypedDict):
    prompt: str
    note_types: List[str]
    selected_note_type: str
    note_fields: List[str]
    tts_source_fields: List[str]
    selected_tts_source_field: str
    selected_note_field: str
    is_loading_prompt: bool
    generate_manually: bool
    chat_provider: ReadableChatProvider
    chat_providers: List[ReadableChatProvider]
    chat_models: List[ChatModels]
    chat_model: ChatModels
    chat_temperature: int
    use_custom_model: bool
    type: Literal["chat", "tts"]


class PartialState(TypedDict):
    prompt: str
    target_fields: List[str]
    target_field: str
    source_fields: List[str]
    source_field: str


class PerFieldSettings(TypedDict):
    chat_provider: ReadableChatProvider
    chat_model: ChatModels
    chat_temperature: int
    use_custom_model: bool
    type: Literal["chat", "tts"]


class PromptDialog(QDialog):
    prompt_text_box: QTextEdit
    test_button: QPushButton
    valid_fields: QLabel
    card_combo_box: QComboBox
    state: StateManager[State]
    prompts_map: PromptMap
    chat_options: ChatOptions
    tts_options: TTSOptions
    mode: Literal["new", "edit"]
    field_type: Literal["chat", "tts"]

    def __init__(
        self,
        prompts_map: PromptMap,
        processor: Processor,
        on_accept_callback: Callable[[PromptMap], None],
        field_type: Literal["chat", "tts"],
        card_type: Union[str, None] = None,
        field: Union[str, None] = None,
        prompt: Union[str, None] = None,
    ):
        super().__init__()

        self.processor = processor
        self.on_accept_callback = on_accept_callback
        self.prompts_map = prompts_map
        self.mode = "edit" if card_type else "new"
        self.field_type = field_type
        note_types = self._get_note_types()
        selected_note_type = card_type or note_types[0]

        # Ensure there are valid fields to select
        if not len(note_types):
            show_message_box(
                "No valid note types left. Edit or delete some fields to continue!"
            )
            QTimer.singleShot(0, self.close)
            return

        default_note_state = self._state_for_new_card_type(
            selected_note_type, field_type
        )
        selected_target_field = field or default_note_state["target_field"]

        automatic = get_generate_automatically(
            selected_note_type, selected_target_field, prompts_map
        )

        per_field_settings = self.get_per_field_settings(
            selected_note_type,
            selected_target_field,
        )

        # Only if it's a new card, we need to get the fields for the selected card type
        target_fields = (
            default_note_state["target_fields"]
            if self.mode == "new"
            else get_fields(selected_note_type)
        )

        # If it's an edit, we need to get the source field from the prompt
        selected_tts_source_field = (
            (self._attempt_to_parse_source_field(prompt) or "")
            if prompt
            else default_note_state["source_field"]
        )

        initial_state: State = {
            "prompt": prompt or default_note_state["prompt"],
            # Note types
            "selected_note_type": selected_note_type,
            "note_types": note_types,
            # tts
            "tts_source_fields": default_note_state["source_fields"],
            "selected_tts_source_field": selected_tts_source_field,
            # target fields
            "note_fields": target_fields,
            "selected_note_field": selected_target_field,
            # other
            "is_loading_prompt": False,
            "generate_manually": not automatic,
            "chat_providers": ["ChatGPT", "Claude"],
            "chat_models": provider_model_map[
                chat_ui_to_provider_map[per_field_settings["chat_provider"]]
                or config.chat_provider
            ],
            **per_field_settings,
        }
        self.state = StateManager[State](initial_state)

        self.manual_box = ReactiveCheckBox(
            self.state,
            "generate_manually",
            text="Manually generate only",
        )
        self.manual_box.onChange.connect(
            lambda checked: self.state.update({"generate_manually": checked})
        )

        tabs = QTabWidget()
        tabs.addTab(self.render_main_tab(), "Main")
        tabs.addTab(self.render_options_tab(), "Options")

        container = QVBoxLayout()
        container.addWidget(tabs)
        self.setLayout(container)
        self.setup_ui()

    def get_per_field_settings(
        self, selected_card_type: str, selected_field: str
    ) -> PerFieldSettings:
        extras = get_extras(
            selected_card_type, selected_field, self.prompts_map, type=self.field_type
        )

        return {
            "chat_provider": chat_provider_to_ui_map[
                extras.get("chat_provider") or config.chat_provider
            ],
            "chat_model": extras.get("chat_model") or config.chat_model,
            "chat_temperature": extras.get("chat_temperature")
            or config.chat_temperature,
            "use_custom_model": extras["use_custom_model"],
            "type": extras["type"],
        }

    def setup_ui(self) -> None:
        self.render_ui()

    def render_ui(self) -> None:
        self.render_buttons()
        self.render_valid_fields()
        self.render_automatic_button()

    def render_main_tab(self) -> QWidget:
        layout = QVBoxLayout()

        text = (
            "New Text Field"
            if self.state.s["type"] == "chat"
            else "New Text to Speech Field"
        )
        self.setWindowTitle(text)

        self.card_combo_box = ReactiveComboBox(
            self.state, "note_types", "selected_note_type"
        )
        card_label = QLabel("Card Type")
        layout.addWidget(card_label)
        layout.addWidget(self.card_combo_box)

        if self.state.s["type"] == "tts":
            self.tts_source_combo_box = ReactiveComboBox(
                self.state, "tts_source_fields", "selected_tts_source_field"
            )
            self.tts_source_combo_box.onChange.connect(self.on_source_changed)
            source_label = QLabel("Source Field")
            layout.addWidget(source_label)
            layout.addWidget(self.tts_source_combo_box)

        self.field_combo_box = ReactiveComboBox(
            self.state, "note_fields", "selected_note_field"
        )
        field_label = QLabel("Target Field")
        layout.addWidget(field_label)
        layout.addWidget(self.field_combo_box)

        self.standard_buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.Save
        )

        self.test_button = QPushButton("Test ✨")

        prompt_label = QLabel("Prompt")
        self.prompt_text_box = ReactiveEditText(self.state, "prompt")
        self.prompt_text_box.setMinimumHeight(150)
        self.prompt_text_box.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.prompt_text_box.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.prompt_text_box.setWordWrapMode(
            QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere
        )
        self.prompt_text_box.setPlaceholderText(explanation)
        self.valid_fields = QLabel("")
        self.valid_fields.setMinimumWidth(500)
        size_policy = QSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred
        )
        size_policy.setHorizontalStretch(1)
        self.valid_fields.setSizePolicy(size_policy)
        self.valid_fields.setWordWrap(True)
        small_font = self.valid_fields.font()
        small_font.setPointSize(10)
        self.valid_fields.setFont(small_font)

        self.setLayout(layout)
        layout.addWidget(prompt_label)
        layout.addWidget(self.prompt_text_box)
        layout.addWidget(self.valid_fields)
        layout.addWidget(self.test_button)

        layout.addWidget(self.standard_buttons)

        self.state.state_changed.connect(self.render_ui)
        self.card_combo_box.onChange.connect(self._on_new_card_type_selected)
        self.field_combo_box.onChange.connect(self.on_target_field_changed)
        self.prompt_text_box.onChange.connect(
            lambda text: self.state.update({"prompt": text})
        )

        self.test_button.clicked.connect(self.on_test)
        self.standard_buttons.accepted.connect(self.on_accept)
        self.standard_buttons.rejected.connect(self.on_reject)
        container = QWidget()
        container.setLayout(layout)

        # Control visibility depending on mode
        if self.mode == "edit":
            self.card_combo_box.setEnabled(False)
            self.field_combo_box.setEnabled(False)
            if hasattr(self, "tts_source_combo_box"):
                self.tts_source_combo_box.setEnabled(False)
        return container

    def render_options_tab(self) -> QWidget:
        models_layout = default_form_layout()
        self.model_options = self.render_custom_model()
        self.model_options.setEnabled(self.state.s["use_custom_model"])
        self.custom_model = ReactiveCheckBox(self.state, "use_custom_model")
        self.custom_model.onChange.connect(
            lambda checked: self.state.update({"use_custom_model": checked})
        )
        self.state.state_changed.connect(self.on_state_update)
        models_layout.addRow("Override Default Model", self.custom_model)
        models_layout.addWidget(self.model_options)
        model_box = QGroupBox("⚙️ Model Settings")
        model_box.setLayout(models_layout)

        behavior_box = QGroupBox("Field Behavior")
        behavior_layout = default_form_layout()
        behavior_box.setLayout(behavior_layout)

        manual_explanation = QLabel("Via editor right click -> generate")
        manual_explanation.setFont(font_small)
        behavior_layout.addRow(self.manual_box)
        behavior_layout.addRow(manual_explanation)

        container_layout = default_form_layout()
        container_layout.addRow(behavior_box)
        container_layout.addRow(model_box)
        container = QWidget()
        container.setLayout(container_layout)
        return container

    def render_custom_model(self) -> QWidget:
        # TODO: encapsulate this ChatOptions state
        self.chat_options = ChatOptions(self.state)  # type: ignore
        self.tts_options = TTSOptions()
        return self.chat_options if self.state.s["type"] == "chat" else self.tts_options

    def on_state_update(self):
        self.model_options.setEnabled(self.state.s["use_custom_model"])

    def _get_note_types(self) -> List[str]:
        """Returns note types for which there are valid target fields remaining"""
        note_types = get_note_types()
        # Need to find a note type where there are valid field
        return [
            note_type
            for note_type in note_types
            if self._valid_fields_remain(note_type)
        ]

    def _valid_fields_remain(self, note_type: str) -> bool:
        target_fields = self._get_valid_target_fields(note_type)
        return len(target_fields) > 0

    def _state_for_new_card_type(
        self, note_type: str, type: Literal["chat", "tts"]
    ) -> PartialState:

        target_fields = self._get_valid_target_fields(note_type)
        target_field = target_fields[0] if len(target_fields) else "None"

        source_fields = get_fields(note_type)
        source_field = self._get_initial_source_field(note_type)
        prompt = self.get_tts_prompt(source_field) if type == "tts" else ""
        return {
            "prompt": prompt,
            "target_fields": target_fields,
            "target_field": target_field,
            "source_fields": source_fields,
            "source_field": source_field,
        }

    def _on_new_card_type_selected(self, note_type: str):
        new_state = self._state_for_new_card_type(note_type, self.state.s["type"])
        self.state.update(
            {
                "prompt": new_state["prompt"],
                "selected_note_type": note_type,
                "selected_note_field": new_state["target_field"],
                "note_fields": new_state["target_fields"],
                "tts_source_fields": new_state["source_fields"],
                "selected_tts_source_field": new_state["source_field"],
            }
        )

    def on_source_changed(self, source: str) -> None:
        self.state.update({"prompt": self.get_tts_prompt(source)})

    def get_tts_prompt(self, source: str) -> str:
        return f"{{{{{source}}}}}"

    def on_target_field_changed(self, field: Union[str, None]) -> None:
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
                # TODO: do I still need this if editing is not allowed?
                **self.get_per_field_settings(
                    self.state.s["selected_note_type"], field
                ),
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
            self.test_button.setText("Test Prompt ✨")

    def on_test(self) -> None:
        prompt = self.state.s["prompt"]

        if not mw or not prompt:
            return

        selected_note_type = self.state.s["selected_note_type"]
        error = prompt_has_error(
            prompt,
            selected_note_type,
            self.state.s["selected_note_field"],
        )

        if error:
            show_message_box(f"Invalid prompt: {error}")
            return

        sample_note_ids = mw.col.find_notes(f'note:"{selected_note_type}"')

        if not sample_note_ids:
            show_message_box("No cards found for this note type.")
            return

        sample_note = mw.col.get_note(sample_note_ids[0])
        self.state["is_loading_prompt"] = True

        def on_success(arg):

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
            msg = f"Ran with fields: \n{stringified_vals}.\n\n Response: {arg}"

            self.state["is_loading_prompt"] = False
            show_message_box(msg, custom_ok="Close")

        def on_failure(e: Exception) -> None:
            show_message_box(f"Failed to get response: {e}")
            self.state["is_loading_prompt"] = False

        self.processor.get_chat_response(
            prompt=prompt,
            note=sample_note,
            on_success=on_success,
            on_failure=on_failure,
        )

    def render_automatic_button(self) -> None:
        self.manual_box.setChecked(self.state.s["generate_manually"])

    def render_valid_fields(self) -> None:
        fields = self.get_valid_fields_for_prompt(
            self.state.s["selected_note_type"], self.state.s["selected_note_field"]
        )
        fields = ["{{" + field + "}}" for field in fields]
        text = f"Valid Fields: {', '.join(fields)}"
        self.valid_fields.setText(text)

    def get_valid_fields_for_prompt(
        self, selected_note_type: str, selected_note_field: Union[str, None] = None
    ) -> List[str]:
        """Gets all fields excluding the selected one, if one is selected"""
        fields = get_fields(selected_note_type)
        return [field for field in fields if field != selected_note_field]

    def _get_valid_target_fields(
        self, selected_note_type: str, selected_note_field: Union[str, None] = None
    ) -> List[str]:
        """Gets all fields excluding selected and existing prompts"""
        all_valid_fields = self.get_valid_fields_for_prompt(
            selected_note_type, selected_note_field
        )
        existing_prompts = set(
            get_prompts(override_prompts_map=self.prompts_map)
            .get(selected_note_type, {})
            .keys()
        )
        return [field for field in all_valid_fields if field not in existing_prompts]

    def _get_initial_source_field(self, note_type: str) -> str:
        """Get the first valid source field for a note type by finding the first field that isn't the default target field"""
        fields = get_fields(note_type)
        valid_target_fields = self._get_valid_target_fields(note_type)
        default_target_field = (
            valid_target_fields[0] if len(valid_target_fields) > 0 else None
        )
        return next(f for f in fields if f != default_target_field)

    def _attempt_to_parse_source_field(self, prompt: str) -> Union[str, None]:
        fields = get_prompt_fields(prompt, lower=False)

        if len(fields) != 1:
            return None

        return fields[0]

    def on_accept(self):
        prompt = self.state.s["prompt"]
        prompts_map = self.prompts_map
        selected_card_type = self.state.s["selected_note_type"]
        selected_field = self.state.s["selected_note_field"]

        if not prompt:
            return

        err = prompt_has_error(prompt, selected_card_type, selected_field)

        if err:
            show_message_box(f"Invalid prompt: {err}")
            return

        logger.debug(
            f"Trying to set prompt for {selected_card_type}, {selected_field}, {prompt}"
        )

        if not is_app_unlocked():
            if (
                self.state.s["use_custom_model"]
                and self.state.s["chat_provider"] != "ChatGPT"
            ):
                show_message_box(UNPAID_PROVIDER_ERROR)
                return

        is_automatic = not self.state.s["generate_manually"]

        # Add the prompt to the prompts map
        if not prompts_map["note_types"].get(selected_card_type):
            prompts_map["note_types"][selected_card_type] = {
                "fields": {},
                "extra": {},  # type: ignore
            }

        prompts_map["note_types"][selected_card_type]["fields"][selected_field] = prompt

        # Write out extras
        extras = prompts_map["note_types"][selected_card_type].get("extras")
        if not extras:
            extras = {}
            prompts_map["note_types"][selected_card_type]["extras"] = extras

        # Actually populate extras for this field
        selected_field_extras: FieldExtras = extras.get(selected_field, {})

        type = self.state.s["type"]
        selected_field_extras["type"] = type
        selected_field_extras["automatic"] = is_automatic
        is_custom = self.state.s["use_custom_model"]
        selected_field_extras["use_custom_model"] = is_custom

        # Need to delete any custom config if it's not being used
        if is_custom:
            if type == "tts":
                selected_field_extras["tts_provider"] = self.tts_options.state.s[
                    "tts_provider"
                ]
                selected_field_extras["tts_voice"] = self.tts_options.state.s[
                    "tts_voice"
                ]
            elif type == "chat":
                selected_field_extras["chat_model"] = self.state.s["chat_model"]
                selected_field_extras["chat_provider"] = chat_ui_to_provider_map[
                    self.state.s["chat_provider"]
                ]
                selected_field_extras["chat_temperature"] = self.state.s[
                    "chat_temperature"
                ]
        else:
            to_pop = [
                "chat_model",
                "chat_provider",
                "chat_temperature",
                "tts_model",
                "tts_provider",
                "tts_voice",
            ]
            for extra in to_pop:
                # TODO: fix this type ignore; can we just set them to None?
                selected_field_extras.pop(extra, None)  # type: ignore

        # Write em out
        extras[selected_field] = selected_field_extras
        self.on_accept_callback(prompts_map)
        self.accept()

    def on_reject(self):
        self.reject()
