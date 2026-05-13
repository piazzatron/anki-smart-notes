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

from typing import Optional, TypedDict

from aqt import QComboBox, QGroupBox, QLabel, Qt, QVBoxLayout, QWidget

from ..config import key_or_config_val
from ..models import (
    ChatModels,
    ChatProviders,
    OverridableChatOptionsDict,
    overridable_chat_options,
    provider_model_map,
)
from .reactive_check_box import ReactiveCheckBox
from .state_manager import StateManager
from .ui_utils import default_form_layout, font_small


class ChatOptionsState(TypedDict):
    chat_provider: ChatProviders
    chat_model: ChatModels
    chat_temperature: int
    chat_web_search: bool


models_map: dict[str, str] = {
    "gpt-5-mini": "GPT-5 Mini (1x cost)",
    "gpt-5-chat-latest": "GPT-5 (No Reasoning, 5x cost)",
    "gpt-5": "GPT-5 (Reasoning, 5x++ cost)",
    "gpt-5-nano": "GPT-5 Nano (0.2x cost)",
    "gpt-4o-mini": "GPT-4o Mini (0.3x cost)",
    "claude-haiku-4-5": "Claude Haiku 4.5 (2x Cost)",
    "claude-sonnet-4-6": "Claude Sonnet 4.6 (7x Cost)",
    "claude-opus-4-6": "Claude Opus 4.6 (10x Cost)",
    "deepseek-v3": "Deepseek v3 (0.7x Cost)",
    "gemini-3-flash": "Gemini 3 Flash (1.5x Cost)",
    "gemini-3.1-flash-lite": "Gemini 3.1 Flash Lite (0.75x Cost)",
    "gemini-3.1-pro": "Gemini 3.1 Pro (5x Cost)",
}

providers_map: dict[ChatProviders, str] = {
    "openai": "OpenAI",
    "anthropic": "Anthropic",
    "google": "Google",
    "deepseek": "DeepSeek",
}

# Display order: providers in this order, models within each provider in
# provider_model_map order.
provider_display_order: list[ChatProviders] = [
    "openai",
    "anthropic",
    "google",
    "deepseek",
]

model_to_provider: dict[ChatModels, ChatProviders] = {
    model: provider
    for provider, models in provider_model_map.items()
    for model in models
}


class ChatOptions(QWidget):
    def __init__(
        self,
        chat_options: Optional[OverridableChatOptionsDict] = None,
    ):
        super().__init__()
        self.state = StateManager[ChatOptionsState](
            self.get_initial_state(chat_options or {})  # type: ignore
        )
        self.setup_ui()

    def setup_ui(self) -> None:
        self.chat_model_combo = self.build_grouped_model_combo()
        self.chat_model_combo.setMinimumWidth(350)
        self.chat_model_combo.setMinimumHeight(30)
        self.chat_model_combo.currentIndexChanged.connect(self.on_model_changed)
        self.select_model_in_combo(self.state.s["chat_model"])

        chat_box = QGroupBox("✨ Language Model")
        chat_form = default_form_layout()
        # vcenter labels so they align with a taller combobox rather than
        # sticking to the top edge of the row.
        chat_form.setLabelAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        chat_box.setLayout(chat_form)
        chat_form.addRow("Model:", self.chat_model_combo)

        search_box = QGroupBox("🔍 Web Search")
        search_layout = default_form_layout()
        search_box.setLayout(search_layout)
        self.web_search_box = ReactiveCheckBox(self.state, "chat_web_search")
        search_layout.addRow(QLabel("Enable Web Search:"), self.web_search_box)
        search_warning = QLabel(
            "⚠️ Search is expensive; monitor your credits. Not available for Deepseek."
        )
        search_warning.setFont(font_small)
        search_layout.addRow(search_warning)

        chat_layout = QVBoxLayout()
        chat_layout.addWidget(chat_box)
        chat_layout.addSpacing(12)
        chat_layout.addWidget(search_box)
        chat_layout.addStretch()
        chat_layout.setContentsMargins(0, 0, 0, 0)

        self.setLayout(chat_layout)

    def build_grouped_model_combo(self) -> QComboBox:
        # Raw QComboBox rather than ReactiveComboBox: this dropdown mixes two
        # row types — non-selectable bold provider headings ("OpenAI", "Anthropic"…)
        # interleaved with selectable model rows — which ReactiveComboBox's
        # flat-list-of-strings contract doesn't model. We bind manually instead:
        # on_model_changed writes both chat_model and chat_provider to state.
        combo = QComboBox()
        model = combo.model()
        for provider in provider_display_order:
            combo.addItem(providers_map[provider], None)
            header_item = model.item(combo.count() - 1)  # type: ignore[attr-defined]
            header_item.setEnabled(False)
            header_font = header_item.font()
            header_font.setBold(True)
            header_item.setFont(header_font)

            for chat_model in provider_model_map[provider]:
                combo.addItem(f"  {models_map.get(chat_model, chat_model)}", chat_model)
        return combo

    def select_model_in_combo(self, chat_model: ChatModels) -> None:
        for i in range(self.chat_model_combo.count()):
            data = self.chat_model_combo.itemData(i, Qt.ItemDataRole.UserRole)
            if data == chat_model:
                self.chat_model_combo.setCurrentIndex(i)
                return

    def on_model_changed(self, index: int) -> None:
        chat_model = self.chat_model_combo.itemData(index, Qt.ItemDataRole.UserRole)
        if not chat_model:
            return
        self.state.update(
            {
                "chat_model": chat_model,
                "chat_provider": model_to_provider[chat_model],
            }
        )

    def get_initial_state(
        self, chat_options: OverridableChatOptionsDict
    ) -> ChatOptionsState:
        ret: ChatOptionsState = {
            k: key_or_config_val(chat_options, k)
            for k in overridable_chat_options  # type: ignore
        }
        return ret
