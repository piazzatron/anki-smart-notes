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

from copy import deepcopy
from typing import Any, Dict, Generic, TypeVar

from aqt import QObject, pyqtSignal

from ..logger import logger
from ..utils import is_production

T = TypeVar("T")


class StateManager(QObject, Generic[T]):
    _state: T
    state_changed = pyqtSignal(dict)
    updating: bool

    def __init__(self, initial_state: T):
        super().__init__()
        self._state = initial_state
        self.updating = False

    @property
    def s(self) -> T:
        return self._state

    def update(self, updates: Dict[str, Any]) -> None:
        # Avoid recursive calls to update, i.e. from components
        # that are re-configuring themselves as a response to
        # a state change, which itself calls update(...)
        if self.updating:
            return
        self.updating = True
        new_state = deepcopy(self._state)
        for key, value in updates.items():
            assert key in new_state  # type: ignore
            new_state[key] = value  # type: ignore

        if new_state != self._state:
            if not is_production():
                logger.debug("State transition")
                # logger.debug(self._state)
                # logger.debug(new_state)
            self._state = new_state
            self.state_changed.emit(new_state)

        self.updating = False

    def bind(
        self, widget: Any
    ):  # TODO: should be ReactiveWidget but circular import that I'm too lazy to fix rn
        self.state_changed.connect(widget.update_from_state)
        self.state_changed.emit(self._state)

    def __setitem__(self, k: str, v: Any) -> None:
        self.update({k: v})
