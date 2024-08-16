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

from typing import Dict, List, Literal, TypedDict

from aqt import QGroupBox, QWidget

from ..models import (
    ChatModels,
    ChatProviders,
    anthropic_chat_models,
    openai_chat_models,
)
from .reactive_combo_box import ReactiveComboBox
from .reactive_spin_box import ReactiveDoubleSpinBox
from .state_manager import StateManager
from .ui_utils import default_form_layout

ReadableChatProvider = Literal["ChatGPT", "Claude"]
ReadableChatProviders: List[ReadableChatProvider] = ["ChatGPT", "Claude"]


class ChatOptionsState(TypedDict):
    chat_provider: ReadableChatProvider
    chat_providers: List[ReadableChatProvider]
    chat_models: List[ChatModels]
    chat_model: ChatModels
    chat_temperature: int


chat_provider_to_ui_map: Dict[ChatProviders, ReadableChatProvider] = {
    "openai": "ChatGPT",
    "anthropic": "Claude",
}
# Reversed
chat_ui_to_provider_map: Dict[ReadableChatProvider, ChatProviders] = {
    v: k for k, v in chat_provider_to_ui_map.items()
}

provider_model_map: Dict[ChatProviders, List[ChatModels]] = {
    "openai": openai_chat_models,
    "anthropic": anthropic_chat_models,
}


class ChatOptions(QWidget):
    def __init__(self, state: StateManager[ChatOptionsState]):
        super().__init__()
        self.state = state
        self.setup_ui()

    def setup_ui(self) -> None:
        self.chat_provider = ReactiveComboBox(
            self.state, "chat_providers", "chat_provider"
        )
        self.chat_provider.onChange.connect(
            lambda text: self.state.update(
                {
                    "chat_provider": text,
                    "chat_models": provider_model_map[chat_ui_to_provider_map[text]],
                    "chat_model": provider_model_map[chat_ui_to_provider_map[text]][0],
                }
            )
        )
        self.temperature = ReactiveDoubleSpinBox(self.state, "chat_temperature")
        self.temperature.setRange(0, 1)
        self.temperature.setSingleStep(0.1)
        self.temperature.onChange.connect(
            lambda temp: self.state.update({"chat_temperature": temp})
        )
        self.chat_model = ReactiveComboBox(self.state, "chat_models", "chat_model")
        chat_box = QGroupBox("✨ Default Chat Settings")
        chat_form = default_form_layout()
        chat_form.addRow("Provider:", self.chat_provider)
        chat_form.addRow("Model:", self.chat_model)

        advanced = QGroupBox("⚙️ Advanced Settings")
        advanced_layout = default_form_layout()
        advanced.setLayout(advanced_layout)
        advanced_layout.addRow("Temperature:", self.temperature)
        # TODO: description of temp

        chat_box.setLayout(chat_form)
        chat_layout = default_form_layout()
        chat_layout.addRow(chat_box)
        chat_layout.addRow(advanced)

        self.setLayout(chat_layout)
