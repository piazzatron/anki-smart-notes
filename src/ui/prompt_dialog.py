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

from typing import Any, Callable, Dict, List, TypedDict, Union

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
    get_prompt_fields_lower,
    get_prompts,
    interpolate_prompt,
    prompt_has_error,
)
from ..utils import get_fields, to_lowercase_dict
from .ui_utils import show_message_box

explanation = """Write a "prompt" to help ChatGPT generate your target smart field.

You may reference any other field via enclosing it in {{double curly braces}}. Valid fields are listed below for convenience.

Test out your prompt with the test button before saving it!
"""


class State(TypedDict):
    prompts_map: PromptMap
    is_loading_prompt: bool
    prompt: str
    selected_field: str
    selected_card_type: str


class PromptDialog(QDialog):
    prompt_text_box: QTextEdit
    test_button: QPushButton
    valid_fields: QLabel
    card_combo_box: QComboBox
    state: State
    rendering: bool

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
        self.rendering = False

        card_types = self.get_card_types()
        selected_card_type = card_type or card_types[0]
        self.state = {
            "prompt": prompt or "",
            "is_loading_prompt": False,
            "selected_field": field or get_fields(selected_card_type)[0],
            "selected_card_type": selected_card_type,
            "prompts_map": prompts_map,
        }

        self.setup_ui()

    def set_state(self, updates: Dict[str, Any]) -> None:
        if self.rendering:
            return

        new_state: State = dict(self.state)  # type: ignore

        for key, value in updates.items():
            assert key in new_state
            new_state[key] = value  # type: ignore

        if new_state != self.state:
            print("STATE UPDATE")
            print(self.state)
            print(new_state)
            self.state = new_state
            self.render_ui()

    def setup_ui(self) -> None:
        self.setWindowTitle("New Smart Field")
        self.card_combo_box = QComboBox()
        self.card_combo_box.addItems(self.get_card_types())

        self.field_combo_box = QComboBox()

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
        self.prompt_text_box = QTextEdit()
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

        self.setLayout(layout)
        layout.addWidget(prompt_label)
        layout.addWidget(self.prompt_text_box)
        layout.addWidget(self.valid_fields)
        layout.addWidget(self.test_button)
        layout.addWidget(self.standard_buttons)

        self.card_combo_box.currentTextChanged.connect(self.on_card_type_selected)
        self.prompt_text_box.textChanged.connect(
            lambda: self.set_state({"prompt": self.prompt_text_box.toPlainText()})
        )
        self.field_combo_box.currentTextChanged.connect(self.on_field_changed)
        self.test_button.clicked.connect(self.on_test)
        self.standard_buttons.accepted.connect(self.on_accept)
        self.standard_buttons.rejected.connect(self.on_reject)

        self.render_ui()

    def render_ui(self) -> None:
        self.rendering = True
        self.render_card_types()
        self.render_fields()
        self.render_buttons()
        self.render_prompt()
        self.render_valid_fields()
        self.rendering = False

    def get_card_types(self) -> List[str]:
        if not mw:
            return []

        # Including this function in a little UI
        # class is a horrible violation of separation of concerns
        # but I won't tell anybody if you don't

        models = mw.col.models.all()
        return [model["name"] for model in models]

    def on_card_type_selected(self, card_type: str):
        selected_field = get_fields(card_type)[0]
        prompt = get_prompts().get(card_type, {}).get(selected_field, "")
        self.set_state(
            {
                "selected_card_type": card_type,
                "selected_field": selected_field,
                "prompt": prompt,
            }
        )

    def on_field_changed(self, field: Union[str, None]) -> None:
        # Field can be none because we reset the combo box in render. Make sure not to update state to None
        print("FIELD CHANGED")
        if not field:
            return

        prompt = get_prompts().get(self.state["selected_card_type"], {}).get(field, "")
        self.set_state({"selected_field": field, "prompt": prompt})

    def render_card_types(self) -> None:
        self.card_combo_box.setCurrentText(self.state["selected_card_type"])
        self.field_combo_box.clear()
        self.field_combo_box.addItems(get_fields(self.state["selected_card_type"]))

    def render_fields(self) -> None:
        # Need to make sure that this render doesn't trigger a state update
        try:
            self.field_combo_box.currentTextChanged.disconnect(self.on_field_changed)
        except Exception:
            pass

        self.field_combo_box.clear()
        self.field_combo_box.addItems(get_fields(self.state["selected_card_type"]))
        self.field_combo_box.setCurrentText(self.state["selected_field"])

        self.field_combo_box.currentTextChanged.connect(self.on_field_changed)

    def render_buttons(self) -> None:
        is_enabled = bool(self.state["prompt"]) and not self.state["is_loading_prompt"]
        self.test_button.setEnabled(is_enabled)
        self.standard_buttons.button(QDialogButtonBox.StandardButton.Save).setEnabled(  # type: ignore
            is_enabled
        )

        if self.state["is_loading_prompt"]:
            self.test_button.setText("Loading...")
        else:
            self.test_button.setText("Test Prompt ✨")

    def render_prompt(self) -> None:
        # Need to store cursor
        cursor = self.prompt_text_box.cursor()
        self.prompt_text_box.setText(self.state["prompt"])
        self.prompt_text_box.setTextCursor(cursor)

    def on_test(self) -> None:
        prompt = self.state["prompt"]

        if not mw or not prompt:
            return

        error = prompt_has_error(
            prompt,
            self.state["selected_card_type"],
            self.state["selected_field"],
        )

        if error:
            show_message_box(f"Invalid prompt: {error}")
            return

        selected_card_type = self.state["selected_card_type"]
        sample_note_ids = mw.col.find_notes(f'note:"{selected_card_type}"')

        if not sample_note_ids:
            show_message_box("No cards found for this note type.")
            return

        sample_note = mw.col.get_note(sample_note_ids[0])

        # TODO
        prompt = interpolate_prompt(prompt, sample_note)
        if not prompt:
            return

        self.set_state({"is_loading_prompt": True})

        def on_success(arg):
            prompt = self.state["prompt"]
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

            self.set_state({"is_loading_prompt": False})
            show_message_box(msg, custom_ok="Close")

        def on_failure(e: Exception) -> None:
            self.set_state({"is_loading_prompt": False})

        self.processor.get_chat_response(
            prompt, on_success=on_success, on_failure=on_failure
        )

    def render_valid_fields(self) -> None:
        fields = self.get_valid_fields()
        fields = ["{{" + field + "}}" for field in fields]
        text = f"Fields: {', '.join(fields)}"
        self.valid_fields.setText(text)

    def get_valid_fields(self) -> List[str]:
        fields = get_fields(self.state["selected_card_type"])
        existing_prompts = set(
            get_prompts().get(self.state["selected_card_type"], {}).keys()
        )
        existing_prompts.add(self.state["selected_field"])

        not_ai_fields = [field for field in fields if field not in existing_prompts]
        return not_ai_fields

    def on_accept(self):
        prompt = self.state["prompt"]
        prompts_map = self.state["prompts_map"]
        selected_card_type = self.state["selected_card_type"]
        selected_field = self.state["selected_field"]

        if not prompt:
            return

        err = prompt_has_error(prompt, selected_card_type, selected_field)

        if err:
            show_message_box(f"Invalid prompt: {err}")
            return

        logger.debug(
            f"Trying to set prompt for {selected_card_type}, {selected_field}, {prompt}"
        )

        # Add the prompt to the prompts map
        if not prompts_map.get(selected_card_type):
            prompts_map["note_types"][selected_card_type] = {"fields": {}, "extra": {}}

        prompts_map["note_types"][selected_card_type]["fields"][selected_field] = prompt
        self.on_accept_callback(prompts_map)
        self.accept()

    def on_reject(self):
        self.reject()
