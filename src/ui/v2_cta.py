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

from aqt import QWidget

from ..sentry import pinger
from ..tasks import run_async_in_background
from .webview_dialog import WebviewDialog


class V2CTA(WebviewDialog):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent, "/v2")
        run_async_in_background(pinger("show_trial_cta"), use_collection=False)
        self.setMinimumHeight(1200)
