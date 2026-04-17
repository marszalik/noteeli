import sqlite3
from contextlib import contextmanager

from app.core.config import Settings, get_settings
from app.domains.preferences.schemas import AppPreferences, SortMode, ThemeMode, SourceType, ImageUploadMode  # noqa: F401


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
            ("source_type", "local"),
            ("content_root", str(self.settings.content_root)),
            ("sftp_host", ""),
            ("sftp_port", "22"),
            ("sftp_username", ""),
            ("sftp_password", ""),
            ("sftp_path", "/"),
            ("gdrive_folder_id", "root"),
            ("gdrive_credentials", ""),
            ("sort_mode", "alphabetical"),
            ("theme_mode", "light"),
            ("editor_font_size", "16"),
            ("image_upload_mode", "same_dir"),
            ("image_upload_subdir", "assets"),
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
            source_type=values.get("source_type", "local"),
            content_root=values["content_root"],
            sftp_host=values.get("sftp_host", ""),
            sftp_port=int(values.get("sftp_port", "22")),
            sftp_username=values.get("sftp_username", ""),
            sftp_password=values.get("sftp_password", ""),
            sftp_path=values.get("sftp_path", "/"),
            gdrive_folder_id=values.get("gdrive_folder_id", "root"),
            gdrive_credentials=values.get("gdrive_credentials", ""),
            sort_mode=values.get("sort_mode", "alphabetical"),
            theme_mode=values.get("theme_mode", "light"),
            editor_font_size=int(values.get("editor_font_size", "16")),
            image_upload_mode=values.get("image_upload_mode", "same_dir"),
            image_upload_subdir=values.get("image_upload_subdir", "assets"),
        )

    def update_app_preferences(
        self,
        *,
        source_type: SourceType | None = None,
        content_root: str | None = None,
        sftp_host: str | None = None,
        sftp_port: int | None = None,
        sftp_username: str | None = None,
        sftp_password: str | None = None,
        sftp_path: str | None = None,
        gdrive_folder_id: str | None = None,
        gdrive_credentials: str | None = None,
        sort_mode: SortMode | None = None,
        theme_mode: ThemeMode | None = None,
        editor_font_size: int | None = None,
        image_upload_mode: ImageUploadMode | None = None,
        image_upload_subdir: str | None = None,
    ) -> AppPreferences:
        updates: list[tuple[str, str]] = []
        if source_type is not None:
            updates.append(("source_type", source_type))
        if content_root is not None:
            updates.append(("content_root", content_root))
        if sftp_host is not None:
            updates.append(("sftp_host", sftp_host))
        if sftp_port is not None:
            updates.append(("sftp_port", str(sftp_port)))
        if sftp_username is not None:
            updates.append(("sftp_username", sftp_username))
        if sftp_password is not None:
            updates.append(("sftp_password", sftp_password))
        if sftp_path is not None:
            updates.append(("sftp_path", sftp_path))
        if gdrive_folder_id is not None:
            updates.append(("gdrive_folder_id", gdrive_folder_id))
        if gdrive_credentials is not None:
            updates.append(("gdrive_credentials", gdrive_credentials))
        if sort_mode is not None:
            updates.append(("sort_mode", sort_mode))
        if theme_mode is not None:
            updates.append(("theme_mode", theme_mode))
        if editor_font_size is not None:
            updates.append(("editor_font_size", str(editor_font_size)))
        if image_upload_mode is not None:
            updates.append(("image_upload_mode", image_upload_mode))
        if image_upload_subdir is not None:
            updates.append(("image_upload_subdir", image_upload_subdir))

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
