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
    ImageModels,
    ImageProviders,
    OverridableImageOptionsDict,
    image_model_to_provider,
    image_provider_model_map,
)
from .state_manager import StateManager
from .ui_utils import default_form_layout, font_bold, font_small

image_models_display: dict[str, str] = {
    "z-image-turbo": "Z-Image Turbo (0.3x Cost)",
    "flux-dev": "Flux Dev (3x Cost)",
    "nano-banana-2": "Nano Banana 2 (5x Cost)",
    "gpt-image-1.5-medium": "GPT Image 1.5 Medium (4x Cost)",
    "gpt-image-1.5-low": "GPT Image 1.5 Low (1x Cost)",
    "gpt-image-2-medium": "GPT Image 2 Medium (4x Cost)",
    "gpt-image-2-low": "GPT Image 2 Low (1x Cost)",
}

providers_map: dict[ImageProviders, str] = {
    "openai": "OpenAI",
    "google": "Google",
    "replicate": "Other",
}

# Display order: providers in this order, models within each provider in
# image_provider_model_map order.
provider_display_order: list[ImageProviders] = ["openai", "google", "replicate"]

model_to_provider: dict[ImageModels, ImageProviders] = {
    model: provider
    for provider, models in image_provider_model_map.items()
    for model in models
}


class State(TypedDict):
    image_model: ImageModels
    image_provider: ImageProviders


class ImageOptions(QWidget):
    def __init__(
        self, image_options: Optional[OverridableImageOptionsDict] = None
    ) -> None:
        super().__init__()

        model: ImageModels = key_or_config_val(image_options or {}, "image_model")

        self.state = StateManager[State](
            {
                "image_model": model,
                "image_provider": image_model_to_provider[model],
            }
        )

        self._setup_ui()

    def _setup_ui(self) -> None:
        self.model_picker = self.build_grouped_model_combo()
        self.model_picker.currentIndexChanged.connect(self.on_model_changed)
        self.select_model_in_combo(self.state.s["image_model"])
        self.model_picker.setMaximumWidth(300)
        box = QGroupBox("🖼️ Image Model Settings")
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(box)
        box_layout = default_form_layout()
        box.setLayout(box_layout)
        box_layout.addRow("Image Model:", self.model_picker)
        tips_title = QLabel("💡  Picking an Image Model")
        tips_title.setFont(font_bold)
        tips_body = QLabel(
            "• GPT Image 1.5 Low tends to be the best tradeoff of quality and speed.\n"
            "• GPT Image 2 variants are the same cost but slower and higher quality.\n"
            "• Z-Image Turbo is the fastest and cheapest."
        )
        tips_body.setWordWrap(True)
        tips_body.setFont(font_small)
        info_box = QGroupBox()
        info_layout = QVBoxLayout()
        info_layout.addWidget(tips_title)
        info_layout.addWidget(tips_body)
        info_box.setLayout(info_layout)
        box_layout.addRow(info_box)
        layout.addStretch()
        self.setLayout(layout)

    def build_grouped_model_combo(self) -> QComboBox:
        # Raw QComboBox rather than ReactiveComboBox: this dropdown mixes two
        # row types — non-selectable bold provider headings ("OpenAI", "Google"…)
        # interleaved with selectable model rows — which ReactiveComboBox's
        # flat-list-of-strings contract doesn't model. We bind manually instead:
        # on_model_changed writes both image_model and image_provider to state.
        combo = QComboBox()
        model = combo.model()
        for provider in provider_display_order:
            combo.addItem(providers_map[provider], None)
            header_item = model.item(combo.count() - 1)  # type: ignore[attr-defined]
            header_item.setEnabled(False)
            header_font = header_item.font()
            header_font.setBold(True)
            header_item.setFont(header_font)

            for image_model in image_provider_model_map[provider]:
                combo.addItem(
                    f"  {image_models_display.get(image_model, image_model)}",
                    image_model,
                )
        return combo

    def select_model_in_combo(self, image_model: ImageModels) -> None:
        for i in range(self.model_picker.count()):
            data = self.model_picker.itemData(i, Qt.ItemDataRole.UserRole)
            if data == image_model:
                self.model_picker.setCurrentIndex(i)
                return

    def on_model_changed(self, index: int) -> None:
        image_model = self.model_picker.itemData(index, Qt.ItemDataRole.UserRole)
        if not image_model:
            return
        self.state.update(
            {
                "image_model": image_model,
                "image_provider": model_to_provider[image_model],
            }
        )
