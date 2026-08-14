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

from copy import deepcopy
from typing import Any, Literal, Optional, TypedDict, Union

import aiohttp

from .config import config
from .constants import (
    APP_LOCKED_ERROR,
    FREE_TRIAL_ENDED_CAPACITY_API_KEY,
    FREE_TRIAL_ENDED_CAPACITY_NO_API_KEY,
    FREE_TRIAL_ENDED_EXPIRED_API_KEY,
    FREE_TRIAL_ENDED_EXPIRED_NO_API_KEY,
    PAID_PLAN_ENDED_CAPACITY_API_KEY,
    PAID_PLAN_ENDED_CAPACITY_NO_API_KEY,
    PAID_PLAN_ENDED_EXPIRED_API_KEY,
    PAID_PLAN_ENDED_EXPIRED_NO_API_KEY,
)
from .event_bus import StateInvalidated, event_bus
from .logger import logger
from .sentry import run_async_in_background_with_sentry
from .subscription_provider import (
    PlanInfo,
    UserStatus,
    subscription_provider,
)
from .ui.state_manager import StateManager
from .ui.ui_utils import show_message_box


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

    def bind(self, widget: Any) -> None:
        """Bind a widget to state changes."""
        self._state.bind(widget)

    def _publish_web_state(self, _state: AppState) -> None:
        """Keep connected webviews current when account state changes."""
        event_bus.publish(StateInvalidated())

    def is_free_trial(self) -> bool:
        state = self._state.s
        return (
            state["status"] == "AUTHENTICATED" and state["plan"]["planType"] == "trial"
        )

    def update_account_state(self) -> None:
        if not config.auth_token:
            logger.info("User is not authenticated")
            self._state.update(
                {"status": "UNAUTHENTICATED", "plan": None, "email": None}
            )
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

            old_state = self._state.s.copy()
            plan_conditions = get_plan_conditions(plan)
            functionality_degraded = self._did_functionality_degrade(
                old_state, plan_conditions
            )

            self._state.update(
                {
                    "status": "AUTHENTICATED",
                    "plan": plan,
                    "email": email,
                }
            )

            if functionality_degraded:
                self._handle_plan_became_blocked(plan, plan_conditions)

            self._check_capacity_threshold(plan)

        run_async_in_background_with_sentry(
            subscription_provider.get_user_status,
            on_new_status,
            on_failure,
            use_collection=False,
        )

    def _did_functionality_degrade(
        self, old_state: AppState, new_conditions: PlanConditions
    ) -> bool:
        if old_state["status"] != "AUTHENTICATED":
            return False

        old_conditions = get_plan_conditions(old_state["plan"])
        had_access = not any(old_conditions.values())
        is_blocked = any(new_conditions.values())
        if had_access and is_blocked:
            logger.info(
                f"Functionality degraded, new plan conditions: {new_conditions}"
            )
        return had_access and is_blocked

    def _handle_plan_became_blocked(
        self, plan: PlanInfo, conditions: PlanConditions
    ) -> None:
        plan_type = "trial" if plan["planType"] == "trial" else "paid"
        end_type = "expired" if conditions["expired"] else "capacity"
        is_api_key = has_api_key()
        messages = {
            ("trial", "capacity", False): FREE_TRIAL_ENDED_CAPACITY_NO_API_KEY,
            ("trial", "capacity", True): FREE_TRIAL_ENDED_CAPACITY_API_KEY,
            ("trial", "expired", False): FREE_TRIAL_ENDED_EXPIRED_NO_API_KEY,
            ("trial", "expired", True): FREE_TRIAL_ENDED_EXPIRED_API_KEY,
            ("paid", "capacity", False): PAID_PLAN_ENDED_CAPACITY_NO_API_KEY,
            ("paid", "capacity", True): PAID_PLAN_ENDED_CAPACITY_API_KEY,
            ("paid", "expired", False): PAID_PLAN_ENDED_EXPIRED_NO_API_KEY,
            ("paid", "expired", True): PAID_PLAN_ENDED_EXPIRED_API_KEY,
        }
        show_message_box(messages[(plan_type, end_type, is_api_key)])

    def _check_capacity_threshold(self, plan: Optional[PlanInfo]) -> None:
        """Alert user when they cross 50% capacity threshold."""
        if not plan or plan["planType"] == "trial":
            return

        capacity_percent = plan["totalCreditsUsed"] / plan["totalCreditsCapacity"] * 100
        did_show = config.did_show_capacity_threshold_this_cycle

        if capacity_percent < 50 and did_show:
            config.did_show_capacity_threshold_this_cycle = False
            return

        if capacity_percent >= 50 and not did_show:
            config.did_show_capacity_threshold_this_cycle = True
            show_message_box(
                "Smart Notes: You've used 50% of your credits this period. Check the account tab to see your usage breakdown."
            )


app_state = AppStateManager()

# Mode selection stuff


def is_capacity_remaining(show_box: bool = False) -> bool:
    state = app_state.state
    unlocked = state["status"] == "AUTHENTICATED" and not any(
        get_plan_conditions(state["plan"]).values()
    )
    if not unlocked and show_box:
        show_message_box(APP_LOCKED_ERROR)
    return unlocked


def has_api_key() -> bool:
    return bool(config.openai_api_key)


def is_app_legacy() -> bool:
    return not is_capacity_remaining() and has_api_key()


def is_capacity_remaining_or_legacy(show_box: bool = False) -> bool:
    allowed = is_capacity_remaining() or has_api_key()
    if not allowed and show_box:
        show_message_box(APP_LOCKED_ERROR)
    return allowed
