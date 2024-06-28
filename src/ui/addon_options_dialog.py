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

from aqt import (QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFormLayout,
                 QGroupBox, QHBoxLayout, QLabel, QLineEdit, QPushButton,
                 QSizePolicy, QTableWidget, QTableWidgetItem, QTabWidget,
                 QVBoxLayout, QWidget)
from PyQt6.QtCore import Qt

from ..config import Config, OpenAIModels, PromptMap
from ..logger import logger
from ..processor import Processor
from .prompt_dialog import PromptDialog
from .ui_utils import show_message_box

OPTIONS_MIN_WIDTH = 750

openai_models = ["gpt-3.5-turbo", "gpt-4o", "gpt-4-turbo", "gpt-4"]


class AddonOptionsDialog(QDialog):
    api_key_edit: QLineEdit
    table_buttons: QHBoxLayout
    remove_button: QPushButton
    table: QTableWidget
    restore_defaults: QPushButton
    edit_button: QPushButton
    generate_at_review: bool

    def __init__(self, config: Config, processor: Processor):
        super().__init__()
        self.processor = processor
        self.prompts_map = config.prompts_map
        self.openai_model = config.openai_model
        self.generate_at_review = config.generate_at_review
        self.config = config
        self.selected_row = None

        self.setup_ui()

    def setup_ui(self) -> None:
        self.setWindowTitle("Smart Notes ✨")
        self.setMinimumWidth(OPTIONS_MIN_WIDTH)

        title_box = QWidget()
        title_box_layout = QHBoxLayout()
        title_box.setLayout(title_box_layout)
        title = QLabel("<h2>Smart Notes</h2>")
        subtitle = QLabel("v0.1.0")  # TODO: reference the version somewhere
        title_box_layout.addWidget(title)
        title_box_layout.addWidget(subtitle)

        # Form
        get_api_key_label = QLabel(
            "An API key is required. Free tier use is limited to three requests per minute. <a href='https://platform.openai.com/account/api-keys/'>Get an API key.</a>"
        )
        font = get_api_key_label.font()
        font.setPointSize(10)
        get_api_key_label.setOpenExternalLinks(True)
        get_api_key_label.setFont(font)

        self.api_key_edit = QLineEdit()
        self.api_key_edit.setPlaceholderText("sk-proj-1234...")
        self.api_key_edit.setMinimumWidth(500)
        self.api_key_edit.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )

        # Select model
        self.models_combo_box = QComboBox()
        self.models_combo_box.addItems(openai_models)
        self.models_combo_box.currentTextChanged.connect(
            lambda text: setattr(self, "openai_model", text)
        )

        form = QFormLayout()
        form.setVerticalSpacing(12)
        form.addRow("<b>🔑 OpenAI API Key:</b>", self.api_key_edit)
        form.addRow(get_api_key_label)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        group_box = QGroupBox("API Key")
        group_box.setLayout(form)

        # Buttons
        # TODO: Need a restore defaults button
        table_buttons = QHBoxLayout()
        add_button = QPushButton("Add")
        add_button.clicked.connect(self.on_add)
        self.remove_button = QPushButton("Remove")
        self.edit_button = QPushButton("Edit")
        self.edit_button.clicked.connect(self.on_edit)
        table_buttons.addWidget(self.remove_button, 1)
        table_buttons.addWidget(self.edit_button, 1)
        self.remove_button.clicked.connect(self.on_remove)
        table_buttons.addWidget(add_button, 2, Qt.AlignmentFlag.AlignRight)

        standard_buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok
        )
        self.restore_defaults = QPushButton("Restore Defaults")
        standard_buttons.addButton(
            self.restore_defaults, QDialogButtonBox.ButtonRole.ResetRole
        )
        self.restore_defaults.clicked.connect(self.on_restore_defaults)

        standard_buttons.accepted.connect(self.on_accept)
        standard_buttons.rejected.connect(self.on_reject)

        # Table
        self.table = self.create_table()
        self.update_table()

        # Set up layout

        tabs = QTabWidget()

        explanation = QLabel(
            "Automatically generate fields per note type. Reference any existing field in your prompt with {{double curly braces}}."
        )
        explanation.setFont(font)
        layout = QVBoxLayout()
        layout.addWidget(group_box)
        layout.addSpacing(24)
        layout.addWidget(QLabel("<h3>✨ Smart Fields</h3>"))
        layout.addWidget(explanation)
        layout.addSpacing(16)
        layout.addWidget(self.table)
        layout.addLayout(table_buttons)

        tab1 = QWidget()
        tab1.setLayout(layout)
        tabs.addTab(tab1, "General")

        # Tab2

        learn_more_about_models = QLabel(
            'Newer models (GPT-4o, etc) will perform better with lower rate limits and higher cost. <a href="https://platform.openai.com/docs/models/">Learn more.</a>'
        )
        learn_more_about_models.setOpenExternalLinks(True)
        learn_more_about_models.setFont(font)
        tab2 = QWidget()
        tab2_layout = QFormLayout()
        tab2_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        tab2_layout.setFormAlignment(Qt.AlignmentFlag.AlignLeft)
        tab2_layout.addRow("OpenAI Model:", self.models_combo_box)
        tab2_layout.addRow(learn_more_about_models)
        # Add spacer row
        tab2_layout.addRow("", QLabel(""))

        self.generate_at_review_button = QCheckBox()

        def set_generate_at_review(checked: int):
            self.generate_at_review = checked == 2

        self.generate_at_review_button.stateChanged.connect(set_generate_at_review)
        tab2_layout.addRow(
            "Auto-generate fields at review time:", self.generate_at_review_button
        )

        tab2.setLayout(tab2_layout)
        tabs.addTab(tab2, "Advanced")

        tab_layout = QVBoxLayout()
        # TODO: add back
        # tab_layout.addWidget(title_box)
        tab_layout.addWidget(tabs)
        tab_layout.addSpacing(24)

        tab_layout.addWidget(standard_buttons)

        self.update_buttons()
        self.setLayout(tab_layout)
        self.update_ui()

    def update_ui(self) -> None:
        self.api_key_edit.setText(self.config.openai_api_key)
        self.models_combo_box.setCurrentText(self.openai_model)
        self.generate_at_review_button.setChecked(self.generate_at_review)
        self.update_table()

    def create_table(self) -> QTableWidget:
        table = QTableWidget(0, 3)
        table.setHorizontalHeaderLabels(["Note Type", "Target Field", "Prompt"])

        # Selection
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)

        # Styling
        table.horizontalHeader().setStretchLastSection(True)  # type: ignore
        table.verticalHeader().setVisible(False)  # type: ignore

        # Wire up slots
        table.currentItemChanged.connect(self.on_row_selected)
        table.itemDoubleClicked.connect(self.on_edit)

        return table

    def update_table(self) -> None:
        self.table.setRowCount(0)

        row = 0
        for note_type, field_prompts in self.prompts_map["note_types"].items():
            for field, prompt in field_prompts["fields"].items():
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

    def on_edit(self, _) -> None:
        if self.selected_row is None:
            return

        card_type = self.table.item(self.selected_row, 0).text()
        field = self.table.item(self.selected_row, 1).text()
        prompt = self.table.item(self.selected_row, 2).text()
        logger.debug(f"Editing {card_type}, {field}")

        # Save out API key jic
        self.config.openai_api_key = self.api_key_edit.text()

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
        is_enabled = self.selected_row is not None
        self.remove_button.setEnabled(is_enabled)
        self.edit_button.setEnabled(is_enabled)

    def on_add(self, _: int) -> None:
        # Save out the API key in case it's been updated this run
        self.config.openai_api_key = self.api_key_edit.text()

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
        logger.debug(f"Removing {card_type}, {field}")
        self.prompts_map["note_types"][card_type]["fields"].pop(field)
        self.update_table()

    def on_accept(self) -> None:
        self.config.openai_api_key = self.api_key_edit.text()
        self.config.prompts_map = self.prompts_map
        self.config.openai_model = self.openai_model
        self.config.generate_at_review = self.generate_at_review
        self.accept()

    def on_reject(self) -> None:
        self.reject()

    def on_update_prompts(self, prompts_map: PromptMap) -> None:
        self.prompts_map = prompts_map

    def on_restore_defaults(self) -> None:
        # TODO: this is so brittle
        self.config.restore_defaults()
        self.prompts_map = self.config.prompts_map
        self.openai_model = self.config.openai_model
        self.generate_at_review = self.config.generate_at_review
        self.update_ui()
