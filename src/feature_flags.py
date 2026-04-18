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

from typing import TypedDict

import aiohttp

from .constants import get_server_url
from .logger import logger
from .sentry import run_async_in_background_with_sentry


class FeatureFlagsPayload(TypedDict, total=False):
    review_free_month: bool


class FeatureFlags:
    """Global feature flags fetched from the server. Callers read attributes
    directly; defaults apply until the first successful fetch completes."""

    review_free_month: bool = False


flags = FeatureFlags()


async def fetch_flags() -> FeatureFlagsPayload:
    async with (
        aiohttp.ClientSession() as session,
        session.get(
            f"{get_server_url()}/feature-flags",
            timeout=aiohttp.ClientTimeout(total=10),
        ) as response,
    ):
        response.raise_for_status()
        data: FeatureFlagsPayload = await response.json()
        return data


def refresh_feature_flags() -> None:
    """Fetch flags from the server and update the global `flags` object.
    Fires and forgets; failures are logged but non-fatal."""

    def on_success(payload: FeatureFlagsPayload) -> None:
        flags.review_free_month = bool(payload.get("review_free_month", False))
        logger.debug(
            f"Feature flags updated: review_free_month={flags.review_free_month}"
        )

    def on_failure(e: Exception) -> None:
        logger.warning(f"Failed to fetch feature flags: {e}")

    run_async_in_background_with_sentry(
        fetch_flags,
        on_success,
        on_failure,
        use_collection=False,
    )
