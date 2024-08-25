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

from typing import Any, Dict, Generic, List, TypeVar

from aqt import QComboBox

from .reactive_widget import ReactiveWidget
from .state_manager import StateManager

T = TypeVar("T")


class ReactiveComboBox(ReactiveWidget[T], QComboBox, Generic[T]):
    _fields_key: str
    _selected_key: str

    def __init__(
        self,
        state: StateManager[T],
        fields_key: str,
        selected_key: str,
        render_map: Dict[str, str] = {},
        **kwargs: Any
    ):
        super().__init__(state, **kwargs)
        self._fields_key = fields_key
        self._selected_key = selected_key
        self.state_to_ui = render_map
        self.ui_to_state = {v: k for k, v in render_map.items()}

        # Bind from state change to view
        state.bind(self)

        self.currentTextChanged.connect(self._on_current_text_changed)

        # Bind from view change to state
        self.onChange.connect(
            lambda new_value: state.update({self._selected_key: new_value})
        )

    def _update_from_state(self, updates: Dict[str, Any]) -> None:
        fields: List[str] = updates[self._fields_key]
        selected: str = updates[self._selected_key]
        assert fields and selected

        self.clear()
        self.addItems([self.state_to_ui.get(field, field) for field in fields])
        self.setCurrentText(self.state_to_ui.get(selected, selected))

    def _on_current_text_changed(self, text: str) -> None:
        if self._state.updating:
            return

        self.onChange.emit(self.ui_to_state.get(text, text))
