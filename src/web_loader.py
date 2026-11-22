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

import asyncio
import hashlib
import io
import json
import shutil
import threading
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import aiohttp

from .constants import get_server_url
from .database import get_user_files_path
from .logger import logger
from .utils import get_version

# Downloaded builds, one folder per build number. Anki keeps user_files across
# add-on updates.
WEB_BUILDS_DIR = Path(get_user_files_path("web"))
# A build made from source beside the add-on, which only a development
# checkout has. It's served instead of a downloaded one.
LOCAL_BUILD_DIR = Path(__file__).parent / "web" / "static"
# What the window shows until the first build has downloaded.
LOADING_PAGE = Path(__file__).parent / "web" / "loading.html"

CHECK_INTERVAL_SEC = 6 * 60 * 60


@dataclass(frozen=True)
class Build:
    number: int
    # The oldest add-on version the build works with.
    min_plugin: str
    path: Path


def _version(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.split("."))


def installed_builds(builds_dir: Path) -> list[Build]:
    """The complete builds in `builds_dir`. A download still being unpacked is in
    a `.partial` folder, so it isn't one."""
    builds = []
    for build_json in builds_dir.glob("*/build.json"):
        if not build_json.parent.name.isdigit():
            continue
        info = json.loads(build_json.read_text())
        builds.append(Build(info["build"], info["minPlugin"], build_json.parent))
    return builds


def newest_compatible(builds: list[Build], plugin_version: str) -> Optional[Build]:
    compatible = [
        build
        for build in builds
        if _version(build.min_plugin) <= _version(plugin_version)
    ]
    return max(compatible, key=lambda build: build.number, default=None)


def install_build(
    *, zip_bytes: bytes, sha256: str, number: int, builds_dir: Path
) -> None:
    """Unpacks a downloaded build into `builds_dir/<number>`, which appears only
    once it's complete."""
    if hashlib.sha256(zip_bytes).hexdigest() != sha256:
        raise ValueError(f"web build {number} doesn't match its checksum")

    partial = builds_dir / f"{number}.partial"
    shutil.rmtree(partial, ignore_errors=True)
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as archive:
        archive.extractall(partial)
    partial.rename(builds_dir / str(number))


async def _get(url: str, **params: str) -> bytes:
    async with (
        aiohttp.ClientSession() as session,
        session.get(
            url, params=params, timeout=aiohttp.ClientTimeout(total=60)
        ) as response,
    ):
        response.raise_for_status()
        return await response.read()


def _track(event: str, properties: dict[str, Any]) -> None:
    # Imported here: telemetry imports the API client, which imports this.
    from .telemetry import track_event
    from .utils import run_on_main

    # track_event starts a Qt background op, which the main thread must create.
    run_on_main(lambda: track_event(event, properties))


class WebLoader:
    """Keeps the Smart Notes window's web app up to date: downloads the build our
    server names in the background and picks which one each window is served."""

    def __init__(self) -> None:
        # The folder /app serves, or None while there's no build yet.
        self.serving_dir: Optional[Path] = (
            LOCAL_BUILD_DIR if (LOCAL_BUILD_DIR / "index.html").exists() else None
        )
        self.serving_build: Optional[int] = None
        # The build our server last named. It's usually the newest, but older
        # when a newer one was withdrawn.
        self.target: Optional[int] = None
        # Whether the last check failed.
        self.failed = False
        # While a window shows the loading page: when it first did, and how many
        # times its Try again was pressed.
        self.loading_since: Optional[float] = None
        self.loading_retries = 0
        # Dev builds' window loads Vite; this makes it load the downloaded builds
        # from the local server instead, like a release (`cli/sn webbuild window`).
        self.served_in_dev = False
        self._checking = threading.Lock()
        self._started = False

    def start(self) -> None:
        """Checks for a new build now and every few hours while Anki runs."""
        if self._started:
            return
        self._started = True

        def run() -> None:
            while True:
                self.check()
                time.sleep(CHECK_INTERVAL_SEC)

        threading.Thread(target=run, daemon=True).start()

    def select_for_window(self) -> None:
        """Picks the build a window that's about to open is served. A build only
        ever changes here, never under an open window."""
        if (LOCAL_BUILD_DIR / "index.html").exists():
            self.serving_dir = LOCAL_BUILD_DIR
            return

        builds = installed_builds(WEB_BUILDS_DIR)
        chosen = self._choose(builds)
        self._serve(chosen)
        for build in builds:
            if build != chosen and build.number != self.target:
                shutil.rmtree(build.path, ignore_errors=True)

        threading.Thread(target=self.check, daemon=True).start()

    def check(self) -> None:
        """Downloads the build our server names, if it isn't here yet. Open
        windows keep the build they have, unless they have none."""
        with self._checking:
            first_install = self.serving_dir is None and not installed_builds(
                WEB_BUILDS_DIR
            )
            stage = "check"
            try:
                latest: dict[str, Any] = json.loads(
                    asyncio.run(
                        _get(f"{get_server_url()}/web/latest", plugin=get_version())
                    )
                )
                if not (WEB_BUILDS_DIR / str(latest["build"])).exists():
                    logger.info(f"Downloading web build {latest['build']}")
                    started = time.monotonic()
                    stage = "download"
                    zip_bytes = asyncio.run(_get(latest["url"]))
                    stage = "install"
                    WEB_BUILDS_DIR.mkdir(parents=True, exist_ok=True)
                    install_build(
                        zip_bytes=zip_bytes,
                        sha256=latest["sha256"],
                        number=latest["build"],
                        builds_dir=WEB_BUILDS_DIR,
                    )
                    _track(
                        "web_app_downloaded",
                        {
                            "build": latest["build"],
                            "seconds": round(time.monotonic() - started, 1),
                            "first_install": first_install,
                        },
                    )
                self.target = latest["build"]
                self.failed = False
            except Exception as e:
                self.failed = True
                _track(
                    "web_app_download_failed",
                    {"stage": stage, "first_install": first_install},
                )
                # Without any build the window can't open, so it's an error;
                # otherwise the window still works with the one on disk.
                if self.serving_dir is None and not installed_builds(WEB_BUILDS_DIR):
                    logger.error(f"Couldn't download the web app ({stage}): {e}")
                else:
                    logger.warning(f"Couldn't update the web app ({stage}): {e}")

            if self.serving_dir is None:
                self._serve(self._choose(installed_builds(WEB_BUILDS_DIR)))

    def update_ready(self) -> bool:
        """Whether a build other than the one served is here to switch to."""
        if (LOCAL_BUILD_DIR / "index.html").exists():
            return False
        chosen = self._choose(installed_builds(WEB_BUILDS_DIR))
        return chosen is not None and chosen.number != self.serving_build

    def apply_update(self) -> bool:
        """Switches to that build, on the user's own Check for updates, whose
        window then reloads into it."""
        if not self.update_ready():
            return False
        self._serve(self._choose(installed_builds(WEB_BUILDS_DIR)))
        return True

    def loading_shown(self) -> None:
        """A window is showing the loading page."""
        if self.loading_since is None:
            self.loading_since = time.monotonic()
            self.loading_retries = 0

    def loading_finished(self, outcome: str) -> None:
        """The loading page gave way to the app ("loaded") or its window
        closed first ("closed")."""
        if self.loading_since is None:
            return
        _track(
            "web_loading_screen",
            {
                "seconds": round(time.monotonic() - self.loading_since, 1),
                "outcome": outcome,
                "retries": self.loading_retries,
            },
        )
        self.loading_since = None

    def _choose(self, builds: list[Build]) -> Optional[Build]:
        compatible = [
            build
            for build in builds
            if _version(build.min_plugin) <= _version(get_version())
        ]
        named = [build for build in compatible if build.number == self.target]
        return named[0] if named else newest_compatible(compatible, get_version())

    def _serve(self, build: Optional[Build]) -> None:
        if build is None:
            return
        self.serving_dir = build.path
        self.serving_build = build.number
        # Imported here: sentry imports the API client, which imports this.
        from .sentry import sentry

        if sentry:
            with sentry.hub.configure_scope() as scope:
                scope.set_tag("web_version", build.number)

    def reset(self) -> None:
        """Forgets every downloaded build, as on a fresh install (dev tooling)."""
        shutil.rmtree(WEB_BUILDS_DIR, ignore_errors=True)
        self.serving_dir = None
        self.serving_build = None
        self.target = None
        self.failed = False
        self.loading_since = None


web_loader = WebLoader()
