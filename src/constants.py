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

from .. import env
from .models import ChatModels, ChatProviders

SERVER_URL_PROD = "https://anki-smart-notes-server-production.up.railway.app"
SERVER_URL_DEV = "http://localhost:3000"

SITE_URL_PROD = "https://google.com"  # TOOD
SITE_URL_DEV = "http://localhost:3001"

RETRY_BASE_SECONDS = 5
MAX_RETRIES = 10
CHAT_CLIENT_TIMEOUT_SEC = 10
TTS_PROVIDER_TIMEOUT_SEC = 20

DEFAULT_CHAT_MODEL: ChatModels = "gpt-4o-mini"
DEFAULT_CHAT_PROVIDER: ChatProviders = "openai"

DEFAULT_TEMPERATURE = 0


def get_server_url() -> str:
    return SERVER_URL_PROD if env.environment == "PROD" else SERVER_URL_DEV


def get_site_url() -> str:
    return SITE_URL_PROD if env.environment == "PROD" else SITE_URL_DEV
