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

from typing import Callable, List, TypedDict, Union

from aqt import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QPushButton,
    QSizePolicy,
    Qt,
    QTextEdit,
    QTextOption,
    QVBoxLayout,
    mw,
)

from ..config import PromptMap
from ..logger import logger
from ..processor import Processor
from ..prompts import (
    get_generate_automatically,
    get_prompt_fields_lower,
    get_prompts,
    interpolate_prompt,
    prompt_has_error,
)
from ..utils import get_fields, to_lowercase_dict
from .reactive_check_box import ReactiveCheckBox
from .reactive_combo_box import ReactiveComboBox
from .reactive_edit_text import ReactiveEditText
from .state_manager import StateManager
from .ui_utils import show_message_box

explanation = """Write a "prompt" to help ChatGPT generate your target smart field.

You may reference any other field via enclosing it in {{double curly braces}}. Valid fields are listed below for convenience.

Test out your prompt with the test button before saving it!
"""


class StateType(TypedDict):
    prompts_map: PromptMap


class ReactiveState(TypedDict):
    prompt: str
    note_types: List[str]
    selected_note_type: str
    note_fields: List[str]
    selected_note_field: str
    is_loading_prompt: bool
    generate_automatically: bool


class PromptDialog(QDialog):
    prompt_text_box: QTextEdit
    test_button: QPushButton
    valid_fields: QLabel
    card_combo_box: QComboBox
    state: StateManager[ReactiveState]
    prompts_map: PromptMap

    def __init__(
        self,
        prompts_map: PromptMap,
        processor: Processor,
        on_accept_callback: Callable[[PromptMap], None],
        card_type: Union[str, None] = None,
        field: Union[str, None] = None,
        prompt: Union[str, None] = None,
    ):
        super().__init__()
        self.processor = processor
        self.on_accept_callback = on_accept_callback
        self.prompts_map = prompts_map

        note_types = self.get_note_types()
        selected_card_type = card_type or note_types[0]
        note_fields = get_fields(selected_card_type)
        selected_field = field or note_fields[0]
        automatic = get_generate_automatically(
            selected_card_type, selected_field, prompts_map
        )

        self.state = StateManager[ReactiveState](
            {
                "prompt": prompt or "",
                "note_types": note_types,
                "selected_note_type": selected_card_type,
                "note_fields": note_fields,
                "selected_note_field": selected_field,
                "is_loading_prompt": False,
                "generate_automatically": automatic,
            }
        )

        self.setup_ui()

    def setup_ui(self) -> None:
        self.setWindowTitle("New Smart Field")
        self.card_combo_box = ReactiveComboBox(
            self.state, "note_types", "selected_note_type"
        )

        self.field_combo_box = ReactiveComboBox(
            self.state, "note_fields", "selected_note_field"
        )

        card_label = QLabel("Card Type")
        field_label = QLabel("Target Field")
        layout = QVBoxLayout()
        layout.addWidget(card_label)
        layout.addWidget(self.card_combo_box)
        layout.addWidget(field_label)
        layout.addWidget(self.field_combo_box)

        self.standard_buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.Save
        )

        self.test_button = QPushButton("Test ✨")

        prompt_label = QLabel("ChatGPT Prompt")
        self.prompt_text_box = ReactiveEditText(self.state, "prompt")
        self.prompt_text_box.setMinimumHeight(150)
        self.prompt_text_box.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.prompt_text_box.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.prompt_text_box.setWordWrapMode(
            QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere
        )
        self.prompt_text_box.setPlaceholderText(explanation)
        self.valid_fields = QLabel("")
        self.valid_fields.setMinimumWidth(300)
        size_policy = QSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred
        )
        size_policy.setHorizontalStretch(1)
        self.valid_fields.setSizePolicy(size_policy)
        self.valid_fields.setWordWrap(True)
        font = self.valid_fields.font()
        font.setPointSize(10)
        self.valid_fields.setFont(font)
        self.automatic_box = ReactiveCheckBox(
            self.state, "generate_automatically", text="Always Generate Smart Field"
        )

        self.setLayout(layout)
        layout.addWidget(prompt_label)
        layout.addWidget(self.prompt_text_box)
        layout.addWidget(self.valid_fields)
        layout.addWidget(self.test_button)
        layout.addWidget(self.automatic_box)
        layout.addWidget(self.standard_buttons)

        self.state.state_changed.connect(self.render_ui)
        self.card_combo_box.onChange.connect(self.on_card_type_selected)
        self.field_combo_box.onChange.connect(self.on_field_changed)
        self.prompt_text_box.onChange.connect(
            lambda text: self.state.update({"prompt": text})
        )

        self.test_button.clicked.connect(self.on_test)
        self.standard_buttons.accepted.connect(self.on_accept)
        self.standard_buttons.rejected.connect(self.on_reject)
        self.automatic_box.onChange.connect(
            lambda checked: self.state.update({"generate_automatically": checked})
        )

        self.render_ui()

    def render_ui(self) -> None:
        self.render_buttons()
        self.render_valid_fields()
        self.render_automatic_button()

    def get_note_types(self) -> List[str]:
        if not mw:
            return []

        # Including this function in a little UI
        # class is a horrible violation of separation of concerns
        # but I won't tell anybody if you don't

        models = mw.col.models.all()
        return [model["name"] for model in models]

    def on_card_type_selected(self, card_type: str):
        if card_type == self.state.s["selected_note_type"]:
            return

        fields = get_fields(card_type)
        selected_field = fields[0]
        prompt = get_prompts().get(card_type, {}).get(selected_field, "")

        self.state.update(
            {
                "prompt": prompt,
                "selected_note_type": card_type,
                "selected_note_field": selected_field,
                "note_fields": fields,
            }
        )

    def on_field_changed(self, field: Union[str, None]) -> None:
        # This shouldn't happen
        if not field:
            return

        prompt = (
            get_prompts().get(self.state.s["selected_note_type"], {}).get(field, "")
        )

        self.state.update({"prompt": prompt, "selected_note_field": field})

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

        # TODO: BUG HERE!
        prompt = interpolate_prompt(prompt, sample_note)
        if not prompt:
            return

        self.state["is_loading_prompt"] = True

        def on_success(arg):

            prompt = self.state.s["prompt"]
            if not prompt:
                return

            prompt_fields = get_prompt_fields_lower(prompt)

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
            self.state["is_loading_prompt"] = False

        self.processor.get_chat_response(
            prompt, on_success=on_success, on_failure=on_failure
        )

    def render_valid_fields(self) -> None:
        fields = self.get_valid_fields()
        fields = ["{{" + field + "}}" for field in fields]
        text = f"Fields: {', '.join(fields)}"
        self.valid_fields.setText(text)

    def render_automatic_button(self) -> None:
        self.automatic_box.setChecked(self.state.s["generate_automatically"])

    def get_valid_fields(self) -> List[str]:
        selected_note_type = self.state.s["selected_note_type"]
        selected_field = self.state.s["selected_note_field"]
        fields = get_fields(selected_note_type)
        existing_prompts = set(get_prompts().get(selected_note_type, {}).keys())
        existing_prompts.add(selected_field)

        not_ai_fields = [field for field in fields if field not in existing_prompts]
        return not_ai_fields

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

        is_automatic = self.state.s["generate_automatically"]

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

        if not extras.get(selected_field):
            extras[selected_field] = {}  # type: ignore

        extras[selected_field]["automatic"] = is_automatic

        self.on_accept_callback(prompts_map)
        self.accept()

    def on_reject(self):
        self.reject()
