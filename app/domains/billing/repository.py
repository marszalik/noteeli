"""Billing repository — users and subscriptions tables."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Generator

from app.core.config import Settings


class BillingRepository:
    def __init__(self, settings: Settings) -> None:
        self._db_path = settings.database_path
        self._ensure_schema()

    @contextmanager
    def _connect(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
                    google_id          TEXT    NOT NULL UNIQUE,
                    email              TEXT    NOT NULL,
                    paddle_customer_id TEXT,
                    created_at         TEXT    NOT NULL DEFAULT (datetime('now'))
                );
                CREATE UNIQUE INDEX IF NOT EXISTS idx_users_google_id ON users (google_id);
                CREATE INDEX        IF NOT EXISTS idx_users_email     ON users (email);

                CREATE TABLE IF NOT EXISTS subscriptions (
                    user_id                INTEGER NOT NULL PRIMARY KEY
                                           REFERENCES users(id) ON DELETE CASCADE,
                    paddle_subscription_id TEXT    NOT NULL UNIQUE,
                    status                 TEXT    NOT NULL,
                    current_period_end     TEXT,
                    updated_at             TEXT    NOT NULL DEFAULT (datetime('now'))
                );
            """)

    # ── Users ────────────────────────────────────────────────────────────

    def get_or_create_user(self, google_id: str, email: str) -> int:
        """Return the DB user-id, creating a row if needed."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id FROM users WHERE google_id = ?", (google_id,)
            ).fetchone()
            if row:
                # Update email in case it changed (rare but possible).
                conn.execute(
                    "UPDATE users SET email = ? WHERE google_id = ?",
                    (email, google_id),
                )
                return row["id"]
            cur = conn.execute(
                "INSERT INTO users (google_id, email) VALUES (?, ?)",
                (google_id, email),
            )
            return cur.lastrowid  # type: ignore[return-value]

    def set_paddle_customer_id(self, user_id: int, paddle_customer_id: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE users SET paddle_customer_id = ? WHERE id = ?",
                (paddle_customer_id, user_id),
            )

    def get_paddle_customer_id(self, user_id: int) -> str | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT paddle_customer_id FROM users WHERE id = ?", (user_id,)
            ).fetchone()
            return row["paddle_customer_id"] if row else None

    def get_user_by_paddle_customer_id(self, paddle_customer_id: str) -> dict | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id, google_id, email FROM users WHERE paddle_customer_id = ?",
                (paddle_customer_id,),
            ).fetchone()
            return dict(row) if row else None

    # ── Subscriptions ────────────────────────────────────────────────────

    def upsert_subscription(
        self,
        user_id: int,
        paddle_subscription_id: str,
        status: str,
        current_period_end: str | None,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO subscriptions
                    (user_id, paddle_subscription_id, status, current_period_end, updated_at)
                VALUES (?, ?, ?, ?, datetime('now'))
                ON CONFLICT(user_id) DO UPDATE SET
                    paddle_subscription_id = excluded.paddle_subscription_id,
                    status                 = excluded.status,
                    current_period_end     = excluded.current_period_end,
                    updated_at             = datetime('now')
                """,
                (user_id, paddle_subscription_id, status, current_period_end),
            )

    def get_subscription(self, user_id: int) -> dict | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM subscriptions WHERE user_id = ?", (user_id,)
            ).fetchone()
            return dict(row) if row else None

    def is_subscription_active(self, user_id: int) -> bool:
        sub = self.get_subscription(user_id)
        if not sub:
            return False
        return sub["status"] in ("active", "trialing")
