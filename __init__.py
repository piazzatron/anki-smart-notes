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

import sys
import os

from . import env


def update_path() -> None:

    # Local and prod builds have different package directories
    relative_packages_dir = (
        "vendor" if env.environment == "PROD" else "env/lib/python3.11/site-packages"
    )

    packages_dir = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), relative_packages_dir
    )

    sys.path.append(packages_dir)


update_path()
from dotenv import load_dotenv

load_dotenv()


def setup_platform_specific_functionality() -> None:
    import platform
    import asyncio

    # https://stackoverflow.com/questions/45600579/asyncio-event-loop-is-closed-when-getting-loop
    # https://github.com/piazzatron/anki-smart-notes/issues/5
    if platform.system() == "Windows":
        print("Running in windows environment, setting event loop to selector policy")
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())  # type: ignore


setup_platform_specific_functionality()

from .src import main
