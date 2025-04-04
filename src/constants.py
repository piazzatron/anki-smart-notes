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

from typing import cast

from anki.decks import DeckId

from .. import env
from .models import ChatModels, ChatProviders

SERVER_URL_PROD = "https://anki-smart-notes-server-production.up.railway.app"
SERVER_URL_DEV = "http://localhost:3000"

SITE_URL_PROD = "https://smart-notes.xyz"
SITE_URL_DEV = "http://localhost:3001"

RETRY_BASE_SECONDS = 5
MAX_RETRIES = 10
CHAT_CLIENT_TIMEOUT_SEC = 60
TTS_PROVIDER_TIMEOUT_SEC = 30
IMAGE_PROVIDER_TIMEOUT_SEC = 45

STANDARD_BATCH_LIMIT = 10

DEFAULT_CHAT_MODEL: ChatModels = "gpt-4o-mini"
DEFAULT_CHAT_PROVIDER: ChatProviders = "openai"

DEFAULT_TEMPERATURE = 1

# Errors
UNPAID_PROVIDER_ERROR = (
    "Only ChatGPT is supported for users without a Smart Notes subscription!"
)

APP_LOCKED_ERROR = (
    "Smart Notes: this option cannot be completed without a subscription or trial."
)

CHAINED_FIELDS_SKIPPED_ERROR = "Smart Notes: Looks like you have some chained smart fields, which require a subscription. Any chained fields will be skipped. This message will not show again."

# Plan ended errors

FREE_TRIAL_ENDED_CAPACITY_API_KEY = "Smart Notes: Your free trial capacity has been used up! Please upgrade to continue using Smart Notes. Smart Notes will continue with limited functionality using your OpenAI API key."
FREE_TRIAL_ENDED_EXPIRED_API_KEY = "Smart Notes: Your free trial capacity has been used up! Please upgrade to continue using Smart Notes. Smart Notes will continue with limited functionality using your OpenAI API key."
FREE_TRIAL_ENDED_CAPACITY_NO_API_KEY = "Smart Notes: Your free trial capacity has been used up! Please upgrade to continue using Smart Notes."
FREE_TRIAL_ENDED_EXPIRED_NO_API_KEY = "Smart Notes: Your free trial capacity has been used up! Please upgrade to continue using Smart Notes."

PAID_PLAN_ENDED_CAPACITY_API_KEY = "Smart Notes: Your subscription capacity has been used up. Please upgrade to a higher plan to continue using Smart Notes. Smart Notes will continue with limited functionality using your OpenAI API key."
PAID_PLAN_ENDED_EXPIRED_API_KEY = "Smart Notes: Your subscription has expired. Smart Notes will continue with limited functionality using your OpenAI API key."
PAID_PLAN_ENDED_CAPACITY_NO_API_KEY = "Smart Notes: Your subscription capacity has been used up. Please upgrade to a higher plan to continue using Smart Notes."
PAID_PLAN_ENDED_EXPIRED_NO_API_KEY = "Smart Notes: Your subscription has expired. Please subscribe to continue using Smart Notes."

EXCEEDED_TEXT_CAPACITY = "Smart Notes: You've used all your text credits! TTS and image will still function if you have enough credits."
EXCEEDED_IMAGE_CAPACITY = "Smart Notes: You've used all your image credits! Text and TTS will still function if you have enough credits."
EXCEEDED_TTS_CAPACITY = "Smart Notes: You've used all your TTS credits! Text and image will still function if you have enough credits."

GENERIC_CREDITS_MESSAGE = "Smart Notes: You have run out of credits for this operation 😕! Check the account tab for more information and consider upgrading to a larger plan."


def get_server_url() -> str:
    return SERVER_URL_PROD if env.environment == "PROD" else SERVER_URL_DEV


def get_site_url() -> str:
    return SITE_URL_PROD if env.environment == "PROD" else SITE_URL_DEV


GLOBAL_DECK_ID: DeckId = cast(DeckId, -1)
GLOBAL_DECK_NAME = "All Decks"
