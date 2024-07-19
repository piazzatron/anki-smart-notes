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
from typing import List, TypedDict

import aiohttp
from aqt import mw

from .config import config
from .constants import get_server_url
from .logger import logger
from .ui.ui_utils import show_message_box
from .utils import run_in_background, run_on_main

SLEEP_DURATION_MINS = 30


class Message(TypedDict):
    title: str
    text: str
    id: int


async def get_messages() -> List[Message]:
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{get_server_url()}/messages") as response:
            if response.status == 200:
                data: List[Message] = await response.json()
                return data
            else:
                logger.error(f"Failed to get messages: {response.status}")
            return []


async def show_latest_message() -> None:
    try:
        messages = await get_messages()
        logger.debug(f"Got messages: {messages}")
        if not messages:
            return
        highest = max(messages, key=id)

        if highest["id"] > config.last_message_id:
            config.last_message_id = highest["id"]
            logger.debug("Running highest new message on main")
            run_on_main(lambda: show_message_box(highest["title"], highest["text"]))
    except Exception as e:
        logger.error("Failed to show latest message", e)


def start_polling_for_messages() -> None:
    if not mw:
        return

    mw.progress.timer(
        SLEEP_DURATION_MINS * 60 * 1000,
        lambda: run_in_background(asyncio.run(show_latest_message())),  # type: ignore
        repeat=True,
        requiresCollection=False,
    )
