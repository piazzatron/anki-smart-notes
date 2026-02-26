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

from aqt import QGroupBox, QLabel, QVBoxLayout, QWidget

from ..config import key_or_config_val
from ..models import (
    ImageModels,
    ImageProviders,
    OverridableImageOptionsDict,
    all_image_models,
    image_model_to_provider,
)
from .reactive_combo_box import ReactiveComboBox
from .state_manager import StateManager
from .ui_utils import default_form_layout, font_bold, font_small

image_models_display: dict[str, str] = {
    "z-image-turbo": "Z-Image Turbo (0.3x Cost)",
    "flux-dev": "Flux Dev (3x Cost)",
    "nano-banana": "Nano Banana (4x Cost)",
    "gpt-image-1.5-medium": "GPT Image 1.5 (4x Cost)",
    "gpt-image-1.5-low": "GPT Image 1.5 Low (1x Cost)",
}


class State(TypedDict):
    image_model: ImageModels
    image_models: list[ImageModels]
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
                "image_models": all_image_models,
                "image_provider": image_model_to_provider[model],
            }
        )

        self._setup_ui()

    def _setup_ui(self) -> None:
        self.model_picker = ReactiveComboBox(
            self.state,
            "image_models",
            "image_model",
            image_models_display,
        )
        self.model_picker.on_change.connect(
            lambda model: self.state.update(
                {"image_provider": image_model_to_provider[model]}
            )
        )
        self.model_picker.setMaximumWidth(300)
        box = QGroupBox("🖼️ Image Model Settings")
        layout = QVBoxLayout()
        layout.addWidget(box)
        box_layout = default_form_layout()
        box.setLayout(box_layout)
        box_layout.addRow("Image Model:", self.model_picker)
        tips_title = QLabel("💡  Picking an Image Model")
        tips_title.setFont(font_bold)
        tips_body = QLabel(
            "GPT-image-low is usually the best balance of quality and price. "
            "Z-Image Turbo is the fastest, cheapest, and lowest quality. "
            "Flux-Dev is fast, but may have quality issues."
        )
        tips_body.setWordWrap(True)
        tips_body.setFont(font_small)
        info_box = QGroupBox()
        info_layout = QVBoxLayout()
        info_layout.addWidget(tips_title)
        info_layout.addWidget(tips_body)
        info_box.setLayout(info_layout)
        box_layout.addRow(info_box)
        self.setLayout(layout)
