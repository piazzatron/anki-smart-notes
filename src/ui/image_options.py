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
from ..models import ImageModels, ImageProviders, OverridableImageOptionsDict
from .reactive_combo_box import ReactiveComboBox
from .state_manager import StateManager
from .ui_utils import default_form_layout


class State(TypedDict):
    image_model: ImageModels
    image_models: list[ImageModels]
    image_provider: ImageProviders


class ImageOptions(QWidget):
    def __init__(
        self, image_options: Optional[OverridableImageOptionsDict] = None
    ) -> None:
        super().__init__()

        self.state = StateManager[State](
            {
                "image_model": key_or_config_val(image_options or {}, "image_model"),
                "image_models": ["flux-dev", "flux-schnell"],
                "image_provider": "replicate",
            }
        )

        self._setup_ui()

    def _setup_ui(self) -> None:
        self.model_picker = ReactiveComboBox(
            self.state,
            "image_models",
            "image_model",
            {
                "flux-schnell": "Flux Schnell (1 credit)",
                "flux-dev": "Flux Dev (8 credits)",
            },
        )
        self.model_picker.setMaximumWidth(300)
        box = QGroupBox("🖼️ Image Model Settings")
        layout = QVBoxLayout()
        layout.addWidget(box)
        box_layout = default_form_layout()
        box.setLayout(box_layout)
        box_layout.addRow("Image Model:", self.model_picker)
        self.setLayout(layout)
