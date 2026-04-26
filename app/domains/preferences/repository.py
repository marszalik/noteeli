import json
import sqlite3
from contextlib import contextmanager

from app.core.config import Settings, get_settings
from app.domains.preferences.schemas import AppPreferences, SavedPreferencesProfile, SortMode, ThemeMode, SourceType, ImageUploadMode, Language  # noqa: F401


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
            ("autosave_enabled", "false"),
            ("image_upload_mode", "same_dir"),
            ("image_upload_subdir", "assets"),
            ("language", "pl"),
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
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS preference_profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    payload TEXT NOT NULL
                )
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
        return self._preferences_from_values(values)

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
        autosave_enabled: bool | None = None,
        image_upload_mode: ImageUploadMode | None = None,
        image_upload_subdir: str | None = None,
        language: Language | None = None,
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
        if autosave_enabled is not None:
            updates.append(("autosave_enabled", "true" if autosave_enabled else "false"))
        if image_upload_mode is not None:
            updates.append(("image_upload_mode", image_upload_mode))
        if image_upload_subdir is not None:
            updates.append(("image_upload_subdir", image_upload_subdir))
        if language is not None:
            updates.append(("language", language))

        if updates:
            with self._connect() as connection:
                connection.executemany(
                    "INSERT OR REPLACE INTO app_settings(key, value) VALUES(?, ?)",
                    updates,
                )

        return self.get_app_preferences()

    def list_profiles(self) -> list[SavedPreferencesProfile]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, name, payload
                FROM preference_profiles
                ORDER BY name COLLATE NOCASE ASC
                """
            ).fetchall()

        return [self._profile_from_row(row) for row in rows]

    def create_profile(self, name: str, preferences: AppPreferences) -> SavedPreferencesProfile:
        payload = json.dumps(preferences.model_dump(), ensure_ascii=False)
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO preference_profiles(name, payload)
                VALUES(?, ?)
                """,
                (name, payload),
            )
            row = connection.execute(
                """
                SELECT id, name, payload
                FROM preference_profiles
                WHERE id = ?
                """,
                (cursor.lastrowid,),
            ).fetchone()

        if row is None:
            raise RuntimeError("Saved profile could not be reloaded.")
        return self._profile_from_row(row)

    def update_profile(
        self,
        profile_id: int,
        name: str,
        preferences: AppPreferences,
    ) -> SavedPreferencesProfile | None:
        payload = json.dumps(preferences.model_dump(), ensure_ascii=False)
        with self._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE preference_profiles
                SET name = ?, payload = ?
                WHERE id = ?
                """,
                (name, payload, profile_id),
            )
            if cursor.rowcount == 0:
                return None
            row = connection.execute(
                """
                SELECT id, name, payload
                FROM preference_profiles
                WHERE id = ?
                """,
                (profile_id,),
            ).fetchone()

        if row is None:
            return None
        return self._profile_from_row(row)

    def delete_profile(self, profile_id: int) -> bool:
        with self._connect() as connection:
            cursor = connection.execute(
                "DELETE FROM preference_profiles WHERE id = ?",
                (profile_id,),
            )
        return cursor.rowcount > 0

    def get_profile_preferences(self, profile_id: int) -> AppPreferences | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT payload
                FROM preference_profiles
                WHERE id = ?
                """,
                (profile_id,),
            ).fetchone()

        if row is None:
            return None

        payload = json.loads(row["payload"])
        return self._preferences_from_values(payload)

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

    def _preferences_from_values(self, values: dict) -> AppPreferences:
        return AppPreferences(
            source_type=values.get("source_type", "local"),
            content_root=values.get("content_root", str(self.settings.content_root)),
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
            autosave_enabled=self._coerce_bool(values.get("autosave_enabled", False)),
            image_upload_mode=values.get("image_upload_mode", "same_dir"),
            image_upload_subdir=values.get("image_upload_subdir", "assets"),
            language=values.get("language", "pl"),
        )

    def _profile_from_row(self, row: sqlite3.Row) -> SavedPreferencesProfile:
        payload = json.loads(row["payload"])
        preferences = self._preferences_from_values(payload)
        return SavedPreferencesProfile(
            id=row["id"],
            name=row["name"],
            source_type=preferences.source_type,
            content_root=preferences.content_root,
            sftp_host=preferences.sftp_host,
            sftp_port=preferences.sftp_port,
            sftp_username=preferences.sftp_username,
            sftp_password=preferences.sftp_password,
            sftp_path=preferences.sftp_path,
            gdrive_folder_id=preferences.gdrive_folder_id,
            gdrive_credentials=preferences.gdrive_credentials,
            sort_mode=preferences.sort_mode,
            theme_mode=preferences.theme_mode,
            editor_font_size=preferences.editor_font_size,
            autosave_enabled=preferences.autosave_enabled,
            image_upload_mode=preferences.image_upload_mode,
            image_upload_subdir=preferences.image_upload_subdir,
            language=preferences.language,
        )

    def _coerce_bool(self, value: object) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "on"}
        return False
