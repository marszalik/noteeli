"""SQLite-backed storage for the published-items table."""
from __future__ import annotations

import sqlite3

from app.core.config import Settings, get_settings


class PublishedItemsRepository:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.settings.ensure_runtime_dirs()
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.settings.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _ensure_schema(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS published_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    kind TEXT NOT NULL CHECK (kind IN ('file', 'directory')),
                    path TEXT NOT NULL UNIQUE,
                    slug TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT (datetime('now'))
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_published_path
                ON published_items(path)
                """
            )
            # Migration: older DBs have no user_key. Existing rows land in
            # the shared/legacy bucket ('') — the public page then falls
            # back to the global preferences, i.e. the previous behaviour.
            cols = [r[1] for r in connection.execute("PRAGMA table_info(published_items)")]
            if cols and "user_key" not in cols:
                connection.execute(
                    "ALTER TABLE published_items ADD COLUMN user_key TEXT NOT NULL DEFAULT ''"
                )

    def list_all(self) -> list[sqlite3.Row]:
        with self._connect() as connection:
            return list(
                connection.execute(
                    "SELECT id, kind, path, slug, created_at, user_key "
                    "FROM published_items ORDER BY created_at DESC"
                ).fetchall()
            )

    def find_by_id(self, item_id: int) -> sqlite3.Row | None:
        with self._connect() as connection:
            return connection.execute(
                "SELECT id, kind, path, slug, created_at, user_key "
                "FROM published_items WHERE id = ?",
                (item_id,),
            ).fetchone()

    def find_by_path(self, path: str) -> sqlite3.Row | None:
        with self._connect() as connection:
            return connection.execute(
                "SELECT id, kind, path, slug, created_at, user_key "
                "FROM published_items WHERE path = ?",
                (path,),
            ).fetchone()

    def insert(self, kind: str, path: str, slug: str, user_key: str = "") -> int:
        with self._connect() as connection:
            cursor = connection.execute(
                "INSERT INTO published_items(kind, path, slug, user_key) "
                "VALUES(?, ?, ?, ?)",
                (kind, path, slug, user_key),
            )
            return int(cursor.lastrowid)

    def delete_by_id(self, item_id: int) -> int:
        with self._connect() as connection:
            cursor = connection.execute(
                "DELETE FROM published_items WHERE id = ?", (item_id,)
            )
            return cursor.rowcount

    def delete_by_path_prefix(self, prefix: str) -> int:
        """Used when a published file/folder is renamed or deleted —
        wipes any published entry that becomes invalid as a result."""
        with self._connect() as connection:
            cursor = connection.execute(
                "DELETE FROM published_items "
                "WHERE path = ? OR path LIKE ?",
                (prefix, prefix + "/%"),
            )
            return cursor.rowcount
