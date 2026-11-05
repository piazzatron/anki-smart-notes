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

from typing import Literal

from .api_client import api

ANKIWEB_REVIEW_URL = "https://ankiweb.net/shared/review/1531888719"

# "available": show the offer; "claimed": the user said they left a review;
# "unavailable": they can't get the free month.
ReviewClaimState = Literal["available", "claimed", "unavailable"]
# "write": the "Write a review" click; "claim": the "I left a review" click.
ReviewClaimStep = Literal["write", "claim"]


async def get_review_claim_state() -> ReviewClaimState:
    response = await api.get_api_response(path="review-claim", method="GET")
    return (await response.json())["state"]


async def send_review_claim(step: ReviewClaimStep) -> ReviewClaimState:
    """Records a step of the free-month review offer on the server, which
    verifies the review against AnkiWeb and grants the month."""
    response = await api.get_api_response(path="review-claim", args={"step": step})
    return (await response.json())["state"]
