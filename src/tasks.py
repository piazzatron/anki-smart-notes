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

import asyncio
from typing import Any, Callable, Union

from aqt import mw
from aqt.operations import QueryOp


def run_async_in_background(
    op: Callable[[], Any],
    on_success: Callable[[Any], None] = lambda _: None,
    on_failure: Union[Callable[[Exception], None], None] = None,
    with_progress: bool = False,
    use_collection: bool = True,
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

    # Not all versions of Anki support with_progress :(
    # https://github.com/ankitects/anki/commit/055d66397081067a5d4cc6f1e3b370168e907119
    if with_progress and hasattr(query_op, "with_progress"):
        query_op = query_op.with_progress()

    if not use_collection:
        query_op = query_op.without_collection()

    query_op.run_in_background()
