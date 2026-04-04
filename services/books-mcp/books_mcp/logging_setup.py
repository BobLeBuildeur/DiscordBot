"""Configure file logging for books-mcp (stdio-safe: no INFO to stdout)."""

from __future__ import annotations

import logging
import logging.handlers
import sys
from pathlib import Path

from books_mcp.config import get_settings

_CONFIGURED = False


def reset_logging_configuration() -> None:
    """Clear handlers and allow ``configure_logging`` to run again (for tests)."""
    global _CONFIGURED
    _CONFIGURED = False
    logger = logging.getLogger("books_mcp")
    logger.handlers.clear()


def _parse_level(name: str) -> int:
    level = getattr(logging, name.upper(), None)
    if isinstance(level, int):
        return level
    return logging.INFO


def configure_logging() -> None:
    """Attach rotating file handler and optional stderr mirror (WARNING+) to ``books_mcp``."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    settings = get_settings()
    log_path = Path(settings.books_log_path).resolve()
    level = _parse_level(settings.books_log_level)

    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        logging.getLogger("books_mcp").error(
            "Cannot create log directory %s: %s",
            log_path.parent,
            e,
        )
        _CONFIGURED = True
        return

    root = logging.getLogger("books_mcp")
    root.setLevel(level)
    root.handlers.clear()
    root.propagate = False

    fmt = logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")

    try:
        file_handler = logging.handlers.RotatingFileHandler(
            log_path,
            maxBytes=settings.books_log_max_bytes,
            backupCount=settings.books_log_backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(fmt)
        root.addHandler(file_handler)
    except OSError as e:
        logging.getLogger("books_mcp").error(
            "Cannot open log file %s: %s",
            log_path,
            e,
        )
        _CONFIGURED = True
        return

    if settings.books_log_mirror_stderr:
        stderr_handler = logging.StreamHandler(sys.stderr)
        stderr_handler.setLevel(logging.WARNING)
        stderr_handler.setFormatter(fmt)
        root.addHandler(stderr_handler)

    root.info(
        "Logging initialized: path=%s level=%s max_bytes=%s backup_count=%s stderr_mirror=%s",
        log_path,
        logging.getLevelName(level),
        settings.books_log_max_bytes,
        settings.books_log_backup_count,
        settings.books_log_mirror_stderr,
    )

    _CONFIGURED = True
