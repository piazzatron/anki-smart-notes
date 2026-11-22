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

from collections.abc import Callable
from typing import Optional

from .app_state import (
    AppState,
    app_state,
    is_capacity_remaining_or_legacy,
    is_free_plan,
)
from .config import config
from .web_app import open_web_app


def needs_free_plan_opt_in() -> bool:
    """The free plan generates nothing until the user has chosen it with
    Continue on Free on its first screen."""
    return is_free_plan() and not config.did_see_free_plan_welcome


def ensure_generation_available() -> bool:
    """Open the account UI and reject a user-triggered generation when blocked."""
    if needs_free_plan_opt_in():
        open_web_app()
        return False

    if is_capacity_remaining_or_legacy():
        return True

    open_generation_blocked_ui()
    return False


def ensure_paid_feature_available(feature: str) -> bool:
    """On the free plan, a paid feature (batch, or an image custom prompt) opens
    the upgrade sheet for it instead of running."""
    if not is_free_plan():
        return True

    open_web_app(upgrade_feature=feature)
    return False


def open_daily_limit_upgrade_ui() -> None:
    """A free user reached today's note cap. Opening Smart Notes refreshes the
    account, so the UI shows the new count under the upgrade sheet."""
    open_web_app(upgrade_feature="dailyLimit")


def open_generation_blocked_ui() -> None:
    open_web_app()


def refresh_account_if_trial_ended(
    *, open_screen: bool, otherwise: Optional[Callable[[], object]] = None
) -> None:
    """After a generation on the trial, refresh the account: the server moves a
    user whose trial ran out to the free plan on their next request. If it did,
    a hand-started generation opens Smart Notes on the free plan's first screen;
    otherwise `otherwise` runs."""
    if not app_state.is_free_trial():
        if otherwise:
            otherwise()
        return

    def on_updated(_: AppState) -> None:
        if needs_free_plan_opt_in():
            if open_screen:
                open_web_app()
        elif otherwise:
            otherwise()

    app_state.update_account_state(on_updated=on_updated)


def refresh_account_after_generation_rejected() -> None:
    """Refresh stale account data before deciding whether to open the account UI."""
    app_state.update_account_state(on_updated=_open_web_app_if_still_blocked)


def _open_web_app_if_still_blocked(_: AppState) -> None:
    ensure_generation_available()
