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

import json
import os
import random
from typing import Any, Callable, Dict, List

from aqt import mw

from ..env import environment
from .config import config
from .ui.rate_dialog import RateDialog


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


USES_BEFORE_RATE_DIALOG = 10


def bump_usage_counter() -> None:
    config.times_used += 1
    if config.times_used > USES_BEFORE_RATE_DIALOG and not config.did_show_rate_dialog:
        config.did_show_rate_dialog = True
        dialog = RateDialog()
        dialog.exec()


def get_file_path(file: str) -> str:
    path = mw.pm.addonFolder()  # type: ignore
    module = __name__.split(".")[0]
    return os.path.join(path, module, file)


def load_file(file: str, test_override: str = "") -> str:
    if os.getenv("IS_TEST"):
        return test_override

    file_path = get_file_path(file)

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    return content


def run_on_main(work: Callable[[], None]) -> None:
    if not mw:
        return
    mw.taskman.run_on_main(work)


def run_in_background(work: Callable[[], None]) -> None:
    if not mw:
        return
    mw.taskman.run_in_background(work)


def is_production() -> bool:
    return environment == "PROD"


def get_version() -> str:
    manifest = load_file("manifest.json")
    return json.loads(manifest)["human_version"]  # type: ignore


def make_uuid() -> str:
    letters = "abcdefghijklmnopqrstuvwxyz1234567890"
    uuid = []
    for _ in range(16):
        uuid.append(random.choice(letters))
    return "".join(uuid)
