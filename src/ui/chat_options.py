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

from typing import Dict, List, Optional, TypedDict

from aqt import QGroupBox, QLabel, QSpacerItem, QWidget

from ..config import key_or_config_val
from ..models import (
    ChatModels,
    ChatProviders,
    OverridableChatOptionsDict,
    overridable_chat_options,
)
from .reactive_check_box import ReactiveCheckBox
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
    chat_markdown_to_html: bool


# Order that the models are displayed in the UI
openai_chat_models: List[ChatModels] = [
    # GPT models
    "gpt-4.1-nano",
    "gpt-4o-mini",
    "gpt-4.1-mini",
    "gpt-4.1",
    # Reasoning models
    "o4-mini",
    "o3",
    # Deprecated
    "gpt-4o",
]

anthropic_chat_models: List[ChatModels] = [
    "claude-3-5-sonnet",
    "claude-3-haiku",
]

deepseek_chat_models: List[ChatModels] = ["deepseek-v3"]

provider_model_map: Dict[ChatProviders, List[ChatModels]] = {
    "openai": openai_chat_models,
    "anthropic": anthropic_chat_models,
    "deepseek": deepseek_chat_models,
}

models_map: Dict[str, str] = {
    "gpt-4.1-nano": "gpt-4.1-nano (0.25x Cost)",
    "gpt-4o-mini": "gpt-4o-mini (0.4x Cost)",
    "gpt-4.1-mini": "gpt-4.1-mini (1x Cost, Recommended 👍)",
    "o4-mini": "o4-mini reasoning model (2.5x Cost)",
    "gpt-4.1": "gpt-4.1 (5x Cost)",
    "gpt-4o": "gpt-4o (7x Cost, Outdated)",
    "o3": "o3 reasoning model (25x Cost)",
    "claude-3-5-sonnet": "Claude 3.5 Sonnet (10x Cost)",
    "claude-3-haiku": "Claude 3 Haiku (0.75x Cost)",
    "deepseek-v3": "Deepseek v3 (0.7x Cost)",
}

providers_map = {"openai": "ChatGPT", "anthropic": "Claude", "deepseek": "DeepSeek"}

all_chat_providers: List[ChatProviders] = ["openai", "anthropic", "deepseek"]


class ChatOptions(QWidget):
    _show_text_processing: bool

    def __init__(
        self,
        chat_options: Optional[OverridableChatOptionsDict] = None,
        show_text_processing: bool = True,
    ):
        super().__init__()
        self.state = StateManager[ChatOptionsState](
            self.get_initial_state(chat_options or {})  # type: ignore
        )
        self._show_text_processing = show_text_processing
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
        chat_box.setLayout(chat_form)
        chat_form.addRow("Provider:", self.chat_provider)
        chat_form.addRow("Model:", self.chat_model)

        text_rules = QGroupBox("🔤 Text Processing")
        text_layout = default_form_layout()
        text_rules.setLayout(text_layout)
        text_rules.setHidden(not self._show_text_processing)
        self.convert_box = ReactiveCheckBox(self.state, "chat_markdown_to_html")
        text_layout.addRow(QLabel("Convert Markdown to HTML:"), self.convert_box)
        convert_explainer = QLabel(
            "Language models often use **Markdown** in their responses - convert it to HTML to render within Anki."
        )
        convert_explainer.setFont(font_small)
        text_layout.addRow(convert_explainer)
        advanced = QGroupBox("⚙️ Advanced")
        advanced_layout = default_form_layout()
        advanced.setLayout(advanced_layout)
        advanced_layout.addRow("Temperature:", self.temperature)
        temp_desc = QLabel(
            "Temperature controls the creativity of responses. Values range from 0-2 (ChatGPT default is 1)."
        )
        temp_desc.setFont(font_small)
        advanced_layout.addRow(temp_desc)

        chat_layout = default_form_layout()
        chat_layout.addRow(chat_box)
        chat_layout.addItem(QSpacerItem(0, 12))
        chat_layout.addRow(text_rules)
        if self._show_text_processing:
            chat_layout.addItem(QSpacerItem(0, 12))
        chat_layout.addRow(advanced)
        chat_layout.setContentsMargins(0, 0, 0, 0)

        self.setLayout(chat_layout)

    def get_initial_state(
        self, chat_options: OverridableChatOptionsDict
    ) -> ChatOptionsState:
        ret: ChatOptionsState = {
            k: key_or_config_val(chat_options, k) for k in overridable_chat_options  # type: ignore
        }

        ret["chat_providers"] = all_chat_providers
        ret["chat_models"] = provider_model_map[ret["chat_provider"]]
        return ret
