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

from typing import List, Optional, TypedDict, Union

from .config import config
from .constants import (
    APP_LOCKED_ERROR,
    EXCEEDED_IMAGE_CAPACITY,
    EXCEEDED_TEXT_CAPACITY,
    EXCEEDED_TTS_CAPACITY,
    FREE_TRIAL_ENDED_CAPACITY_API_KEY,
    FREE_TRIAL_ENDED_CAPACITY_NO_API_KEY,
    FREE_TRIAL_ENDED_EXPIRED_API_KEY,
    FREE_TRIAL_ENDED_EXPIRED_NO_API_KEY,
    PAID_PLAN_ENDED_CAPACITY_API_KEY,
    PAID_PLAN_ENDED_CAPACITY_NO_API_KEY,
    PAID_PLAN_ENDED_EXPIRED_API_KEY,
    PAID_PLAN_ENDED_EXPIRED_NO_API_KEY,
)
from .logger import logger
from .sentry import run_async_in_background_with_sentry
from .subscription_provider import (
    PlanInfo,
    SubscriptionState,
    UserStatus,
    subscription_provider,
)
from .ui.state_manager import StateManager
from .ui.ui_utils import show_message_box


class AppState(TypedDict):
    subscription: SubscriptionState
    plan: Union[PlanInfo, None]


class AppStateManager:
    _state: StateManager[AppState]

    def __init__(self) -> None:
        self._state = StateManager[AppState]({"subscription": "LOADING", "plan": None})

    def is_free_trial(self) -> bool:
        free_trial_states: List[SubscriptionState] = [
            "FREE_TRIAL_ACTIVE",
            "FREE_TRIAL_CAPACITY",
            "FREE_TRIAL_PARTIAL_CAPACITY",
            "FREE_TRIAL_EXPIRED",
        ]
        return self._state.s["subscription"] in free_trial_states

    def update_subscription_state(self) -> None:
        if not config.auth_token:
            logger.debug("User is not authenticated")
            self._state.update({"subscription": "UNAUTHENTICATED", "plan": None})
            return

        def on_failure(_) -> None:
            logger.error("Got failure getting new status. Wiping auth.")
            config.auth_token = None
            self._state.update({"subscription": "LOADING", "plan": None})

        def on_new_status(status: Union[UserStatus, None]) -> None:
            logger.debug(f"Got new subscription status: {status}")

            if not status:
                logger.error(
                    "Got empty status. Possibly dead account. Logging user out."
                )
                config.auth_token = None
                on_failure(None)
                return

            if not status.get("plan"):
                if status.get("error"):
                    logger.error(f"Saw error in app_state: ${status['error']}")
                    on_failure(None)
                return

            old_state = self._state.s.copy()

            new_sub_state = self._make_subscription_state(status["plan"])
            old_sub_state = old_state["subscription"]

            sub_did_end = self._did_functionality_degrade(old_sub_state, new_sub_state)

            self._state.update({"subscription": new_sub_state, "plan": status["plan"]})

            if sub_did_end:
                self._handle_subscription_did_transition(new_sub_state, status["plan"])

        run_async_in_background_with_sentry(
            subscription_provider.get_subscription_status,
            on_new_status,
            on_failure,
            use_collection=False,
        )

    def _make_subscription_state(self, sub: Union[PlanInfo, None]) -> SubscriptionState:
        if not sub:
            return "NO_SUBSCRIPTION"

        is_free = sub["planId"] == "free"
        text_capacity_reached = did_exceed_text_capacity(sub)
        voice_capacity_reached = did_exceed_voice_capacity(sub)
        image_capacity_reached = did_exceed_image_capacity(sub)

        if (
            is_free
            and sub["notesLimit"]
            and sub["notesUsed"]
            and sub["notesUsed"] >= sub["notesLimit"]
        ):
            return "FREE_TRIAL_CAPACITY"

        if sub["daysLeft"] <= 0:
            return "FREE_TRIAL_EXPIRED" if is_free else "PAID_PLAN_EXPIRED"

        if text_capacity_reached and voice_capacity_reached and image_capacity_reached:
            return "FREE_TRIAL_CAPACITY" if is_free else "PAID_PLAN_CAPACITY"

        if text_capacity_reached or voice_capacity_reached or image_capacity_reached:
            return (
                "FREE_TRIAL_PARTIAL_CAPACITY"
                if is_free
                else "PAID_PLAN_PARTIAL_CAPACITY"
            )

        return "FREE_TRIAL_ACTIVE" if is_free else "PAID_PLAN_ACTIVE"

    def _did_functionality_degrade(
        self, old_state: SubscriptionState, new_state: SubscriptionState
    ) -> bool:
        # Never show it on first load

        if old_state == "LOADING":
            return False

        # Only show warning if new state isn't an active state
        active_states: List[SubscriptionState] = [
            "PAID_PLAN_ACTIVE",
            "FREE_TRIAL_ACTIVE",
        ]

        did_transition = old_state != new_state
        did_functionality_degrade = did_transition and new_state not in active_states
        if did_functionality_degrade:
            logger.debug(
                f"Functionality degraded, transitioned from {old_state} to {new_state}"
            )
        return did_functionality_degrade

    def _handle_subscription_did_transition(
        self, new_sub: SubscriptionState, plan: Optional[PlanInfo]
    ) -> None:
        plan_type = "trial" if "FREE" in new_sub else "paid"
        end_type: str

        if new_sub in ["FREE_TRIAL_CAPACITY", "PAID_PLAN_CAPACITY"]:
            end_type = "capacity"
        elif new_sub in ["FREE_TRIAL_EXPIRED", "PAID_PLAN_EXPIRED"]:
            end_type = "expired"
        elif new_sub in ["FREE_TRIAL_PARTIAL_CAPACITY", "PAID_PLAN_PARTIAL_CAPACITY"]:
            end_type = "partial_capacity"
        else:
            logger.error(f"Unexpected subscription state: {new_sub}")
            return

        err: str
        is_api_key = has_api_key()

        if end_type == "capacity":
            if plan_type == "trial":
                if is_api_key:
                    err = FREE_TRIAL_ENDED_CAPACITY_API_KEY
                else:
                    err = FREE_TRIAL_ENDED_CAPACITY_NO_API_KEY
            else:
                if is_api_key:
                    err = PAID_PLAN_ENDED_CAPACITY_API_KEY
                else:
                    err = PAID_PLAN_ENDED_CAPACITY_NO_API_KEY
        elif end_type == "expired":
            if plan_type == "trial":
                if is_api_key:
                    err = FREE_TRIAL_ENDED_EXPIRED_API_KEY
                else:
                    err = FREE_TRIAL_ENDED_EXPIRED_NO_API_KEY
            else:
                if is_api_key:
                    err = PAID_PLAN_ENDED_EXPIRED_API_KEY
                else:
                    err = PAID_PLAN_ENDED_EXPIRED_NO_API_KEY
        elif end_type == "partial_capacity":
            if did_exceed_image_capacity(plan):
                err = EXCEEDED_IMAGE_CAPACITY
            elif did_exceed_text_capacity(plan):
                err = EXCEEDED_TEXT_CAPACITY
            elif did_exceed_voice_capacity(plan):
                err = EXCEEDED_TTS_CAPACITY

        # Migrate you from anthropic to OpenAI if necessary
        if config.chat_provider == "anthropic":
            logger.debug("Migrating ot OpenAI chat provider")
            config.chat_provider = "openai"
            config.chat_model = "gpt-5-mini"

        if not err:
            logger.error(
                f"Unexpectedly couldnt find error for {plan_type}, {end_type}, {is_api_key}"
            )
            return
        else:
            show_message_box(err)


app_state = AppStateManager()

# Mode selection stuff


def is_app_unlocked(show_box=False) -> bool:
    state = app_state._state.s["subscription"]
    unlocked_states: List[SubscriptionState] = [
        "FREE_TRIAL_ACTIVE",
        "PAID_PLAN_ACTIVE",
        "FREE_TRIAL_PARTIAL_CAPACITY",
        "PAID_PLAN_PARTIAL_CAPACITY",
    ]

    unlocked = state in unlocked_states
    if not unlocked and show_box:
        show_message_box(APP_LOCKED_ERROR)
    return unlocked


def has_api_key() -> bool:
    return bool(config.openai_api_key)


def is_app_legacy() -> bool:
    return not is_app_unlocked() and has_api_key()


def is_app_unlocked_or_legacy(show_box=False) -> bool:
    allowed = is_app_unlocked() or has_api_key()
    if not allowed and show_box:
        show_message_box(APP_LOCKED_ERROR)
    return allowed


def did_exceed_image_capacity(sub: Optional[PlanInfo] = None) -> bool:
    sub = sub or app_state._state.s["plan"]
    if not sub:
        return False
    return sub["imageCreditsUsed"] >= sub["imageCreditsCapacity"]


def did_exceed_text_capacity(sub: Optional[PlanInfo] = None) -> bool:
    sub = sub or app_state._state.s["plan"]
    if not sub:
        return False
    return sub["textCreditsUsed"] >= sub["textCreditsCapacity"]


def did_exceed_voice_capacity(sub: Optional[PlanInfo] = None) -> bool:
    sub = sub or app_state._state.s["plan"]
    if not sub:
        return False
    return sub["voiceCreditsUsed"] >= sub["voiceCreditsCapacity"]
