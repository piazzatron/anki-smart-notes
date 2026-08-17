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

from . import env

SERVER_URL_PROD = "https://api.smart-notes.xyz"
SERVER_URL_DEV = "http://localhost:3003"

SITE_URL_PROD = "https://smart-notes.xyz"
SITE_URL_DEV = "http://localhost:3001"

# Vite dev server for the web app (`make web`); port pinned in vite.config.ts.
WEB_APP_DEV_URL = "http://localhost:5173/app/"

RETRY_BASE_SECONDS = 1
MAX_RETRIES = 3
CHAT_CLIENT_TIMEOUT_SEC = 60
TTS_PROVIDER_TIMEOUT_SEC = 30
IMAGE_PROVIDER_TIMEOUT_SEC = 120

STANDARD_BATCH_LIMIT = 10

# Errors
CHAINED_FIELDS_SKIPPED_ERROR = "Smart Notes: Looks like you have some chained smart fields, which require a subscription. Any chained fields will be skipped. This message will not show again."


def get_server_url() -> str:
    return SERVER_URL_PROD if env.environment == "PROD" else SERVER_URL_DEV


def get_site_url() -> str:
    return SITE_URL_PROD if env.environment == "PROD" else SITE_URL_DEV


GLOBAL_DECK_ID: DeckId = cast("DeckId", -1)
GLOBAL_DECK_NAME = "All Decks"
