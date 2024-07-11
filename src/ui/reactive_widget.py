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

from aqt import pyqtSignal

from .state_manager import StateManager

T = TypeVar("T")


class ReactiveWidget(Generic[T]):
    onChange = pyqtSignal(str)
    _state: StateManager[T]

    def __init__(self, state: StateManager[T], **kwargs: Any):
        super().__init__(**kwargs)
        self._state = state

    def update_from_state(self, new_state: Dict[str, Any]) -> None:
        raise NotImplementedError()
