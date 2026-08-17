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

import webbrowser

from .constants import get_site_url
from .logger import logger


def open_browser(path: str) -> None:
    url = f"{get_site_url()}{_with_plugin_utm_params(path)}"
    logger.info(f"Opening browser for signup: {url}")
    webbrowser.open(url, new=1)


def _with_plugin_utm_params(path: str) -> str:
    separator = "&" if "?" in path else "?"
    return f"{path}{separator}utm_source=plugin"
