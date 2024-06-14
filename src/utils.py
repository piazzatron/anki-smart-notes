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

from typing import Callable, Dict, Any, Union
from aqt import mw
from aqt.operations import QueryOp
from .config import config
import os

from .ui.rate_dialog import RateDialog
from .ui.ui_utils import show_message_box
import asyncio


def to_lowercase_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    """Converts a dictionary to lowercase keys"""
    return {k.lower(): v for k, v in d.items()}


def get_fields(note_type: str):
    """Gets the fields of a note type."""
    if not mw or not mw.col:
        return []

    if not note_type:
        return []

    model = mw.col.models.by_name(note_type)
    if not model:
        return []

    return [field["name"] for field in model["flds"]]


def run_async_in_background(
    op: Callable[[], Any],
    on_success: Callable[[Any], None],
    on_failure: Union[Callable[[Exception], None], None] = None,
    with_progress: bool = False,
):
    "Runs an async operation in the background and calls on_success when done."

    if not mw:
        raise Exception("Error: mw not found in run_async_in_background")

    query_op = QueryOp(
        parent=mw,
        op=lambda _: asyncio.run(op()),
        success=on_success,
    )

    if on_failure:
        query_op.failure(on_failure)

    if with_progress:
        query_op = query_op.with_progress()

    query_op.run_in_background()


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
    dir = os.getcwd()
    file_path = os.path.join(dir, file)

    print(f"Loading from: {file_path}")
    with open(file_path, "r") as f:
        content = f.read()

    return content
