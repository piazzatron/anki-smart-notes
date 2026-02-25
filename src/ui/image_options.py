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

from aqt import QGroupBox, QVBoxLayout, QWidget

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
from .ui_utils import default_form_layout

image_models_display: dict[str, str] = {
    "flux-schnell": "Flux Schnell (1x Image Cost)",
    "flux-dev": "Flux Dev (8x Image Cost)",
    "nano-banana": "Nano Banana (TBD Cost)",
    "nano-banana-pro": "Nano Banana Pro (TBD Cost)",
    "gpt-image-1.5": "GPT Image 1.5 (TBD Cost)",
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
        self.setLayout(layout)
