from __future__ import annotations

import logging

import pytest

from books_mcp.logging_setup import configure_logging, reset_logging_configuration


def test_configure_logging_writes_to_file(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    log_file = tmp_path / "books.log"
    monkeypatch.setenv("BOOKS_LOG_PATH", str(log_file))
    monkeypatch.setenv("BOOKS_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("BOOKS_LOG_MIRROR_STDERR", "false")

    reset_logging_configuration()
    configure_logging()

    logging.getLogger("books_mcp").info("smoke-test-log-line")

    text = log_file.read_text(encoding="utf-8")
    assert "smoke-test-log-line" in text
    assert "Logging initialized" in text

    reset_logging_configuration()
