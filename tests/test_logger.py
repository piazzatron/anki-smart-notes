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

from pathlib import Path
from types import SimpleNamespace

import pytest

import src.logger as logger_module


def test_cleanup_logger_closes_log_file_handler(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    log_path = tmp_path / "smart-notes.log"
    log_path.write_text("old log", encoding="utf-8")

    monkeypatch.delenv("IS_TEST", raising=False)
    monkeypatch.setattr(
        logger_module,
        "mw",
        SimpleNamespace(
            addonManager=SimpleNamespace(getConfig=lambda _: {"debug": False})
        ),
    )
    monkeypatch.setattr(logger_module, "get_file_path", lambda _: str(log_path))

    stream = None
    try:
        logger_module.setup_logger()
        logger_module.logger.info("second line")
        file_handler = next(
            handler
            for handler in logger_module.logger.handlers
            if isinstance(handler, logger_module.logging.FileHandler)
        )
        stream = file_handler.stream

        log_text = log_path.read_text(encoding="utf-8")
        assert "old log" not in log_text
        assert "Starting app with info logging enabled" in log_text
        assert stream is not None
        assert not stream.closed
    finally:
        logger_module.cleanup_logger()

    assert stream is not None
    assert stream.closed


def test_setup_logger_continues_when_log_file_cannot_be_opened(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def raise_permission_error(*_args: object, **_kwargs: object) -> None:
        raise PermissionError("permission denied")

    monkeypatch.delenv("IS_TEST", raising=False)
    monkeypatch.setattr(
        logger_module,
        "mw",
        SimpleNamespace(
            addonManager=SimpleNamespace(getConfig=lambda _: {"debug": False})
        ),
    )
    monkeypatch.setattr(logger_module, "get_file_path", lambda _: "smart-notes.log")
    monkeypatch.setattr(logger_module.logging, "FileHandler", raise_permission_error)

    try:
        logger_module.setup_logger()
        captured = capsys.readouterr()

        assert "Could not open Smart Notes log file" in captured.out
        assert "Starting app with info logging enabled" in captured.out
        assert len(logger_module.logger.handlers) == 1
        assert isinstance(
            logger_module.logger.handlers[0], logger_module.logging.StreamHandler
        )
    finally:
        logger_module.cleanup_logger()


def test_cleanup_logger_removes_stream_handlers() -> None:
    try:
        logger_module.logger.addHandler(logger_module.logging.StreamHandler())
        assert logger_module.logger.handlers
    finally:
        logger_module.cleanup_logger()

    assert logger_module.logger.handlers == []
