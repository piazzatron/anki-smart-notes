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

from aqt import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QSlider,
    Qt,
    QVBoxLayout,
    QWidget,
)

from ..config import key_or_config_val
from ..models import (
    ChatModels,
    ChatProviders,
    ChatReasoningLevel,
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
    chat_reasoning_level: ChatReasoningLevel
    chat_temperature: int
    chat_web_search: bool


models_map: dict[str, str] = {
    "auto": "Auto (Best Value, 0.3x cost)",
    "auto-max": "Auto (MAX) (4x cost)",
    "gpt-5-mini": "GPT-5 Mini (1x cost)",
    "gpt-5-chat-latest": "GPT-5 (No Reasoning, 7x cost)",
    "gpt-5": "GPT-5 (Reasoning, 7x cost)",
    "claude-haiku-4-5": "Claude Haiku 4.5 (3x cost)",
    "claude-sonnet-4-6": "Claude Sonnet 4.6 (10x cost)",
    "claude-opus-4-6": "Claude Opus 4.6 (16x cost)",
    "gemini-3-flash": "Gemini 3 Flash (2x cost)",
    "gemini-3.1-flash-lite": "Gemini 3.1 Flash Lite (1x cost)",
    "gemini-3.1-pro": "Gemini 3.1 Pro (8x cost)",
}

providers_map: dict[ChatProviders, str] = {
    "auto": "Auto",
    "openai": "OpenAI",
    "anthropic": "Anthropic",
    "google": "Google",
}

# Display order: providers in this order, models within each provider in
# provider_model_map order.
provider_display_order: list[ChatProviders] = [
    "auto",
    "openai",
    "anthropic",
    "google",
]

model_to_provider: dict[ChatModels, ChatProviders] = {
    model: provider
    for provider, models in provider_model_map.items()
    for model in models
}

reasoning_levels: list[ChatReasoningLevel] = ["off", "low", "high"]
reasoning_level_to_slider_value = {
    level: index for index, level in enumerate(reasoning_levels)
}
chat_model_control_width = 320


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
        self.chat_model_combo.setFixedWidth(chat_model_control_width)
        self.chat_model_combo.setMinimumHeight(30)
        self.chat_model_combo.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
        )
        self.select_model_in_combo(self.state.s["chat_model"])
        chat_model_container = QWidget()
        chat_model_layout = QHBoxLayout()
        chat_model_layout.setContentsMargins(0, 0, 0, 0)
        chat_model_layout.addWidget(self.chat_model_combo)
        chat_model_layout.addStretch()
        chat_model_container.setLayout(chat_model_layout)

        self.reasoning_slider = QSlider(Qt.Orientation.Horizontal)
        self.reasoning_slider.setRange(0, len(reasoning_levels) - 1)
        self.reasoning_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.reasoning_slider.setTickInterval(1)
        self.reasoning_slider.setSingleStep(1)
        self.reasoning_slider.valueChanged.connect(self.on_reasoning_changed)
        self.reasoning_slider.setValue(
            reasoning_level_to_slider_value[self.state.s["chat_reasoning_level"]]
        )

        reasoning_labels = QHBoxLayout()
        reasoning_labels.setContentsMargins(0, 0, 0, 0)
        reasoning_labels.setSpacing(0)
        for label in ("Off", "Low", "High"):
            level_label = QLabel(label)
            level_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            reasoning_labels.addWidget(level_label)
            if label != "High":
                reasoning_labels.addStretch()

        reasoning_scale = QWidget()
        reasoning_scale.setFixedWidth(chat_model_control_width)
        reasoning_scale_layout = QVBoxLayout()
        reasoning_scale_layout.setContentsMargins(0, 0, 0, 0)
        reasoning_scale_layout.setSpacing(4)
        reasoning_scale_layout.addWidget(self.reasoning_slider)
        reasoning_scale_layout.addLayout(reasoning_labels)
        reasoning_scale.setLayout(reasoning_scale_layout)

        self.reasoning_container = QWidget()
        reasoning_layout = QVBoxLayout()
        reasoning_layout.setContentsMargins(0, 0, 0, 0)
        reasoning_layout.setSpacing(4)
        reasoning_layout.addWidget(reasoning_scale)
        reasoning_help = QLabel(
            "⚠️ Higher reasoning levels can improve harder generations but use more credits."
        )
        reasoning_help.setFont(font_small)
        reasoning_help.setWordWrap(False)
        reasoning_layout.addWidget(reasoning_help)
        self.reasoning_container.setLayout(reasoning_layout)

        chat_box = QGroupBox("✨ Language Model")
        chat_form = default_form_layout()
        chat_form.setVerticalSpacing(20)
        # vcenter labels so they align with a taller combobox rather than
        # sticking to the top edge of the row.
        chat_form.setLabelAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        chat_box.setLayout(chat_form)
        chat_form.addRow("Model", chat_model_container)
        self.reasoning_row_label = QLabel("Reasoning")
        chat_form.addRow(self.reasoning_row_label, self.reasoning_container)
        self.update_reasoning_visibility()
        self.chat_model_combo.currentIndexChanged.connect(self.on_model_changed)

        search_box = QGroupBox("🔍 Web Search")
        search_layout = default_form_layout()
        search_box.setLayout(search_layout)
        self.web_search_box = ReactiveCheckBox(self.state, "chat_web_search")
        search_layout.addRow(QLabel("Enable Web Search:"), self.web_search_box)
        search_warning = QLabel("⚠️ Search is expensive; monitor your credits.")
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
        self.update_reasoning_visibility()

    def on_reasoning_changed(self, value: int) -> None:
        self.state.update({"chat_reasoning_level": reasoning_levels[value]})

    def update_reasoning_visibility(self) -> None:
        is_auto_model = self.state.s["chat_provider"] == "auto"
        self.reasoning_row_label.setVisible(is_auto_model)
        self.reasoning_container.setVisible(is_auto_model)

    def get_initial_state(
        self, chat_options: OverridableChatOptionsDict
    ) -> ChatOptionsState:
        ret: ChatOptionsState = {
            k: key_or_config_val(chat_options, k)
            for k in overridable_chat_options  # type: ignore
        }
        ret["chat_reasoning_level"] = ret["chat_reasoning_level"] or "off"
        return ret
