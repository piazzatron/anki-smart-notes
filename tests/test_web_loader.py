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

import hashlib
import io
import json
import zipfile
from pathlib import Path

import pytest
from aiohttp.test_utils import TestClient, TestServer

import src.local_server
from src.web_loader import (
    WebLoader,
    install_build,
    installed_builds,
    newest_compatible,
)
from tests.test_local_server import _make_server  # pyright: ignore[reportPrivateUsage]

# pyright: reportPrivateUsage=false


def _zip(files: dict[str, str]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    return buffer.getvalue()


def _build(number: int, min_plugin: str) -> bytes:
    return _zip(
        {
            "build.json": json.dumps({"build": number, "minPlugin": min_plugin}),
            "index.html": f"<html>build {number}</html>",
        }
    )


def _install(builds_dir: Path, number: int, min_plugin: str = "2.0.0") -> None:
    zip_bytes = _build(number, min_plugin)
    install_build(
        zip_bytes=zip_bytes,
        sha256=hashlib.sha256(zip_bytes).hexdigest(),
        number=number,
        builds_dir=builds_dir,
    )


def test_picks_the_newest_build_this_add_on_can_run(tmp_path: Path) -> None:
    _install(tmp_path, 1, "2.9.0")
    _install(tmp_path, 2, "2.9.0")
    _install(tmp_path, 3, "2.10.0")
    # An unpacking download isn't a build yet.
    (tmp_path / "4.partial").mkdir()
    (tmp_path / "4.partial" / "build.json").write_text(
        json.dumps({"build": 4, "minPlugin": "2.0.0"})
    )

    builds = installed_builds(tmp_path)

    # 2.10.0 is newer than 2.9.5, though it sorts lower as text.
    assert newest_compatible(builds, "2.9.5").number == 2  # type: ignore[union-attr]
    assert newest_compatible(builds, "2.10.0").number == 3  # type: ignore[union-attr]
    assert newest_compatible(builds, "2.8.0") is None


def test_a_withdrawn_build_gives_way_to_the_one_the_server_names(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr("src.web_loader.get_version", lambda: "2.29.0")
    _install(tmp_path, 1)
    _install(tmp_path, 2)
    loader = WebLoader()

    # Before the first check, the newest build here.
    assert loader._choose(installed_builds(tmp_path)).number == 2  # type: ignore[union-attr]

    # Build 2 was withdrawn, so the server names build 1.
    loader.target = 1
    assert loader._choose(installed_builds(tmp_path)).number == 1  # type: ignore[union-attr]


def test_check_for_updates_switches_only_to_a_build_not_already_served(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr("src.web_loader.get_version", lambda: "2.29.0")
    monkeypatch.setattr("src.web_loader.WEB_BUILDS_DIR", tmp_path)
    monkeypatch.setattr("src.web_loader.LOCAL_BUILD_DIR", tmp_path / "no-local-build")
    _install(tmp_path, 1)
    loader = WebLoader()
    loader.target = 1
    assert loader.update_ready() is True
    assert loader.apply_update() is True
    assert loader.serving_build == 1

    assert loader.update_ready() is False
    assert loader.apply_update() is False

    _install(tmp_path, 2)
    loader.target = 2
    assert loader.apply_update() is True
    assert loader.serving_dir == tmp_path / "2"


def test_a_download_that_doesnt_match_its_checksum_is_never_installed(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError):
        install_build(
            zip_bytes=_build(5, "2.0.0"),
            sha256="0" * 64,
            number=5,
            builds_dir=tmp_path,
        )

    assert installed_builds(tmp_path) == []


@pytest.mark.asyncio
async def test_the_window_gets_the_loading_page_until_a_build_is_there(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    loader = src.local_server.web_loader
    monkeypatch.setattr(loader, "serving_dir", None)

    async with TestClient(TestServer(_make_server()._build_app())) as client:
        loading = await (await client.get("/app/")).text()
        assert "Smart Notes" in loading
        assert (await (await client.get("/loading/status")).json())["ready"] is False

        _install(tmp_path, 7)
        monkeypatch.setattr(loader, "serving_dir", tmp_path / "7")
        (tmp_path / "secret.txt").write_text("not part of the build")

        index = await client.get("/app/")
        assert await index.text() == "<html>build 7</html>"
        assert index.headers["Cache-Control"] == "no-cache"
        assert (await client.get("/app/build.json")).status == 200
        assert (await client.get("/app/../secret.txt")).status == 404
        assert (await client.get("/app/%2e%2e/secret.txt")).status == 404
        assert (await (await client.get("/loading/status")).json())["ready"] is True
