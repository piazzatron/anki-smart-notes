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
from copy import deepcopy
from typing import Literal, Optional, TypedDict, Union

import aiohttp

from .config import config
from .event_bus import StateInvalidated, event_bus
from .logger import logger
from .sentry import run_async_in_background_with_sentry
from .subscription_provider import (
    PlanInfo,
    UserStatus,
    subscription_provider,
)
from .ui.state_manager import StateManager


class PendingAccountState(TypedDict):
    status: Literal["LOADING", "UNAUTHENTICATED"]
    plan: None
    email: None


class AuthenticatedAccountState(TypedDict):
    status: Literal["AUTHENTICATED"]
    plan: PlanInfo
    email: str


AppState = Union[PendingAccountState, AuthenticatedAccountState]


class PlanConditions(TypedDict):
    expired: bool
    note_limit_reached: bool
    credit_limit_reached: bool


def get_plan_conditions(plan: PlanInfo) -> PlanConditions:
    notes_used = plan["notesUsed"] or 0
    notes_limit = plan["notesLimit"]
    return {
        "expired": plan["daysLeft"] <= 0,
        "note_limit_reached": notes_limit is not None and notes_used >= notes_limit,
        "credit_limit_reached": plan["totalCreditsUsed"]
        >= plan["totalCreditsCapacity"],
    }


class AppStateManager:
    _state: StateManager[AppState]

    def __init__(self) -> None:
        self._state = StateManager[AppState](
            {"status": "LOADING", "plan": None, "email": None}
        )
        self._state.state_changed.connect(self._publish_web_state)

    @property
    def state(self) -> AppState:
        return deepcopy(self._state.s)

    def _publish_web_state(self, _state: AppState) -> None:
        """Keep connected webviews current when account state changes."""
        event_bus.publish(StateInvalidated())

    def is_free_trial(self) -> bool:
        state = self._state.s
        return (
            state["status"] == "AUTHENTICATED" and state["plan"]["planType"] == "trial"
        )

    def update_account_state(
        self,
        on_updated: Optional[Callable[[AppState], None]] = None,
    ) -> None:
        if not config.auth_token:
            logger.info("User is not authenticated")
            self._state.update(
                {"status": "UNAUTHENTICATED", "plan": None, "email": None}
            )
            if on_updated is not None:
                on_updated(self.state)
            return

        def on_failure(exc: Optional[Exception]) -> None:
            logger.error(f"Got failure getting new status: {exc}")
            # Self-heal: a stale/invalid token blocks the signin UI's logout
            # button. Clear it so the user can re-auth without manual steps.
            if isinstance(exc, aiohttp.ClientResponseError) and exc.status == 401:
                logger.info("Auth token rejected by server, clearing")
                config.auth_token = None
                self._state.update(
                    {
                        "status": "UNAUTHENTICATED",
                        "plan": None,
                        "email": None,
                    }
                )

        def on_new_status(status: Optional[UserStatus]) -> None:
            logger.debug(f"Got new account status: {status}")

            if not status:
                logger.error(
                    "Got empty status. Possibly dead account. Logging user out."
                )
                config.auth_token = None
                on_failure(None)
                return

            plan = status["plan"]
            email = status["email"]

            self._state.update(
                {
                    "status": "AUTHENTICATED",
                    "plan": plan,
                    "email": email,
                }
            )
            if on_updated is not None:
                on_updated(self.state)

        run_async_in_background_with_sentry(
            subscription_provider.get_user_status,
            on_new_status,
            on_failure,
            use_collection=False,
        )


app_state = AppStateManager()

# Mode selection stuff


def is_capacity_remaining() -> bool:
    state = app_state.state
    return state["status"] == "AUTHENTICATED" and not any(
        get_plan_conditions(state["plan"]).values()
    )


def has_legacy_openai_access() -> bool:
    return config.legacy_support is True and bool(config.openai_api_key)


def is_app_legacy() -> bool:
    return not is_capacity_remaining() and has_legacy_openai_access()


def is_capacity_remaining_or_legacy() -> bool:
    return is_capacity_remaining() or has_legacy_openai_access()
