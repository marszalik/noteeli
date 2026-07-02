"""Rotating file logs for the running instance.

systemd's journal rotates away and is painful to search after the fact
("a user couldn't log in yesterday — what happened?"). This module adds a
daily-rotated file log under <data_dir>/logs/noteeli.log, keeping
NOTEELI_LOG_RETENTION_DAYS days (default 14), covering:

  - application loggers (auth denials, git failures, unexpected errors)
  - uvicorn error + access logs (the request trail around an incident)

Console/journal output is left untouched — the file is additive. Handlers
are tagged so repeated create_app() calls (tests spin up many apps with
different data dirs) replace our handler instead of stacking duplicates.
"""
from __future__ import annotations

import logging
import logging.handlers
from pathlib import Path

from app.core.config import Settings

_TAG = "_noteeli_file_handler"

# Loggers that should reach the file. Root covers app.* and any library
# warnings; uvicorn's loggers don't propagate to root, so they're wired
# explicitly.
_LOGGER_NAMES = ("", "uvicorn.error", "uvicorn.access")


def setup_file_logging(settings: Settings) -> Path | None:
    """Attach a shared daily-rotating file handler. Returns the log path,
    or None when the log directory can't be created (never fatal — the
    app must not die because a disk path is read-only)."""
    log_dir = settings.data_dir / "logs"
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        return None
    log_path = log_dir / "noteeli.log"

    handler = logging.handlers.TimedRotatingFileHandler(
        log_path,
        when="midnight",
        backupCount=max(1, settings.log_retention_days),
        encoding="utf-8",
        delay=True,  # don't touch the file until the first record
    )
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    setattr(handler, _TAG, True)

    for name in _LOGGER_NAMES:
        logger = logging.getLogger(name)
        # Drop any handler we added earlier (repeated create_app in tests,
        # or a different data_dir) so lines aren't duplicated.
        for existing in list(logger.handlers):
            if getattr(existing, _TAG, False):
                logger.removeHandler(existing)
                try:
                    existing.close()
                except Exception:
                    pass
        logger.addHandler(handler)
        # Make sure INFO-level records (access log lines, our warnings)
        # actually flow; don't lower a logger that's already more verbose.
        if logger.level > logging.INFO or logger.level == logging.NOTSET:
            if name:  # named loggers — root stays as configured
                logger.setLevel(logging.INFO)
    root = logging.getLogger()
    if root.level > logging.INFO or root.level == logging.NOTSET:
        root.setLevel(logging.INFO)

    return log_path
