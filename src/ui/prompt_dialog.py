from typing import Callable, List, Union
from ..processor import Processor

from aqt import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QPushButton,
    QTextEdit,
    QTextOption,
    QVBoxLayout,
    Qt,
    mw,
)
from ..config import PromptMap
from ..prompts import get_prompt_fields_lower, interpolate_prompt, validate_prompt
from .ui_utils import show_message_box
from ..utils import get_fields, run_async_in_background, to_lowercase_dict


class PromptDialog(QDialog):
    prompt_text_box: QTextEdit
    is_loading_prompt: bool
    test_button: QPushButton

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

        self.card_types = self.get_card_types()
        self.selected_card_type = card_type or self.card_types[0]

        self.fields = get_fields(self.selected_card_type)
        self.selected_field = field or get_fields(self.selected_card_type)[0]

        self.prompt = prompt
        self.is_loading_prompt = False

        self.setup_ui()

    def setup_ui(self) -> None:
        self.setWindowTitle("New Smart Field")
        card_combo_box = QComboBox()

        self.field_combo_box = QComboBox()

        card_combo_box.addItems(self.card_types)

        card_combo_box.setCurrentText(self.selected_card_type)
        card_combo_box.currentTextChanged.connect(self.on_card_type_selected)

        card_label = QLabel("Card Type")
        field_label = QLabel("Target Field")
        layout = QVBoxLayout()
        layout.addWidget(card_label)
        layout.addWidget(card_combo_box)
        layout.addWidget(field_label)
        layout.addWidget(self.field_combo_box)

        standard_buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.Save
        )

        self.test_button = QPushButton("Test Prompt ✨")
        self.test_button.clicked.connect(self.on_test)
        standard_buttons.accepted.connect(self.on_accept)
        standard_buttons.rejected.connect(self.on_reject)

        prompt_label = QLabel("Prompt")
        self.prompt_text_box = QTextEdit()
        self.prompt_text_box.textChanged.connect(self.on_text_changed)
        self.prompt_text_box.setMinimumHeight(150)
        self.prompt_text_box.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.prompt_text_box.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.prompt_text_box.setWordWrapMode(
            QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere
        )
        self.prompt_text_box.setPlaceholderText(
            "Write a simple sentence in Japanese for the word {{expression}}."
        )

        self.update_prompt()
        self.setLayout(layout)
        layout.addWidget(prompt_label)
        layout.addWidget(self.prompt_text_box)
        layout.addWidget(self.test_button)
        layout.addWidget(standard_buttons)

        self.update_test_button()
        # This needs to be called at the end
        # once the widgets are set up
        self.update_fields()
        # Very brittle; this needs to be called after update_fields
        # because otherwise update_fields will clear out the field combo box,
        # causing it to default select the first field in the list
        self.field_combo_box.currentTextChanged.connect(self.on_field_selected)

    def get_card_types(self) -> List[str]:
        if not mw:
            return []

        # Including this function in a little UI
        # class is a horrible violation of separation of concerns
        # but I won't tell anybody if you don't

        models = mw.col.models.all()
        return [model["name"] for model in models]

    def on_field_selected(self, field: str):
        print(f"Field selected: {field}")
        if not field:
            return
        self.selected_field = field
        self.update_prompt()

    def on_card_type_selected(self, card_type: str):
        if not card_type:
            return
        self.selected_card_type = card_type

        self.update_fields()
        self.update_prompt()

    def update_fields(self) -> None:
        if not self.selected_card_type:
            return

        self.fields = get_fields(self.selected_card_type)

        self.field_combo_box.clear()
        self.field_combo_box.addItems(self.fields)
        print(f"Attempting to set field to {self.selected_field}")
        self.field_combo_box.setCurrentText(self.selected_field)

    def update_test_button(self) -> None:
        is_enabled = (
            bool(self.selected_card_type and self.selected_field and self.prompt)
            and not self.is_loading_prompt
        )
        self.test_button.setEnabled(is_enabled)
        if self.is_loading_prompt:
            self.test_button.setText("Loading...")
        else:
            self.test_button.setText("Test Prompt ✨")

    def update_prompt(self) -> None:
        if not self.selected_field or not self.selected_card_type:
            self.prompt_text_box.setText("")
            return

        prompt = (
            self.prompts_map.get("note_types", {})  # type: ignore
            .get(self.selected_card_type, {})
            .get("fields", {})
            .get(self.selected_field, "")
        )
        self.prompt_text_box.setText(prompt)

    def on_text_changed(self):
        self.prompt = self.prompt_text_box.toPlainText()
        self.update_test_button()

    def on_test(self):
        if not mw or not self.prompt:
            return

        if self.selected_card_type and self.selected_field and self.prompt:
            if not validate_prompt(self.prompt, self.selected_card_type):
                show_message_box("Invalid prompt. Please ensure all fields are valid.")
                return

        sample_note_ids = mw.col.find_notes(f'note:"{self.selected_card_type}"')

        if not sample_note_ids:
            show_message_box("No cards found for this note type.")
            return

        sample_note = mw.col.get_note(sample_note_ids[0])
        prompt = interpolate_prompt(self.prompt, sample_note)
        self.is_loading_prompt = True
        self.update_test_button()

        def on_success(arg):
            if not self.prompt:
                return

            self.is_loading_prompt = False
            self.update_test_button()

            prompt_fields = get_prompt_fields_lower(self.prompt)

            # clumsy stuff to make it work with lowercase fields...
            fields = to_lowercase_dict(sample_note)  # type: ignore
            field_map = {
                prompt_field: fields[prompt_field] for prompt_field in prompt_fields
            }

            stringified_vals = "\n".join([f"{k}: {v}" for k, v in field_map.items()])
            msg = f"Ran with fields: \n{stringified_vals}.\n\n Response: {arg}"

            show_message_box(msg, custom_ok="Close")

        self.processor.get_chat_response(prompt, on_success)

    def on_accept(self):
        if self.selected_card_type and self.selected_field and self.prompt:
            if not validate_prompt(
                self.prompt, self.selected_card_type, self.selected_field
            ):
                show_message_box(
                    "Invalid prompt. Please ensure all fields are valid and do not reference the target field."
                )
                return

            # IDK if this is gonna work on the config object? I think not...
            print(
                f"Trying to set prompt for {self.selected_card_type}, {self.selected_field}, {self.prompt}"
            )
            if not self.prompts_map["note_types"].get(self.selected_card_type):
                self.prompts_map["note_types"][self.selected_card_type] = {"fields": {}}
            self.prompts_map["note_types"][self.selected_card_type]["fields"][
                self.selected_field
            ] = self.prompt
            self.on_accept_callback(self.prompts_map)
        self.accept()

    def on_reject(self):
        self.reject()
