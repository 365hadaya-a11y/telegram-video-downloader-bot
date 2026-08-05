"""Centralised logging setup (console + rotating file)."""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler

from ..config import Settings

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_QUIET_LOGGERS = (
    "aiogram.event",
    "aiogram.dispatcher",
    "urllib3",
    "aiohttp.access",
    "asyncio",
)


def _make_stream_encoding_safe() -> None:
    """Stop cp1252 consoles from crashing on emoji in log lines (Windows)."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(errors="replace")
            except (OSError, ValueError):
                pass


def setup_logging(settings: Settings) -> None:
    """Configure console + rotating file handlers once."""
    settings.log_dir.mkdir(parents=True, exist_ok=True)
    _make_stream_encoding_safe()

    root = logging.getLogger()
    root.setLevel(settings.log_level.upper())
    if root.handlers:
        root.handlers.clear()

    formatter = logging.Formatter(_LOG_FORMAT, _DATE_FORMAT)

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    root.addHandler(console)

    file_handler = RotatingFileHandler(
        settings.log_dir / "bot.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    for name in _QUIET_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)
