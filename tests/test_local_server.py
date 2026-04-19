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

from typing import Any
from unittest.mock import MagicMock

import pytest
from aiohttp.test_utils import TestClient, TestServer


def _ok(result: Any) -> dict[str, Any]:
    return {"result": result, "error": None}


def _err(message: str) -> dict[str, Any]:
    return {"result": None, "error": message}


def _make_app():
    from src.local_server import build_app

    return build_app(MagicMock())


ALLOWED_ORIGIN = "https://smart-notes.xyz"


def make_request(action: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    req: dict[str, Any] = {"action": action, "version": 1}
    if params is not None:
        req["params"] = params
    return req


async def _post(client: TestClient, data: dict[str, Any]) -> dict[str, Any]:
    resp = await client.post("/", json=data)
    return await resp.json()


# -- RPC dispatch ------------------------------------------------------------


@pytest.mark.asyncio
async def test_ping():
    async with TestClient(TestServer(_make_app())) as client:
        data = await _post(client, make_request("ping"))
        assert data == _ok("pong")


@pytest.mark.asyncio
async def test_invalid_json():
    async with TestClient(TestServer(_make_app())) as client:
        resp = await client.post(
            "/", data=b"not json", headers={"Content-Type": "application/json"}
        )
        data = await resp.json()
        assert data["error"] is not None


@pytest.mark.asyncio
async def test_bad_version():
    async with TestClient(TestServer(_make_app())) as client:
        data = await _post(client, {"action": "ping", "version": 99})
        assert data == _err("Unsupported version: 99, expected 1")


@pytest.mark.asyncio
async def test_unknown_action():
    async with TestClient(TestServer(_make_app())) as client:
        data = await _post(client, make_request("nonExistent"))
        assert data == _err("Unknown action: nonExistent")


# -- getSmartFields ----------------------------------------------------------


@pytest.mark.asyncio
async def test_get_smart_fields_missing_note_type():
    async with TestClient(TestServer(_make_app())) as client:
        data = await _post(client, make_request("getSmartFields", {}))
        assert data == _err("noteType is required")


@pytest.mark.asyncio
async def test_get_smart_fields(monkeypatch):
    import src.local_server

    monkeypatch.setattr(
        src.local_server,
        "get_prompts_for_note",
        lambda note_type, deck_id, fallback_to_global_deck=True: {"Field1": "prompt1"},
    )
    monkeypatch.setattr(
        src.local_server,
        "get_extras",
        lambda note_type, field, deck_id: {"type": "chat", "automatic": True},
    )

    async with TestClient(TestServer(_make_app())) as client:
        data = await _post(
            client, make_request("getSmartFields", {"noteType": "Basic"})
        )
        assert data["error"] is None
        assert data["result"]["Field1"]["prompt"] == "prompt1"
        assert data["result"]["Field1"]["extras"]["type"] == "chat"


@pytest.mark.asyncio
async def test_get_smart_fields_empty(monkeypatch):
    import src.local_server

    monkeypatch.setattr(
        src.local_server,
        "get_prompts_for_note",
        lambda note_type, deck_id, fallback_to_global_deck=True: None,
    )

    async with TestClient(TestServer(_make_app())) as client:
        data = await _post(
            client, make_request("getSmartFields", {"noteType": "Basic"})
        )
        assert data == _ok({})


# -- addSmartField / updateSmartField ----------------------------------------


@pytest.mark.asyncio
async def test_add_smart_field_missing_field():
    async with TestClient(TestServer(_make_app())) as client:
        data = await _post(client, make_request("addSmartField", {"noteType": "Basic"}))
        # dacite reports the first missing required field.
        assert data["error"] == "field is required"


@pytest.mark.asyncio
async def test_add_smart_field_missing_prompt():
    async with TestClient(TestServer(_make_app())) as client:
        data = await _post(
            client,
            make_request("addSmartField", {"noteType": "Basic", "field": "Back"}),
        )
        assert data["error"] == "prompt is required"


@pytest.mark.asyncio
async def test_add_smart_field_already_exists(monkeypatch):
    import src.local_server

    monkeypatch.setattr(
        src.local_server,
        "get_prompts_for_note",
        lambda note_type, deck_id, fallback_to_global_deck=False: {"Back": "existing"},
    )

    async with TestClient(TestServer(_make_app())) as client:
        data = await _post(
            client,
            make_request(
                "addSmartField",
                {"noteType": "Basic", "field": "Back", "prompt": "test"},
            ),
        )
        assert "already exists" in data["error"]


@pytest.mark.asyncio
async def test_add_smart_field_success(monkeypatch):
    import src.local_server

    monkeypatch.setattr(
        src.local_server,
        "get_prompts_for_note",
        lambda note_type, deck_id, fallback_to_global_deck=False: None,
    )
    monkeypatch.setattr(
        src.local_server,
        "add_or_update_prompts",
        lambda **kwargs: {"note_types": {}},
    )

    mock_config = MagicMock()
    mock_config.prompts_map = {"note_types": {}}
    monkeypatch.setattr(src.local_server, "config", mock_config)
    monkeypatch.setattr(src.local_server, "_run_on_main_sync", lambda fn: fn())

    async with TestClient(TestServer(_make_app())) as client:
        data = await _post(
            client,
            make_request(
                "addSmartField",
                {
                    "noteType": "Basic",
                    "field": "Back",
                    "prompt": "Define {{Front}}",
                },
            ),
        )
        assert data == _ok(True)


@pytest.mark.asyncio
async def test_update_smart_field_not_exists(monkeypatch):
    import src.local_server

    monkeypatch.setattr(
        src.local_server,
        "get_prompts_for_note",
        lambda note_type, deck_id, fallback_to_global_deck=False: None,
    )

    async with TestClient(TestServer(_make_app())) as client:
        data = await _post(
            client,
            make_request(
                "updateSmartField",
                {"noteType": "Basic", "field": "Back", "prompt": "test"},
            ),
        )
        assert "does not exist" in data["error"]


@pytest.mark.asyncio
async def test_update_smart_field_success(monkeypatch):
    import src.local_server

    monkeypatch.setattr(
        src.local_server,
        "get_prompts_for_note",
        lambda note_type, deck_id, fallback_to_global_deck=False: {
            "Back": "old prompt"
        },
    )
    monkeypatch.setattr(
        src.local_server,
        "add_or_update_prompts",
        lambda **kwargs: {"note_types": {}},
    )

    mock_config = MagicMock()
    mock_config.prompts_map = {"note_types": {}}
    monkeypatch.setattr(src.local_server, "config", mock_config)
    monkeypatch.setattr(src.local_server, "_run_on_main_sync", lambda fn: fn())

    async with TestClient(TestServer(_make_app())) as client:
        data = await _post(
            client,
            make_request(
                "updateSmartField",
                {
                    "noteType": "Basic",
                    "field": "Back",
                    "prompt": "New prompt {{Front}}",
                },
            ),
        )
        assert data == _ok(True)


# -- removeSmartField --------------------------------------------------------


@pytest.mark.asyncio
async def test_remove_smart_field_missing_field():
    async with TestClient(TestServer(_make_app())) as client:
        data = await _post(
            client, make_request("removeSmartField", {"noteType": "Basic"})
        )
        assert data["error"] == "field is required"


@pytest.mark.asyncio
async def test_remove_smart_field_success(monkeypatch):
    import src.local_server

    monkeypatch.setattr(
        src.local_server,
        "remove_prompt",
        lambda **kwargs: {"note_types": {}},
    )

    mock_config = MagicMock()
    mock_config.prompts_map = {"note_types": {}}
    monkeypatch.setattr(src.local_server, "config", mock_config)
    monkeypatch.setattr(src.local_server, "_run_on_main_sync", lambda fn: fn())

    async with TestClient(TestServer(_make_app())) as client:
        data = await _post(
            client,
            make_request(
                "removeSmartField",
                {"noteType": "Basic", "field": "Back"},
            ),
        )
        assert data == _ok(True)


# -- generateNote / generateNotes --------------------------------------------


@pytest.mark.asyncio
async def test_generate_note_missing_note_id():
    async with TestClient(TestServer(_make_app())) as client:
        data = await _post(client, make_request("generateNote", {}))
        assert data["error"] == "noteId is required"


@pytest.mark.asyncio
async def test_generate_note_no_collection(monkeypatch):
    import src.local_server

    monkeypatch.setattr(src.local_server, "mw", None)

    async with TestClient(TestServer(_make_app())) as client:
        data = await _post(client, make_request("generateNote", {"noteId": 1}))
        assert data["error"] == "Anki collection not available"


@pytest.mark.asyncio
async def test_generate_notes_missing_note_ids():
    async with TestClient(TestServer(_make_app())) as client:
        data = await _post(client, make_request("generateNotes", {}))
        assert data["error"] == "noteIds is required"


@pytest.mark.asyncio
async def test_generate_notes_no_collection(monkeypatch):
    import src.local_server

    monkeypatch.setattr(src.local_server, "mw", None)

    async with TestClient(TestServer(_make_app())) as client:
        data = await _post(client, make_request("generateNotes", {"noteIds": [1, 2]}))
        assert data["error"] == "Anki collection not available"


# -- /auth/callback ----------------------------------------------------------


def _patch_auth_callback_deps(monkeypatch):
    """Replace config/sentry/app_state so handle_auth_callback is pure."""
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
async def test_auth_callback_accepts_any_origin(monkeypatch):
    # No allowlist — the add-on trusts whoever can reach localhost.
    written = _patch_auth_callback_deps(monkeypatch)

    async with TestClient(TestServer(_make_app())) as client:
        resp = await client.post(
            "/auth/callback",
            json={"jwt": "abc.def.ghi"},
            headers={"Origin": "https://anywhere.example"},
        )
        assert resp.status == 200
        assert resp.headers["Access-Control-Allow-Origin"] == "https://anywhere.example"
        assert written["jwt"] == "abc.def.ghi"


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
async def test_auth_preflight_returns_cors_headers():
    async with TestClient(TestServer(_make_app())) as client:
        resp = await client.options(
            "/auth/callback", headers={"Origin": ALLOWED_ORIGIN}
        )
        assert resp.status == 204
        assert resp.headers["Access-Control-Allow-Origin"] == ALLOWED_ORIGIN
        assert resp.headers["Access-Control-Allow-Private-Network"] == "true"
        assert "POST" in resp.headers["Access-Control-Allow-Methods"]


# -- /subscription/refresh ---------------------------------------------------


@pytest.mark.asyncio
async def test_subscription_refresh_happy_path(monkeypatch):
    import src.local_server

    called = {"n": 0}

    def fake_run_on_main(fn):
        called["n"] += 1

    fake_mw = MagicMock()
    fake_mw.taskman.run_on_main = fake_run_on_main
    monkeypatch.setattr(src.local_server, "mw", fake_mw)
    monkeypatch.setattr(src.local_server, "app_state", MagicMock())

    async with TestClient(TestServer(_make_app())) as client:
        resp = await client.post(
            "/subscription/refresh",
            json={},
            headers={"Origin": ALLOWED_ORIGIN},
        )
        assert resp.status == 200
        assert (await resp.json()) == {"ok": True}
        assert resp.headers["Access-Control-Allow-Origin"] == ALLOWED_ORIGIN
        assert called["n"] == 1


# -- /ping -------------------------------------------------------------------


@pytest.mark.asyncio
async def test_loopback_ping_returns_ok():
    async with TestClient(TestServer(_make_app())) as client:
        resp = await client.get("/ping", headers={"Origin": ALLOWED_ORIGIN})
        assert resp.status == 200
        assert (await resp.json()) == {"ok": True}
        assert resp.headers["Access-Control-Allow-Origin"] == ALLOWED_ORIGIN


@pytest.mark.asyncio
async def test_loopback_ping_echoes_any_origin():
    async with TestClient(TestServer(_make_app())) as client:
        resp = await client.get("/ping", headers={"Origin": "https://anywhere.example"})
        assert resp.status == 200
        assert (await resp.json()) == {"ok": True}
        assert resp.headers["Access-Control-Allow-Origin"] == "https://anywhere.example"


@pytest.mark.asyncio
async def test_loopback_ping_preflight():
    async with TestClient(TestServer(_make_app())) as client:
        resp = await client.options("/ping", headers={"Origin": ALLOWED_ORIGIN})
        assert resp.status == 204
        assert resp.headers["Access-Control-Allow-Private-Network"] == "true"
