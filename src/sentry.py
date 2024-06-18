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

import os
import sentry_sdk
import random

from sentry_sdk.integrations.asyncio import AsyncioIntegration
from sentry_sdk.integrations.aiohttp import AioHttpIntegration

from .ui.changelog import get_version
from .. import env
from .config import config

dsn = os.getenv("SENTRY_DSN")


def make_uuid() -> str:
    letters = "abcdefghijklmnopqrstuvwxyz1234567890"
    uuid = []
    for _ in range(16):
        uuid.append(random.choice(letters))
    return "".join(uuid)


print(make_uuid())


def init_sentry() -> None:
    # if env.environment != "PROD":
    #     return

    dsn = os.getenv("SENTRY_DSN")
    release = get_version()
    print(release)
    print(dsn)
    if not dsn or not release:
        print("No sentry DSN or release")
        return

    client = sentry_sdk.Client(dsn=dsn, release=release, default_integrations=False)
    hub = sentry_sdk.Hub(client)
    # sentry_sdk.init(
    #     dsn=dsn,
    #     release=release,
    #     integrations=[AsyncioIntegration(), AioHttpIntegration()],
    #     traces_sample_rate=1.0,
    #     # Set profiles_sample_rate to 1.0 to profile 100%
    #     # of sampled transactions.
    #     # We recommend adjusting this value in production.
    #     profiles_sample_rate=1.0,
    # )

    if not config.uuid:
        config.uuid = make_uuid()

    sentry_sdk.set_user({"id": config.uuid})
    hub.start_session()

    print("Sentry initialized")

    # try:
    #     # Your code here
    #     1 / 0
    # except Exception as e:
    #     print("CAPTURING EXCEPTION")
    #     hub.capture_exception(e)
    hub.end_session()
    hub.client.flush()


init_sentry()
