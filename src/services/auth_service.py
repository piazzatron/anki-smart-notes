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

from ..app_state import app_state
from ..config import config
from ..sentry import sentry


def refresh_account() -> None:
    """Fetch the latest subscription and credit usage from the API."""
    app_state.update_account_state()


def logout() -> None:
    """Clear authentication and immediately project the signed-out state."""
    config.auth_token = None
    if sentry:
        sentry.set_user()
    app_state.update_account_state()
