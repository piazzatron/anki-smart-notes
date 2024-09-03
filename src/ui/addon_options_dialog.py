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

import copy
from typing import List, TypedDict, Union
from urllib.parse import urlparse

from aqt import (
    QDialog,
    QDialogButtonBox,
    QGraphicsOpacityEffect,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from PyQt6.QtCore import Qt

from ..app_state import AppState, app_state, is_app_unlocked
from ..config import PromptMap, config
from ..constants import UNPAID_PROVIDER_ERROR
from ..logger import logger
from ..models import (
    ChatModels,
    ChatProviders,
    OpenAIModels,
    TTSProviders,
    legacy_openai_chat_models,
)
from ..processor import Processor
from ..prompts import get_extras, get_prompts
from .account_options import AccountOptions
from .changelog import get_version
from .chat_options import ChatOptions, provider_model_map
from .prompt_dialog import PromptDialog
from .reactive_check_box import ReactiveCheckBox
from .reactive_combo_box import ReactiveComboBox
from .reactive_line_edit import ReactiveLineEdit
from .state_manager import StateManager
from .subscription_box import SubscriptionBox
from .tts_options import TTSOptions, TTSState
from .ui_utils import default_form_layout, font_large, font_small, show_message_box

OPTIONS_MIN_WIDTH = 875


class State(TypedDict):
    openai_api_key: Union[str, None]
    prompts_map: PromptMap
    openai_model: OpenAIModels
    openai_models: List[OpenAIModels]
    selected_row: Union[int, None]
    generate_at_review: bool
    regenerate_notes_when_batching: bool
    openai_endpoint: Union[str, None]
    allow_empty_fields: bool
    debug: bool

    # Chat Options
    chat_provider: ChatProviders
    chat_providers: List[ChatProviders]
    chat_models: List[ChatModels]
    chat_model: ChatModels
    chat_temperature: int

    # TTS
    tts_provider: Union[TTSProviders, None]
    tts_voice: Union[str, None]
    tts_model: Union[str, None]


class AddonOptionsDialog(QDialog):
    api_key_edit: ReactiveLineEdit[State]
    table_buttons: QHBoxLayout
    remove_button: QPushButton
    table: QTableWidget
    restore_defaults: QPushButton
    edit_button: QPushButton
    state: StateManager[State]

    def __init__(self, processor: Processor):
        super().__init__()
        self.processor = processor
        self.state = StateManager[State](self.make_initial_state())
        self.setup_ui()
        app_state._state.bind(self)

    def setup_ui(self) -> None:
        self.setWindowTitle("Smart Notes ✨")
        self.setMinimumWidth(OPTIONS_MIN_WIDTH)

        # Form

        self.openai_legacy_combo_box = ReactiveComboBox(
            self.state, "legacy_openai_models", "legacy_openai_model"
        )

        # Buttons
        table_buttons = QHBoxLayout()
        add_button = QPushButton("💬 New Text Field")
        add_button.clicked.connect(lambda _: self.on_add(False))
        self.voice_button = QPushButton("🔈 New TTS Field")
        self.voice_button.clicked.connect(lambda _: self.on_add(True))
        self.remove_button = QPushButton("Remove")
        self.remove_button.setFixedWidth(75)
        self.edit_button = QPushButton("Edit")
        self.edit_button.setFixedWidth(75)
        self.edit_button.clicked.connect(self.on_edit)
        table_buttons.addWidget(self.remove_button, 1)
        table_buttons.addWidget(self.edit_button, 1)
        self.remove_button.clicked.connect(self.on_remove)
        table_buttons.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Policy.Expanding))
        table_buttons.addWidget(self.voice_button, Qt.AlignmentFlag.AlignRight)
        self.voice_button.setFixedWidth(150)
        add_button.setFixedWidth(150)
        table_buttons.addWidget(add_button, Qt.AlignmentFlag.AlignRight)

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

        # Set up layout

        tabs = QTabWidget()

        explanation = QLabel("Automatically generate text and voice fields.")
        explanation.setFont(font_small)
        layout = QVBoxLayout()

        subscription_box = SubscriptionBox()

        layout.addWidget(subscription_box)
        layout.addSpacing(24)
        layout.addWidget(QLabel("<h3>✨ Smart Fields</h3>"))
        layout.addWidget(explanation)
        layout.addSpacing(16)
        layout.addWidget(self.table)
        layout.addLayout(table_buttons)

        general_tab = QWidget()
        general_tab.setLayout(layout)
        tabs.addTab(general_tab, "General")
        tabs.addTab(self.render_chat_tab(), "Language Model")
        # Store a ref so we can enable/disable it
        self.tts_tab = self.render_tts_tab()
        tabs.addTab(self.tts_tab, "TTS")
        tabs.addTab(self.render_plugin_tab(), "Advanced")
        tabs.addTab(self.render_account_tab(), "Account")

        tab_layout = QVBoxLayout()
        tab_layout.addWidget(tabs)

        # Version Box

        version_box = QWidget()
        version_box_layout = QHBoxLayout()
        version_box_layout.setContentsMargins(0, 0, 12, 0)
        version_box.setLayout(version_box_layout)
        support_label = QLabel(
            "Found a bug or have a feature request? <a href='https://github.com/piazzatron/anki-smart-notes/issues'>Create an issue on Github</a> or email <a href='mailto:support@smart-notes.xyz'>support@smart-notes.xyz</a>."
        )
        support_label.setFont(font_small)
        support_label.setOpenExternalLinks(True)
        version_label = QLabel(f"Smart Notes v{get_version()}")
        version_label.setFont(font_small)
        version_box_layout.addWidget(support_label)
        version_box_layout.addStretch()
        version_box_layout.addWidget(version_label)

        opacity_effect = QGraphicsOpacityEffect()
        opacity_effect.setOpacity(0.3)
        opacity_effect2 = QGraphicsOpacityEffect()
        opacity_effect2.setOpacity(0.7)

        version_label.setGraphicsEffect(opacity_effect)
        support_label.setGraphicsEffect(opacity_effect2)

        tab_layout.addWidget(version_box)

        tab_layout.addSpacing(12)
        tab_layout.addWidget(standard_buttons)

        self.setLayout(tab_layout)
        self.state.state_changed.connect(self.render_ui)
        self.render_ui()

    def render_openai_api_key_box(self) -> QWidget:
        get_api_key_label = QLabel(
            "A paid OpenAI API key is required. <a href='https://platform.openai.com/account/api-keys/'>Get an API key.</a>"
        )
        get_api_key_label.setOpenExternalLinks(True)
        get_api_key_label.setFont(font_small)

        self.api_key_edit = ReactiveLineEdit(self.state, "openai_api_key")
        self.api_key_edit.setPlaceholderText("sk-proj-1234...")
        self.api_key_edit.setMinimumWidth(500)
        self.api_key_edit.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        self.api_key_edit.onChange.connect(
            lambda text: self.state.update({"openai_api_key": text})
        )

        form = default_form_layout()
        form.addRow("<b>🔑 OpenAI API Key:</b>", self.api_key_edit)
        form.addRow(get_api_key_label)

        group_box = QGroupBox()
        group_box.setLayout(form)

        return group_box

    def render_ui(self) -> None:
        self.render_table()
        self.render_buttons()

    def render_table(self) -> None:
        self.table.setRowCount(0)

        row = 0
        for note_type, field_prompts in self.state.s["prompts_map"][
            "note_types"
        ].items():
            for field, prompt in field_prompts["fields"].items():
                extras = get_extras(note_type, field)
                type = extras["type"]
                self.table.insertRow(self.table.rowCount())
                items = [
                    QTableWidgetItem(note_type),
                    QTableWidgetItem(field),
                    QTableWidgetItem("text" if type == "chat" else "tts"),
                    QTableWidgetItem(prompt if type == "chat" else "🔈"),
                ]
                for i, item in enumerate(items):
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.table.setItem(row, i, item)
                row += 1

        # Ensure the correct row is always selected
        # shouldn't need the second and condition, but defensive
        selected_row = self.state.s["selected_row"]
        if selected_row is not None and selected_row < self.table.rowCount():
            self.table.selectRow(selected_row)

    def render_legacy_options(self) -> QGroupBox:
        models_group_box = QGroupBox("Legacy OpenAI Settings")
        models_form = default_form_layout()
        models_form.addRow(self.render_openai_api_key_box())
        models_form.addRow("OpenAI Model:", self.openai_legacy_combo_box)

        learn_more_about_models = QLabel(
            'Newer models (GPT-4o, etc) will perform better with lower rate limits and higher cost. <a href="https://platform.openai.com/docs/models/">Learn more.</a>'
        )
        learn_more_about_models.setOpenExternalLinks(True)
        learn_more_about_models.setFont(font_small)
        models_form.addRow(learn_more_about_models)
        models_form.addRow("", QLabel(""))

        self.openai_endpoint_edit = ReactiveLineEdit(self.state, "openai_endpoint")
        self.openai_endpoint_edit.setPlaceholderText("https://api.openai.com")
        self.openai_endpoint_edit.setMinimumWidth(400)
        self.openai_endpoint_edit.onChange.connect(
            lambda text: self.state.update({"openai_endpoint": text})
        )
        endpoint_info = QLabel("Provide an alternative endpoint to the OpenAI API.")
        endpoint_info.setFont(font_small)
        models_form.addRow("OpenAI Host:", self.openai_endpoint_edit)
        models_form.addRow(endpoint_info)

        models_group_box.setLayout(models_form)
        return models_group_box

    def render_plugin_tab(self) -> QWidget:
        plugin_box = QGroupBox("✨Smart Field Generation")
        plugin_form = default_form_layout()
        plugin_box.setLayout(plugin_form)

        # Generate at review
        self.generate_at_review_button = ReactiveCheckBox(
            self.state, "generate_at_review"
        )
        self.generate_at_review_button.onChange.connect(
            lambda checked: self.state.update({"generate_at_review": checked})
        )

        plugin_form.addRow(
            "Generate fields during review:", self.generate_at_review_button
        )
        plugin_form.addRow("", QLabel(""))

        # Regenerate when during
        self.regenerate_notes_when_batching = ReactiveCheckBox(
            self.state, "regenerate_notes_when_batching"
        )
        self.regenerate_notes_when_batching.onChange.connect(
            lambda checked: self.state.update(
                {"regenerate_notes_when_batching": checked}
            )
        )
        plugin_form.addRow(
            "Regenerate all smart fields when batch processing:",
            self.regenerate_notes_when_batching,
        )
        regenerate_info = QLabel(
            "When batch processing a group of notes, whether to regenerate all smart fields from scratch, or only generate empty ones."
        )
        regenerate_info.setFont(font_small)
        plugin_form.addRow(regenerate_info)
        plugin_form.addRow("", QLabel(""))

        self.allow_empty_fields_box = ReactiveCheckBox(self.state, "allow_empty_fields")
        self.allow_empty_fields_box.onChange.connect(
            lambda checked: self.state.update({"allow_empty_fields": checked})
        )
        plugin_form.addRow(
            "Generate prompts with some blank fields:", self.allow_empty_fields_box
        )
        empty_fields_info = QLabel(
            "Generate even if the prompt references some blank fields. Prompts referencing *only* blank fields are never generated."
        )
        empty_fields_info.setFont(font_small)
        plugin_form.addRow(empty_fields_info)

        plugin_tab_layout = default_form_layout()
        plugin_tab_layout.addRow(plugin_box)

        if config.legacy_support:
            plugin_tab_layout.addRow(QLabel(""))
            plugin_tab_layout.addRow(self.render_legacy_options())

        self.debug_checkbox = ReactiveCheckBox(self.state, "debug")
        self.debug_checkbox.onChange.connect(
            (lambda checked: self.state.update({"debug": checked}))
        )
        plugin_tab_layout.addRow(QLabel(""))
        plugin_tab_layout.addRow("Debug mode", self.debug_checkbox)

        plugin_settings_tab = QWidget()
        plugin_settings_tab.setLayout(plugin_tab_layout)

        return plugin_settings_tab

    def render_account_tab(self) -> QWidget:
        return AccountOptions()

    def render_chat_tab(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout()
        container.setLayout(layout)
        layout.setContentsMargins(24, 24, 24, 24)
        # TODO: this shouldn't depend on self state
        options = ChatOptions(self.state)  # type: ignore
        options.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        expl = QLabel("Configure default language model settings")
        subExpl = QLabel("These settings can be overridden on a per-field basis.")
        expl.setFont(font_large)
        subExpl.setFont(font_small)
        layout.addWidget(expl)
        layout.addWidget(subExpl)
        layout.addItem(
            QSpacerItem(0, 24, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        )
        layout.addWidget(options)
        return container

    def render_tts_tab(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout()
        container.setLayout(layout)
        layout.setContentsMargins(24, 24, 24, 24)
        options = TTSOptions()
        options.state.state_changed.connect(self.tts_state_changed)
        options.setContentsMargins(0, 0, 0, 0)

        expl = QLabel("Configure default voice settings for TTS.")
        subExpl = QLabel("These settings can be overridden on a per-field basis.")
        expl.setFont(font_large)
        subExpl.setFont(font_small)
        layout.addWidget(expl)
        layout.addWidget(subExpl)
        layout.addItem(
            QSpacerItem(0, 24, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        )
        layout.addWidget(options)
        return container

    def tts_state_changed(self, state: TTSState) -> None:
        self.state.update(
            {
                "tts_provider": state["tts_provider"],
                "tts_voice": state["tts_voice"],
                "tts_model": state["tts_model"],
            }
        )

    def create_table(self) -> QTableWidget:
        table = QTableWidget(0, 4)
        table.setHorizontalHeaderLabels(["Note Type", "Target Field", "Type", "Prompt"])

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

    def on_row_selected(self, current) -> None:
        if current:
            self.state.update({"selected_row": current.row()})

    def on_edit(self, _) -> None:
        row = self.state.s["selected_row"]
        if row is None:
            return

        note_type = self.table.item(row, 0).text()  # type: ignore
        field = self.table.item(row, 1).text()  # type: ignore
        logger.debug(f"Editing {note_type}, {field}")

        # Save out API key jic
        config.openai_api_key = self.api_key_edit.text()

        # Get type
        field_type = get_extras(note_type, field)["type"]

        prompt_dialog = PromptDialog(
            self.state.s["prompts_map"],
            self.processor,
            self.on_update_prompts,
            card_type=note_type,
            field=field,
            field_type=field_type,
            prompt=get_prompts(to_lower=True)[note_type][field.lower()],
        )

        if prompt_dialog.exec() == QDialog.DialogCode.Accepted:
            self.render_table()

    def render_buttons(self) -> None:
        is_enabled = self.state.s["selected_row"] is not None
        self.remove_button.setEnabled(is_enabled)
        self.edit_button.setEnabled(is_enabled)

    def on_add(self, is_tts: bool) -> None:
        # Save out the API key in case it's been updated this run
        config.openai_api_key = self.api_key_edit.text()

        prompt_dialog = PromptDialog(
            self.state.s["prompts_map"],
            self.processor,
            self.on_update_prompts,
            field_type="tts" if is_tts else "chat",
        )

        if prompt_dialog.exec() == QDialog.DialogCode.Accepted:
            self.render_table()

    # When appstate updates
    def update_from_state(self, _: AppState) -> None:
        logger.debug("Updating with new AppState")
        is_unlocked = is_app_unlocked()
        self.voice_button.setEnabled(is_unlocked)
        self.tts_tab.setEnabled(is_unlocked)

    def on_remove(self):
        row = self.state.s["selected_row"]
        if row is None:
            # Should never happen
            return

        card_type = self.table.item(row, 0).text()  # type: ignore
        field = self.table.item(row, 1).text()  # type: ignore
        logger.debug(f"Removing {card_type}, {field}")
        # Deep copy bc we need the subdicts to not be mutated
        prompts_map = copy.deepcopy(self.state.s["prompts_map"])

        prompts_map["note_types"][card_type]["fields"].pop(field)
        extras = prompts_map["note_types"][card_type]["extras"]
        if extras:
            extras.pop(field, None)
        # If there are no more fields for this card type, remove the card type
        if not prompts_map["note_types"][card_type]["fields"]:
            prompts_map["note_types"].pop(card_type)

        self.state.update({"prompts_map": prompts_map, "selected_row": None})

    def on_accept(self) -> None:
        if config.openai_endpoint and not is_valid_url(config.openai_endpoint):
            show_message_box("Invalid OpenAI Host", "Please provide a valid URL.")
            return

        if (
            self.state.s["tts_provider"] == "elevenLabs"
            and not config.tts_provider == "elevenLabs"
        ):
            did_click_ok = show_message_box(
                "Are you sure you want to set your default voice provider to a premium model? These voices may consume your plan quickly.",
                show_cancel=True,
            )
            if not did_click_ok:
                return

        is_unlocked = is_app_unlocked()

        if not is_unlocked:
            if self.state.s["chat_provider"] != "openai":
                show_message_box(UNPAID_PROVIDER_ERROR)
                return

        valid_config_attrs = config.__annotations__.keys()

        old_debug = config.debug
        for k, v in [
            item for item in self.state.s.items() if item[0] in valid_config_attrs
        ]:
            config.__setattr__(k, v)
            logger.debug(f"Setting {k} to {v}")

        if not old_debug and self.state.s["debug"]:
            show_message_box("Debug mode enabled. Please restart Anki.")

        self.accept()

    def on_reject(self) -> None:
        self.reject()

    def on_update_prompts(self, prompts_map: PromptMap) -> None:
        self.state.update({"prompts_map": prompts_map})

    def make_initial_state(self) -> State:
        return {
            "openai_api_key": config.openai_api_key,
            "prompts_map": config.prompts_map,
            "legacy_openai_model": config.openai_model,
            "selected_row": None,
            "generate_at_review": config.generate_at_review,
            "regenerate_notes_when_batching": config.regenerate_notes_when_batching,
            "openai_endpoint": config.openai_endpoint,
            "legacy_openai_models": legacy_openai_chat_models,
            "allow_empty_fields": config.allow_empty_fields,
            "debug": config.debug,
            # Chat
            "chat_provider": config.chat_provider,
            "chat_providers": ["ChatGPT", "Claude"],
            "chat_model": config.chat_model,
            "chat_models": provider_model_map[config.chat_provider],
            "chat_temperature": config.chat_temperature,
            # TTS
            "tts_provider": config.tts_provider,
            "tts_voice": config.tts_voice,
            "tts_model": config.tts_model,
        }

    def on_restore_defaults(self) -> None:
        config.restore_defaults()
        self.state.update(self.make_initial_state())  # type: ignore


def is_valid_url(url: str) -> bool:
    parsed = urlparse(url)
    return all([parsed.scheme, parsed.netloc])
