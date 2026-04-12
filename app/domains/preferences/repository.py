import sqlite3
from contextlib import contextmanager

from app.core.config import Settings, get_settings
from app.domains.preferences.schemas import AppPreferences, SortMode, ThemeMode


class PreferencesRepository:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.settings.ensure_runtime_dirs()
        self._initialize()

    @contextmanager
    def _connect(self):
        connection = sqlite3.connect(self.settings.database_path)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def _initialize(self) -> None:
        defaults = (
            ("content_root", str(self.settings.content_root)),
            ("sort_mode", "alphabetical"),
            ("theme_mode", "light"),
            ("editor_font_size", "16"),
        )
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS app_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS item_preferences (
                    path TEXT PRIMARY KEY,
                    parent_path TEXT NOT NULL,
                    manual_order INTEGER NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_item_preferences_parent
                ON item_preferences (parent_path, manual_order)
                """
            )
            connection.executemany(
                "INSERT OR IGNORE INTO app_settings(key, value) VALUES(?, ?)",
                defaults,
            )

    def get_app_preferences(self) -> AppPreferences:
        with self._connect() as connection:
            rows = connection.execute("SELECT key, value FROM app_settings").fetchall()

        values = {row["key"]: row["value"] for row in rows}
        return AppPreferences(
            content_root=values["content_root"],
            sort_mode=values["sort_mode"],
            theme_mode=values.get("theme_mode", "light"),
            editor_font_size=int(values.get("editor_font_size", "16")),
        )

    def update_app_preferences(
        self,
        *,
        content_root: str | None = None,
        sort_mode: SortMode | None = None,
        theme_mode: ThemeMode | None = None,
        editor_font_size: int | None = None,
    ) -> AppPreferences:
        updates: list[tuple[str, str]] = []
        if content_root is not None:
            updates.append(("content_root", content_root))
        if sort_mode is not None:
            updates.append(("sort_mode", sort_mode))
        if theme_mode is not None:
            updates.append(("theme_mode", theme_mode))
        if editor_font_size is not None:
            updates.append(("editor_font_size", str(editor_font_size)))

        if updates:
            with self._connect() as connection:
                connection.executemany(
                    "INSERT OR REPLACE INTO app_settings(key, value) VALUES(?, ?)",
                    updates,
                )

        return self.get_app_preferences()

    def get_manual_order(self, parent_path: str) -> dict[str, int]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT path, manual_order
                FROM item_preferences
                WHERE parent_path = ?
                ORDER BY manual_order ASC
                """,
                (parent_path,),
            ).fetchall()

        return {row["path"]: row["manual_order"] for row in rows}

    def set_manual_order(self, parent_path: str, ordered_paths: list[str]) -> None:
        with self._connect() as connection:
            connection.execute(
                "DELETE FROM item_preferences WHERE parent_path = ?",
                (parent_path,),
            )
            connection.executemany(
                """
                INSERT INTO item_preferences(path, parent_path, manual_order)
                VALUES(?, ?, ?)
                """,
                [
                    (path, parent_path, index)
                    for index, path in enumerate(ordered_paths)
                ],
            )
