from aqt import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QFormLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)
from PyQt6.QtCore import Qt

from ..processor import Processor

from ..config import Config, OpenAIModels, PromptMap
from .prompt_dialog import PromptDialog
from .ui_utils import show_message_box


OPTIONS_MIN_WIDTH = 750

openai_models = ["gpt-3.5-turbo", "gpt-4o", "gpt-4-turbo", "gpt-4"]


class AddonOptionsDialog(QDialog):
    api_key_edit: QLineEdit
    table_buttons: QHBoxLayout
    remove_button: QPushButton
    table: QTableWidget

    def __init__(self, config: Config, processor: Processor):
        super().__init__()
        self.processor = processor
        self.prompts_map = config.prompts_map
        self.openai_model = config.openai_model
        self.config = config
        self.selected_row = None

        self.setup_ui()

    def setup_ui(self) -> None:
        self.setWindowTitle("🤖 AI Fields Options")
        self.setMinimumWidth(OPTIONS_MIN_WIDTH)

        # Setup Widgets

        # Form
        api_key_label = QLabel("OpenAI API Key")
        api_key_label.setToolTip(
            "Get your API key from https://platform.openai.com/account/api-keys"
        )

        self.api_key_edit = QLineEdit()
        self.api_key_edit.setText(self.config.openai_api_key)
        self.api_key_edit.setPlaceholderText("sk-proj-1234...")

        # Select model
        model_label = QLabel("OpenAI Model")
        self.models_combo_box = QComboBox()
        self.models_combo_box.addItems(openai_models)
        self.models_combo_box.setCurrentText(self.openai_model)
        self.models_combo_box.currentTextChanged.connect(self.on_change_model)

        form = QFormLayout()
        form.addRow(api_key_label, self.api_key_edit)
        form.addRow(model_label, self.models_combo_box)

        # Buttons
        # TODO: Need a restore defaults button
        table_buttons = QHBoxLayout()
        add_button = QPushButton("+")
        add_button.clicked.connect(self.on_add)
        self.remove_button = QPushButton("-")
        table_buttons.addWidget(self.remove_button)
        self.remove_button.clicked.connect(self.on_remove)
        table_buttons.addWidget(add_button)

        standard_buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok
        )

        standard_buttons.accepted.connect(self.on_accept)
        standard_buttons.rejected.connect(self.on_reject)

        # Table
        self.table = self.create_table()
        self.update_table()

        # Set up layout

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(self.table)
        layout.addLayout(table_buttons)
        layout.addWidget(standard_buttons)

        self.update_buttons()
        self.setLayout(layout)

    def create_table(self) -> QTableWidget:
        table = QTableWidget(0, 3)
        table.setHorizontalHeaderLabels(["Note Type", "Field", "Prompt"])

        # Selection
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)

        # Styling
        table.horizontalHeader().setStretchLastSection(True)  # type: ignore
        table.verticalHeader().setVisible(False)  # type: ignore

        # Wire up slots
        table.currentItemChanged.connect(self.on_row_selected)
        table.itemDoubleClicked.connect(self.on_row_double_clicked)

        return table

    def update_table(self) -> None:
        self.table.setRowCount(0)

        row = 0
        for note_type, field_prompts in self.prompts_map["note_types"].items():
            for field, prompt in field_prompts["fields"].items():
                print(field, prompt)
                self.table.insertRow(self.table.rowCount())
                items = [
                    QTableWidgetItem(note_type),
                    QTableWidgetItem(field),
                    QTableWidgetItem(prompt),
                ]
                for i, item in enumerate(items):
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.table.setItem(row, i, item)
                row += 1

    def on_row_selected(self, current):
        if not current:
            self.selected_row = None
        else:
            self.selected_row = current.row()
        self.update_buttons()

    def on_row_double_clicked(self, item: QTableWidgetItem) -> None:
        print(f"Double clicked: {item.row()}")
        if self.selected_row is None:
            return

        card_type = self.table.item(self.selected_row, 0).text()
        field = self.table.item(self.selected_row, 1).text()
        prompt = self.table.item(self.selected_row, 2).text()
        print(f"Editing {card_type}, {field}")

        # TODO: mypy didn't catch the lack of processor here... dodesn't seem this like method's getting typechecked at all
        prompt_dialog = PromptDialog(
            self.prompts_map,
            self.processor,
            self.on_update_prompts,
            card_type=card_type,
            field=field,
            prompt=prompt,
        )

        if prompt_dialog.exec() == QDialog.DialogCode.Accepted:
            self.update_table()

    def update_buttons(self) -> None:
        if self.selected_row is not None:
            self.remove_button.setEnabled(True)
        else:
            self.remove_button.setEnabled(False)

    def on_add(self, _: int) -> None:
        # TODO: this is WRONG now, whhy isn't mypy catching it??!

        prompt_dialog = PromptDialog(
            self.prompts_map, self.processor, self.on_update_prompts
        )

        if prompt_dialog.exec() == QDialog.DialogCode.Accepted:
            self.update_table()

    def on_remove(self):
        if self.selected_row is None:
            # Should never happen
            return
        card_type = self.table.item(self.selected_row, 0).text()
        field = self.table.item(self.selected_row, 1).text()
        print(f"Removing {card_type}, {field}")
        self.prompts_map["note_types"][card_type]["fields"].pop(field)
        self.update_table()

    def on_change_model(self, text: OpenAIModels):
        if self.openai_model == "gpt-3.5-turbo" and text and text != self.openai_model:
            warning = f"Continue with {text}?"
            informative = "Only paid API tiers can use models other than gpt-3.5-turbo."

            should_continue = show_message_box(
                warning, details=informative, show_cancel=True
            )

            if should_continue:
                self.openai_model = text
            else:
                # Otherwise, reset the combo box
                self.models_combo_box.setCurrentText(self.openai_model)

        else:
            self.openai_model = text

    def on_accept(self):
        self.config.openai_api_key = self.api_key_edit.text()
        self.config.prompts_map = self.prompts_map
        self.config.openai_model = self.openai_model
        self.accept()

    def on_reject(self):
        self.reject()

    def on_update_prompts(self, prompts_map: PromptMap):
        self.prompts_map = prompts_map
