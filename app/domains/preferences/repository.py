import json
import sqlite3
from contextlib import contextmanager

from app.core.config import Settings, get_settings
from app.domains.preferences.schemas import AppPreferences, SavedPreferencesProfile, SortMode, ThemeMode, SourceType, ImageUploadMode, Language  # noqa: F401


# Settings that are personal to each logged-in user. Everything else
# (source_type, content_root, sftp_*, gdrive_*) is the instance-wide
# storage config and stays shared — that's what makes a collaborative
# workspace point at one directory while each person keeps their own look.
_PERSONAL_KEYS = frozenset({
    "sort_mode",
    "theme_mode",
    "editor_font_size",
    "autosave_enabled",
    "image_upload_mode",
    "image_upload_subdir",
    "language",
    "compact_chrome",
    "active_profile_id",
})


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
            ("theme_mode", "webnote"),
            ("editor_font_size", "16"),
            ("autosave_enabled", "false"),
            ("image_upload_mode", "same_dir"),
            ("image_upload_subdir", "assets"),
            ("language", "pl"),
            ("compact_chrome", "true"),
            ("active_profile_id", ""),
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
            # Per-user overrides for the personal settings above. The
            # global app_settings row holds the instance defaults; a row
            # here shadows it for one user_key (the lowercased email).
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS user_settings (
                    user_key TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    PRIMARY KEY (user_key, key)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS preference_profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_key TEXT NOT NULL DEFAULT '',
                    name TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    sort_index INTEGER NOT NULL DEFAULT 0,
                    UNIQUE(user_key, name)
                )
                """
            )
            # Migration for older DBs that lack sort_index
            try:
                connection.execute("SELECT sort_index FROM preference_profiles LIMIT 1")
            except Exception:
                connection.execute(
                    "ALTER TABLE preference_profiles ADD COLUMN sort_index INTEGER NOT NULL DEFAULT 0"
                )
            # Migration: older DBs have a global UNIQUE(name) and no
            # user_key. Rebuild so names are unique per user, existing
            # profiles land in the shared/legacy bucket (user_key='').
            cols = [r[1] for r in connection.execute("PRAGMA table_info(preference_profiles)")]
            if cols and "user_key" not in cols:
                connection.execute("ALTER TABLE preference_profiles RENAME TO preference_profiles_old")
                connection.execute(
                    """
                    CREATE TABLE preference_profiles (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_key TEXT NOT NULL DEFAULT '',
                        name TEXT NOT NULL,
                        payload TEXT NOT NULL,
                        sort_index INTEGER NOT NULL DEFAULT 0,
                        UNIQUE(user_key, name)
                    )
                    """
                )
                connection.execute(
                    """
                    INSERT INTO preference_profiles(id, user_key, name, payload, sort_index)
                    SELECT id, '', name, payload, sort_index FROM preference_profiles_old
                    """
                )
                connection.execute("DROP TABLE preference_profiles_old")
            connection.executemany(
                "INSERT OR IGNORE INTO app_settings(key, value) VALUES(?, ?)",
                defaults,
            )

    def get_app_preferences(self, user_key: str | None = None) -> AppPreferences:
        with self._connect() as connection:
            rows = connection.execute("SELECT key, value FROM app_settings").fetchall()
            values = {row["key"]: row["value"] for row in rows}
            if user_key:
                urows = connection.execute(
                    "SELECT key, value FROM user_settings WHERE user_key = ?",
                    (user_key,),
                ).fetchall()
                for row in urows:
                    if row["key"] in _PERSONAL_KEYS:
                        values[row["key"]] = row["value"]
        return self._preferences_from_values(values)

    def update_app_preferences(
        self,
        *,
        user_key: str | None = None,
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
        compact_chrome: bool | None = None,
    ) -> AppPreferences:
        from app.core.crypto import encrypt_secret
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
        # Password handling: always encrypted at rest via Fernet. Empty
        # input means "keep existing" — never used to clear. Use
        # clear_sftp_password() if you need to wipe it explicitly.
        if sftp_password:
            updates.append(("sftp_password", encrypt_secret(sftp_password)))
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
        if compact_chrome is not None:
            updates.append(("compact_chrome", "true" if compact_chrome else "false"))

        # Split: when acting for a specific user, personal settings go to
        # that user's overlay; storage settings stay global. With no
        # user_key (startup seed, demo, save_sftp_credentials, tests),
        # everything writes globally as before.
        global_updates: list[tuple[str, str]] = []
        user_updates: list[tuple[str, str]] = []
        for key, val in updates:
            if user_key and key in _PERSONAL_KEYS:
                user_updates.append((key, val))
            else:
                global_updates.append((key, val))

        if global_updates or user_updates:
            with self._connect() as connection:
                if global_updates:
                    connection.executemany(
                        "INSERT OR REPLACE INTO app_settings(key, value) VALUES(?, ?)",
                        global_updates,
                    )
                if user_updates:
                    connection.executemany(
                        "INSERT OR REPLACE INTO user_settings(user_key, key, value) VALUES(?, ?, ?)",
                        [(user_key, k, v) for k, v in user_updates],
                    )

        return self.get_app_preferences(user_key)

    @staticmethod
    def _profile_scope(user_key: str | None) -> tuple[str, tuple]:
        """SQL fragment + params restricting profile rows to a user.

        A user sees their own profiles plus any legacy/shared rows
        (user_key=''). With no user_key (tests / back-compat) all rows
        are in scope."""
        if user_key:
            return "user_key IN (?, '')", (user_key,)
        return "1=1", ()

    def list_profiles(self, user_key: str | None = None) -> list[SavedPreferencesProfile]:
        scope, params = self._profile_scope(user_key)
        with self._connect() as connection:
            rows = connection.execute(
                f"""
                SELECT id, name, payload
                FROM preference_profiles
                WHERE {scope}
                ORDER BY sort_index ASC, name COLLATE NOCASE ASC
                """,
                params,
            ).fetchall()

        return [self._profile_from_row(row) for row in rows]

    def reorder_profiles(self, ordered_ids: list[int], user_key: str | None = None) -> None:
        """Apply a new sort_index to each id in the order given (scoped)."""
        if not ordered_ids:
            return
        scope, params = self._profile_scope(user_key)
        with self._connect() as connection:
            for index, profile_id in enumerate(ordered_ids):
                connection.execute(
                    f"UPDATE preference_profiles SET sort_index = ? WHERE id = ? AND {scope}",
                    (index, profile_id, *params),
                )

    def create_profile(self, name: str, preferences: AppPreferences, user_key: str | None = None) -> SavedPreferencesProfile:
        payload = json.dumps(self._encrypted_profile_payload(preferences), ensure_ascii=False)
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO preference_profiles(user_key, name, payload)
                VALUES(?, ?, ?)
                """,
                (user_key or "", name, payload),
            )
            row = connection.execute(
                "SELECT id, name, payload FROM preference_profiles WHERE id = ?",
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
        user_key: str | None = None,
    ) -> SavedPreferencesProfile | None:
        payload = json.dumps(self._encrypted_profile_payload(preferences), ensure_ascii=False)
        scope, params = self._profile_scope(user_key)
        with self._connect() as connection:
            cursor = connection.execute(
                f"""
                UPDATE preference_profiles
                SET name = ?, payload = ?
                WHERE id = ? AND {scope}
                """,
                (name, payload, profile_id, *params),
            )
            if cursor.rowcount == 0:
                return None
            row = connection.execute(
                "SELECT id, name, payload FROM preference_profiles WHERE id = ?",
                (profile_id,),
            ).fetchone()

        if row is None:
            return None
        return self._profile_from_row(row)

    def delete_profile(self, profile_id: int, user_key: str | None = None) -> bool:
        scope, params = self._profile_scope(user_key)
        with self._connect() as connection:
            cursor = connection.execute(
                f"DELETE FROM preference_profiles WHERE id = ? AND {scope}",
                (profile_id, *params),
            )
        return cursor.rowcount > 0

    def get_profile_preferences(self, profile_id: int, user_key: str | None = None) -> AppPreferences | None:
        scope, params = self._profile_scope(user_key)
        with self._connect() as connection:
            row = connection.execute(
                f"SELECT payload FROM preference_profiles WHERE id = ? AND {scope}",
                (profile_id, *params),
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
        from app.core.crypto import decrypt_secret
        stored_pass = values.get("sftp_password", "")
        decrypted_pass = decrypt_secret(stored_pass) if stored_pass else ""
        return AppPreferences(
            source_type=values.get("source_type", "local"),
            content_root=values.get("content_root", str(self.settings.content_root)),
            sftp_host=values.get("sftp_host", ""),
            sftp_port=int(values.get("sftp_port", "22")),
            sftp_username=values.get("sftp_username", ""),
            sftp_password=decrypted_pass,
            has_stored_sftp_password=bool(decrypted_pass),
            sftp_path=values.get("sftp_path", "/"),
            gdrive_folder_id=values.get("gdrive_folder_id", "root"),
            gdrive_credentials=values.get("gdrive_credentials", ""),
            sort_mode=values.get("sort_mode", "alphabetical"),
            theme_mode=values.get("theme_mode", "webnote"),
            editor_font_size=int(values.get("editor_font_size", "16")),
            autosave_enabled=self._coerce_bool(values.get("autosave_enabled", False)),
            image_upload_mode=values.get("image_upload_mode", "same_dir"),
            image_upload_subdir=values.get("image_upload_subdir", "assets"),
            language=values.get("language", "pl"),
            compact_chrome=self._coerce_bool(values.get("compact_chrome", True)),
            active_profile_id=self._parse_active_profile_id(values.get("active_profile_id", "")),
        )

    @staticmethod
    def _parse_active_profile_id(raw: object) -> int | None:
        try:
            value = int(str(raw))
            return value if value > 0 else None
        except (TypeError, ValueError):
            return None

    def get_active_profile_id(self, user_key: str | None = None) -> int | None:
        with self._connect() as connection:
            if user_key:
                row = connection.execute(
                    "SELECT value FROM user_settings WHERE user_key = ? AND key = 'active_profile_id'",
                    (user_key,),
                ).fetchone()
            else:
                row = connection.execute(
                    "SELECT value FROM app_settings WHERE key = 'active_profile_id'"
                ).fetchone()
        return self._parse_active_profile_id(row["value"] if row else "")

    def set_active_profile_id(self, profile_id: int | None, user_key: str | None = None) -> None:
        value = str(profile_id) if (isinstance(profile_id, int) and profile_id > 0) else ""
        with self._connect() as connection:
            if user_key:
                connection.execute(
                    """
                    INSERT INTO user_settings(user_key, key, value)
                    VALUES(?, 'active_profile_id', ?)
                    ON CONFLICT(user_key, key) DO UPDATE SET value = excluded.value
                    """,
                    (user_key, value),
                )
            else:
                connection.execute(
                    """
                    INSERT INTO app_settings(key, value) VALUES('active_profile_id', ?)
                    ON CONFLICT(key) DO UPDATE SET value = excluded.value
                    """,
                    (value,),
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

    def _encrypted_profile_payload(self, preferences: AppPreferences) -> dict:
        """Serialize profile preferences, encrypting any credentials so the
        DB never holds plaintext. ``_preferences_from_values`` reverses this
        on read via ``decrypt_secret``."""
        from app.core.crypto import encrypt_secret, is_encrypted

        data = preferences.model_dump()
        raw_password = data.get("sftp_password", "")
        if raw_password and not is_encrypted(raw_password):
            data["sftp_password"] = encrypt_secret(raw_password)
        return data

    def _coerce_bool(self, value: object) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "on"}
        return False
