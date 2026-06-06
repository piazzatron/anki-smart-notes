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
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from src.models import (
    ChatGenerationSettings,
    ImageGenerationSettings,
    TTSGenerationSettings,
)
from src.models.smart_fields import ChatSmartFieldSettings


def _ok(result: Any) -> dict[str, Any]:
    return {"result": result, "error": None}


def _err(message: str) -> dict[str, Any]:
    return {"result": None, "error": message}


def _make_server():
    from src.local_server import LocalServer

    processor = MagicMock()
    return LocalServer(processor)


def _make_app():
    server = _make_server()
    app = web.Application()
    app.router.add_post("/", server._handle_request)
    app.router.add_post("/auth/callback", server._handle_auth_callback)
    app.router.add_options("/auth/callback", server._handle_auth_preflight)
    app.router.add_get("/ping", server._handle_loopback_ping)
    app.router.add_options("/ping", server._handle_ping_preflight)
    return app


ALLOWED_ORIGIN = "https://smart-notes.xyz"


def make_request(action: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    req: dict[str, Any] = {"action": action, "version": 1}
    if params is not None:
        req["params"] = params
    return req


async def _post(client: TestClient, data: dict[str, Any]) -> dict[str, Any]:
    resp = await client.post("/", json=data)
    return await resp.json()


def _patch_smart_field_save_deps(monkeypatch, prompt_error: str | None = None) -> None:
    import src.local_server

    fake_mw = MagicMock()
    fake_mw.col.models.by_name.return_value = {"name": "Basic", "id": 123, "flds": []}
    monkeypatch.setattr(src.local_server, "mw", fake_mw)
    monkeypatch.setattr(src.local_server, "get_note_type_id_from_name", lambda _: 123)
    monkeypatch.setattr(src.local_server, "_run_on_main_sync", lambda fn: fn())
    monkeypatch.setattr(
        src.local_server,
        "prompt_has_error",
        lambda *_, **__: prompt_error,
    )


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


@pytest.mark.asyncio
async def test_add_smart_field_missing_params():
    async with TestClient(TestServer(_make_app())) as client:
        data = await _post(client, make_request("addSmartField", {"noteType": "Basic"}))
        assert data["error"] == "noteType, field, and prompt are required"


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
    smart_field_service = _fake_smart_field_service()
    monkeypatch.setattr(src.local_server, "smart_field_service", smart_field_service)
    _patch_smart_field_save_deps(monkeypatch)

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
        smart_field_service.save_smart_field.assert_called_once()
        saved_field = smart_field_service.save_smart_field.call_args.args[0]
        assert isinstance(saved_field.settings, ChatSmartFieldSettings)
        assert saved_field.settings.uses_default_generation_settings is True


@pytest.mark.asyncio
async def test_add_smart_field_rejects_invalid_prompt(monkeypatch):
    import src.local_server

    monkeypatch.setattr(
        src.local_server,
        "get_prompts_for_note",
        lambda note_type, deck_id, fallback_to_global_deck=False: None,
    )
    smart_field_service = _fake_smart_field_service()
    monkeypatch.setattr(src.local_server, "smart_field_service", smart_field_service)
    _patch_smart_field_save_deps(
        monkeypatch, "Cannot reference TTS or image fields in prompts"
    )

    async with TestClient(TestServer(_make_app())) as client:
        data = await _post(
            client,
            make_request(
                "addSmartField",
                {
                    "noteType": "Basic",
                    "field": "Back",
                    "prompt": "Define {{Audio}}",
                },
            ),
        )
        assert data["error"] == "Cannot reference TTS or image fields in prompts"
        smart_field_service.save_smart_field.assert_not_called()


@pytest.mark.asyncio
async def test_add_smart_field_with_custom_reasoning_level(monkeypatch):
    import src.local_server

    monkeypatch.setattr(
        src.local_server,
        "get_prompts_for_note",
        lambda note_type, deck_id, fallback_to_global_deck=False: None,
    )
    smart_field_service = _fake_smart_field_service()
    monkeypatch.setattr(src.local_server, "smart_field_service", smart_field_service)
    _patch_smart_field_save_deps(monkeypatch)

    async with TestClient(TestServer(_make_app())) as client:
        data = await _post(
            client,
            make_request(
                "addSmartField",
                {
                    "noteType": "Basic",
                    "field": "Back",
                    "prompt": "Define {{Front}}",
                    "useCustomModel": True,
                    "chatOptions": {
                        "provider": "auto",
                        "model": "auto",
                        "reasoningLevel": "high",
                        "webSearch": False,
                    },
                },
            ),
        )
        assert data == _ok(True)
        saved_field = smart_field_service.save_smart_field.call_args.args[0]
        assert isinstance(saved_field.settings, ChatSmartFieldSettings)
        assert saved_field.settings.reasoning_level == "high"
        assert saved_field.settings.uses_default_generation_settings is False


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
    smart_field_service = _fake_smart_field_service()
    monkeypatch.setattr(src.local_server, "smart_field_service", smart_field_service)
    _patch_smart_field_save_deps(monkeypatch)

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
        smart_field_service.save_smart_field.assert_called_once()


def _fake_smart_field_service() -> MagicMock:
    service = MagicMock()
    service.get_chat_defaults.return_value = ChatGenerationSettings(
        provider="auto",
        model="auto",
        reasoning_level="off",
        web_search_enabled=False,
    )
    service.get_tts_defaults.return_value = TTSGenerationSettings(
        provider="openai",
        model="tts-1",
        voice_id="alloy",
    )
    service.get_image_defaults.return_value = ImageGenerationSettings(
        provider="openai",
        model="gpt-image-1.5-low",
    )
    return service


@pytest.mark.asyncio
async def test_remove_smart_field_missing_params():
    async with TestClient(TestServer(_make_app())) as client:
        data = await _post(
            client, make_request("removeSmartField", {"noteType": "Basic"})
        )
        assert data["error"] == "noteType and field are required"


@pytest.mark.asyncio
async def test_remove_smart_field_success(monkeypatch):
    import src.local_server

    smart_field_service = MagicMock()
    monkeypatch.setattr(src.local_server, "smart_field_service", smart_field_service)
    monkeypatch.setattr(src.local_server, "get_note_type_id_from_name", lambda _: 123)
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
        smart_field_service.delete_smart_field.assert_called_once_with(123, -1, "Back")


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
