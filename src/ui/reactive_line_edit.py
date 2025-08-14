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

from typing import Any, Generic, TypeVar

from aqt import QLineEdit

from .reactive_widget import ReactiveWidget
from .state_manager import StateManager

T = TypeVar("T")


class ReactiveLineEdit(ReactiveWidget[T], QLineEdit, Generic[T]):
    def __init__(self, state: StateManager[T], key: str, **kwargs: Any):
        super().__init__(state, **kwargs)
        self._key = key

        state.bind(self)

        self.textChanged.connect(self._on_text_changed)

    def _update_from_state(self, updates: dict[str, Any]) -> None:
        self.setText(updates[self._key])

    def _on_text_changed(self, text: str) -> None:
        if self._state.updating:
            return

        self.on_change.emit(text)
