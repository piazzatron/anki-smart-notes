# type: ignore

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

import json
from typing import Any
from unittest.mock import MagicMock

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer


def _make_server():
    from src.local_server import LocalServer

    return LocalServer()


def _make_app(server=None):
    server = server or _make_server()
    app = web.Application()
    app.router.add_post("/auth/callback", server._handle_auth_callback)
    app.router.add_options("/auth/callback", server._handle_auth_preflight)
    app.router.add_get("/ping", server._handle_loopback_ping)
    app.router.add_options("/ping", server._handle_ping_preflight)
    app.router.add_get("/api/events", server._handle_events)
    return app


ALLOWED_ORIGIN = "https://smart-notes.xyz"


# -- /auth/callback --


def _patch_auth_callback_deps(monkeypatch):
    """Replace config/sentry/app_state so _handle_auth_callback is pure."""
    import src.local_server

    written: dict[str, Any] = {"jwt": None}

    class FakeConfig:
        auth_token = None

    fake_config = FakeConfig()

    def fake_run_on_main(fn):
        fn()
        written["jwt"] = fake_config.auth_token

    fake_mw = MagicMock()
    fake_mw.taskman.run_on_main = fake_run_on_main
    monkeypatch.setattr(src.local_server, "config", fake_config)
    monkeypatch.setattr(src.local_server, "mw", fake_mw)
    monkeypatch.setattr(src.local_server, "sentry", None)
    monkeypatch.setattr(src.local_server, "app_state", MagicMock())
    return written


@pytest.mark.asyncio
async def test_auth_callback_happy_path(monkeypatch):
    written = _patch_auth_callback_deps(monkeypatch)

    async with TestClient(TestServer(_make_app())) as client:
        resp = await client.post(
            "/auth/callback",
            json={"jwt": "abc.def.ghi"},
            headers={"Origin": ALLOWED_ORIGIN},
        )
        assert resp.status == 200
        assert (await resp.json()) == {"ok": True}
        assert resp.headers["Access-Control-Allow-Origin"] == ALLOWED_ORIGIN
        assert written["jwt"] == "abc.def.ghi"


@pytest.mark.asyncio
async def test_auth_callback_rejects_bad_origin(monkeypatch):
    _patch_auth_callback_deps(monkeypatch)

    async with TestClient(TestServer(_make_app())) as client:
        resp = await client.post(
            "/auth/callback",
            json={"jwt": "abc.def.ghi"},
            headers={"Origin": "https://evil.com"},
        )
        assert resp.status == 403
        assert "Access-Control-Allow-Origin" not in resp.headers


@pytest.mark.asyncio
async def test_auth_callback_rejects_missing_origin(monkeypatch):
    _patch_auth_callback_deps(monkeypatch)

    async with TestClient(TestServer(_make_app())) as client:
        resp = await client.post("/auth/callback", json={"jwt": "abc.def.ghi"})
        assert resp.status == 403


@pytest.mark.asyncio
async def test_auth_callback_invalid_json(monkeypatch):
    _patch_auth_callback_deps(monkeypatch)

    async with TestClient(TestServer(_make_app())) as client:
        resp = await client.post(
            "/auth/callback",
            data=b"not json",
            headers={
                "Origin": ALLOWED_ORIGIN,
                "Content-Type": "application/json",
            },
        )
        assert resp.status == 400
        body = await resp.json()
        assert body["error"] == "invalid_json"


@pytest.mark.asyncio
async def test_auth_callback_missing_jwt(monkeypatch):
    _patch_auth_callback_deps(monkeypatch)

    async with TestClient(TestServer(_make_app())) as client:
        resp = await client.post(
            "/auth/callback", json={}, headers={"Origin": ALLOWED_ORIGIN}
        )
        assert resp.status == 400
        assert (await resp.json())["error"] == "missing_jwt"


@pytest.mark.asyncio
async def test_auth_callback_non_string_jwt(monkeypatch):
    _patch_auth_callback_deps(monkeypatch)

    async with TestClient(TestServer(_make_app())) as client:
        resp = await client.post(
            "/auth/callback",
            json={"jwt": 42},
            headers={"Origin": ALLOWED_ORIGIN},
        )
        assert resp.status == 400


@pytest.mark.asyncio
async def test_auth_preflight_allowed_origin():
    async with TestClient(TestServer(_make_app())) as client:
        resp = await client.options(
            "/auth/callback", headers={"Origin": ALLOWED_ORIGIN}
        )
        assert resp.status == 204
        assert resp.headers["Access-Control-Allow-Origin"] == ALLOWED_ORIGIN
        assert resp.headers["Access-Control-Allow-Private-Network"] == "true"
        assert "POST" in resp.headers["Access-Control-Allow-Methods"]


@pytest.mark.asyncio
async def test_auth_preflight_rejects_bad_origin():
    async with TestClient(TestServer(_make_app())) as client:
        resp = await client.options(
            "/auth/callback", headers={"Origin": "https://evil.com"}
        )
        assert resp.status == 403


# -- /ping --


@pytest.mark.asyncio
async def test_loopback_ping_returns_ok():
    async with TestClient(TestServer(_make_app())) as client:
        resp = await client.get("/ping", headers={"Origin": ALLOWED_ORIGIN})
        assert resp.status == 200
        assert (await resp.json()) == {"ok": True}
        assert resp.headers["Access-Control-Allow-Origin"] == ALLOWED_ORIGIN


@pytest.mark.asyncio
async def test_loopback_ping_open_to_any_origin():
    # Intentionally no origin allowlist — the response is a harmless no-op
    # and the PNA consent prompt is not worth protecting here.
    async with TestClient(TestServer(_make_app())) as client:
        resp = await client.get("/ping", headers={"Origin": "https://evil.com"})
        assert resp.status == 200
        assert (await resp.json()) == {"ok": True}


@pytest.mark.asyncio
async def test_loopback_ping_preflight():
    async with TestClient(TestServer(_make_app())) as client:
        resp = await client.options("/ping", headers={"Origin": ALLOWED_ORIGIN})
        assert resp.status == 204
        assert resp.headers["Access-Control-Allow-Private-Network"] == "true"


# -- /api/events --


async def _read_sse_event(resp) -> dict[str, Any]:
    event: dict[str, Any] = {}
    while True:
        line = (await resp.content.readline()).decode().strip()
        if not line:
            return event
        key, _, value = line.partition(": ")
        event[key] = value


@pytest.mark.asyncio
async def test_events_rejects_missing_token():
    async with TestClient(TestServer(_make_app())) as client:
        resp = await client.get("/api/events")
        assert resp.status == 401


@pytest.mark.asyncio
async def test_events_rejects_wrong_token():
    async with TestClient(TestServer(_make_app())) as client:
        resp = await client.get("/api/events?token=wrong")
        assert resp.status == 401


@pytest.mark.asyncio
async def test_events_rejects_non_localhost_host_header():
    server = _make_server()
    async with TestClient(TestServer(_make_app(server))) as client:
        resp = await client.get(
            f"/api/events?token={server.session_token}",
            headers={"Host": "evil.example.com:8766"},
        )
        assert resp.status == 403


@pytest.mark.asyncio
async def test_events_sends_state_on_connect_then_forwards_events(monkeypatch):
    import src.local_server
    from src.web import dto
    from src.web.event_bus import BrowserSelectionChanged, StateInvalidated, event_bus

    fake_state = {"schemaVersion": 1, "smartFields": []}
    monkeypatch.setattr(src.local_server, "_run_on_main_sync", lambda fn: fn())
    monkeypatch.setattr(dto, "build_state", lambda: fake_state)

    server = _make_server()
    async with TestClient(TestServer(_make_app(server))) as client:
        resp = await client.get(f"/api/events?token={server.session_token}")
        assert resp.status == 200
        assert resp.headers["Content-Type"] == "text/event-stream"

        # The snapshot is the head of the stream.
        event = await _read_sse_event(resp)
        assert event["event"] == "state"
        assert json.loads(event["data"]) == fake_state

        # Ephemeral events are forwarded with their payload.
        event_bus.publish(BrowserSelectionChanged({"note": None, "count": 2}))
        event = await _read_sse_event(resp)
        assert event["event"] == "anki.browserSelectionChanged"
        assert json.loads(event["data"]) == {"note": None, "count": 2}

        # Invalidation triggers a fresh whole-state push.
        event_bus.publish(StateInvalidated())
        event = await _read_sse_event(resp)
        assert event["event"] == "state"
        assert json.loads(event["data"]) == fake_state
