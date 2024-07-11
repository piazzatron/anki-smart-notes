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

from typing import Any, Dict, Generic, TypeVar

from aqt import QCheckBox, pyqtSignal

from .reactive_widget import ReactiveWidget
from .state_manager import StateManager

T = TypeVar("T")


class ReactiveCheckBox(ReactiveWidget[T], QCheckBox, Generic[T]):
    onChange = pyqtSignal(bool)

    def __init__(self, state: StateManager[T], key: str, **kwargs):
        super().__init__(state, **kwargs)
        self._key = key

        state.bind(self)

        self.stateChanged.connect(self._on_state_changed)

    def _update_from_state(self, updates: Dict[str, Any]) -> None:
        self.setChecked(updates[self._key])

    def _on_state_changed(self, state) -> None:
        if self._state.updating:
            return

        self.onChange.emit(state == 2)
