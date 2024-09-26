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

from typing import Dict, List, TypedDict

from aqt import QGroupBox, QLabel, QSpacerItem, QWidget

from ..models import (
    ChatModels,
    ChatProviders,
    anthropic_chat_models,
    openai_chat_models,
)
from .reactive_combo_box import ReactiveComboBox
from .reactive_spin_box import ReactiveDoubleSpinBox
from .state_manager import StateManager
from .ui_utils import default_form_layout, font_small


class ChatOptionsState(TypedDict):
    chat_provider: ChatProviders
    chat_providers: List[ChatProviders]
    chat_models: List[ChatModels]
    chat_model: ChatModels
    chat_temperature: int


provider_model_map: Dict[ChatProviders, List[ChatModels]] = {
    "openai": openai_chat_models,
    "anthropic": anthropic_chat_models,
}


models_map: Dict[str, str] = {
    "gpt-4o-mini": "GPT-4o Mini (Fast, Cheap)",
    "gpt-4o": "GPT-4o (Smartest, More Expensive)",
    "claude-3-5-sonnet": "Claude 3.5 Sonnet (Smartest, More Expensive)",
    "claude-3-haiku": "Claude 3 Haiku (Cheap, Fast)",
}

providers_map = {"openai": "ChatGPT", "anthropic": "Claude"}


class ChatOptions(QWidget):
    def __init__(self, state: StateManager[ChatOptionsState]):
        super().__init__()
        self.state = state
        self.setup_ui()

    def setup_ui(self) -> None:
        self.chat_provider = ReactiveComboBox(
            self.state, "chat_providers", "chat_provider", providers_map
        )
        self.chat_provider.onChange.connect(
            lambda text: self.state.update(
                {
                    "chat_provider": text,
                    "chat_models": provider_model_map[text],
                    "chat_model": provider_model_map[text][0],
                }
            )
        )
        self.temperature = ReactiveDoubleSpinBox(self.state, "chat_temperature")
        self.temperature.setRange(0, 2)
        self.temperature.setSingleStep(0.1)
        self.temperature.onChange.connect(
            lambda temp: self.state.update({"chat_temperature": temp})
        )
        self.chat_model = ReactiveComboBox(
            self.state, "chat_models", "chat_model", models_map
        )
        self.chat_model.setMinimumWidth(350)
        chat_box = QGroupBox("✨ Language Model")
        chat_form = default_form_layout()
        chat_form.addRow("Provider:", self.chat_provider)
        chat_form.addRow("Model:", self.chat_model)

        advanced = QGroupBox("⚙️ Advanced")
        advanced_layout = default_form_layout()
        advanced.setLayout(advanced_layout)
        advanced_layout.addRow("Temperature:", self.temperature)
        temp_desc = QLabel(
            "Temperature controls the creativity of responses. Values range from 0-2 (ChatGPT default is 1)."
        )
        temp_desc.setFont(font_small)
        advanced_layout.addRow(temp_desc)

        chat_box.setLayout(chat_form)
        chat_layout = default_form_layout()
        chat_layout.addRow(chat_box)
        chat_layout.addItem(QSpacerItem(0, 12))
        chat_layout.addRow(advanced)
        chat_layout.setContentsMargins(0, 0, 0, 0)

        self.setLayout(chat_layout)
