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

import os
from typing import Any, Callable, Dict, List

from aqt import mw

from ..env import environment
from .config import config
from .ui.rate_dialog import RateDialog
from .ui.ui_utils import show_message_box


def to_lowercase_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    """Converts a dictionary to lowercase keys"""
    return {k.lower(): v for k, v in d.items()}


def get_fields(note_type: str) -> List[str]:
    """Gets the fields of a note type. Returns them sorted in their order on the card"""
    if not mw or not mw.col:
        return []

    if not note_type:
        return []

    model = mw.col.models.by_name(note_type)
    if not model:
        return []

    return [field["name"] for field in sorted(model["flds"], key=lambda x: x["ord"])]


def check_for_api_key(show_box=True) -> bool:
    if not config.openai_api_key:
        if show_box:
            message = "No OpenAI API key found. Please enter your API key in the options menu."
            show_message_box(message)
        return False
    return True


USES_BEFORE_RATE_DIALOG = 10


def bump_usage_counter() -> None:
    config.times_used += 1
    if config.times_used > USES_BEFORE_RATE_DIALOG and not config.did_show_rate_dialog:
        config.did_show_rate_dialog = True
        dialog = RateDialog()
        dialog.exec()


def load_file(file: str) -> str:
    path = mw.pm.addonFolder()  # type: ignore
    module = __name__.split(".")[0]
    file_path = os.path.join(path, module, file)

    with open(file_path, "r") as f:
        content = f.read()

    return content


def run_on_main(work: Callable[[], None]):
    if not mw:
        return
    mw.taskman.run_on_main(work)


def is_production() -> bool:
    return environment == "PROD"
