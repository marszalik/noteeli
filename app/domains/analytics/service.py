"""Privacy-respecting page-view recorder for app.noteeli.com.

Mirror of web-noteeli's analytics.service — writes to the same
shared SQLite DB. The aggregations (read side) live only in the
portal admin; this module is write-only on this side.
"""
from __future__ import annotations

import hashlib
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator

from app.core.config import get_settings


_SKIP_PATH_PREFIXES = (
    "/static/",
    "/api/",
    "/webhooks/",
    "/auth/",
    "/admin",
    "/billing/",
    "/manifest.webmanifest",
    "/service-worker.js",
    "/favicon",
    "/.well-known/",
)

_BOT_HINTS = (
    "bot", "spider", "crawler", "crawl", "scraper", "scrape",
    "fetch", "monitor", "uptime", "lighthouse", "pingdom",
    "headlesschrome",
)


def _is_bot(user_agent: str) -> bool:
    if not user_agent:
        return True
    ua = user_agent.lower()
    return any(h in ua for h in _BOT_HINTS)


def _should_skip(path: str) -> bool:
    if not path or any(path.startswith(p) for p in _SKIP_PATH_PREFIXES):
        return True
    # Skip the public-published /id/slug routes too — too high cardinality.
    parts = path.strip("/").split("/")
    if len(parts) == 2 and parts[0].isdigit():
        return True
    return False


def _visitor_hash(ip: str, user_agent: str) -> str:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    raw = f"{today}|{ip}|{user_agent}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


@contextmanager
def _connect() -> Generator[sqlite3.Connection, None, None]:
    settings = get_settings()
    db = Path(settings.database_path)
    db.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def record_pageview(
    domain: str,
    path: str,
    referrer: str | None,
    ip: str,
    user_agent: str,
    user_id: int | None,
) -> None:
    if _should_skip(path) or _is_bot(user_agent):
        return
    vhash = _visitor_hash(ip, user_agent)
    ref = (referrer or "")[:200] or None
    try:
        with _connect() as conn:
            conn.execute(
                """
                INSERT INTO pageviews (domain, path, referrer, visitor_hash, user_id)
                VALUES (?, ?, ?, ?, ?)
                """,
                (domain, path[:300], ref, vhash, user_id),
            )
    except sqlite3.OperationalError:
        # Schema may not exist (e.g., self-host without portal). Silent skip.
        pass
