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

from .api_client import api


def run_async_in_background(
    op: Callable[[], Any],
    on_success: Callable[[Any], None] = lambda _: None,
    on_failure: Union[Callable[[Exception], None], None] = None,
    with_progress: bool = False,
):
    "Runs an async operation in the background and calls on_success when done."

    if not mw:
        raise Exception("Error: mw not found in run_async_in_background")

    async def wrapped_op() -> Any:
        # Need a new aiohttp session per event loop
        # I hate this
        await api.refresh_session()
        # TODO: does this need to return? Probs not...
        return await op()

    query_op = QueryOp(
        parent=mw,
        op=lambda _: asyncio.run(wrapped_op()),
        success=on_success,
    )

    if on_failure:
        query_op.failure(on_failure)

    if with_progress:
        query_op = query_op.with_progress()

    query_op.run_in_background()
