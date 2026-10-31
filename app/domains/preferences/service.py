import sqlite3
from pathlib import Path

from app.core.config import Settings, get_settings
from app.domains.preferences.repository import PreferencesRepository
from app.domains.preferences.schemas import AppPreferences, SavedPreferencesProfile, SortMode, ThemeMode, SourceType, ImageUploadMode, Language


class PreferenceProfileNotFoundError(Exception):
    """Raised when a saved preferences profile does not exist."""


class PreferenceProfileConflictError(Exception):
    """Raised when a saved preferences profile name already exists."""


class PreferencesService:
    def __init__(
        self,
        settings: Settings | None = None,
        repository: PreferencesRepository | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.repository = repository or PreferencesRepository(self.settings)

    @staticmethod
    def _source_identity(p: AppPreferences) -> tuple:
        """What makes two settings point at the same notes."""
        if p.source_type == "sftp":
            return ("sftp", p.sftp_host, p.sftp_port, p.sftp_username, p.sftp_path)
        if p.source_type == "gdrive":
            return ("gdrive", p.gdrive_folder_id)
        return ("local", p.content_root)

    def _reconcile_active_profile(self, user_key: str | None) -> None:
        """Settings now write through to the active profile, so the active
        profile must actually be the one in effect. Before that, editing
        the source in Settings left a stale "active" marker behind; drop it
        rather than let the next save overwrite an unrelated profile."""
        active_id = self.repository.get_active_profile_id(user_key)
        if not active_id:
            return
        stored = self.repository.get_profile_preferences(active_id, user_key)
        current = self.repository.get_app_preferences(user_key)
        if stored is None or self._source_identity(stored) != self._source_identity(current):
            self.repository.set_active_profile_id(None, user_key)

    def _sync_active_profile(self, user_key: str | None) -> None:
        """Write the settings now in effect into the active profile."""
        active_id = self.repository.get_active_profile_id(user_key)
        if active_id:
            self.repository.update_profile_preferences(
                active_id, self.repository.get_app_preferences(user_key), user_key
            )

    def rename_profile(self, profile_id: int, name: str, user_key: str | None = None) -> SavedPreferencesProfile:
        try:
            profile = self.repository.rename_profile(profile_id, name.strip(), user_key)
        except sqlite3.IntegrityError as exc:
            raise PreferenceProfileConflictError("Saved settings profile name already exists.") from exc
        if profile is None:
            raise PreferenceProfileNotFoundError("Saved settings profile does not exist.")
        return profile

    def create_profile_from_current(self, name: str, user_key: str | None = None) -> SavedPreferencesProfile:
        """Turn the settings currently in effect into a profile and make it
        the active one (first save for installs that predate profiles)."""
        current = self.repository.get_app_preferences(user_key)
        try:
            profile = self.repository.create_profile(name.strip(), current, user_key)
        except sqlite3.IntegrityError as exc:
            raise PreferenceProfileConflictError("Saved settings profile name already exists.") from exc
        self.repository.set_active_profile_id(profile.id, user_key)
        return profile

    def get_preferences(self, user_key: str | None = None) -> AppPreferences:
        self._reconcile_active_profile(user_key)
        preferences = self.repository.get_app_preferences(user_key)
        if preferences.source_type == "local":
            try:
                content_root = self._ensure_local_content_root(preferences.content_root)
            except OSError:
                fallback_root = self._ensure_local_content_root(self.settings.content_root)
                # content_root is global storage, so this fixup is not
                # user-scoped.
                self.repository.update_app_preferences(content_root=str(fallback_root))
                return self.repository.get_app_preferences(user_key)
            if str(content_root) != preferences.content_root:
                self.repository.update_app_preferences(content_root=str(content_root))
                preferences = self.repository.get_app_preferences(user_key)
        return preferences

    def update_preferences(
        self,
        content_root: str,
        sort_mode: SortMode,
        theme_mode: ThemeMode,
        editor_font_size: int,
        source_type: SourceType = "local",
        sftp_host: str = "",
        sftp_port: int = 22,
        sftp_username: str = "",
        sftp_password: str = "",
        sftp_path: str = "/",
        gdrive_folder_id: str = "root",
        gdrive_credentials: str | None = None,
        autosave_enabled: bool = False,
        image_upload_mode: ImageUploadMode = "same_dir",
        image_upload_subdir: str = "assets",
        language: Language = "pl",
        user_key: str | None = None,
    ) -> AppPreferences:
        if source_type == "local":
            resolved_root = self._ensure_local_content_root(content_root)
            content_root = str(resolved_root)

        updated = self.repository.update_app_preferences(
            user_key=user_key,
            source_type=source_type,
            content_root=content_root,
            sftp_host=sftp_host,
            sftp_port=sftp_port,
            sftp_username=sftp_username,
            sftp_password=sftp_password,
            sftp_path=sftp_path,
            gdrive_folder_id=gdrive_folder_id,
            gdrive_credentials=gdrive_credentials,
            autosave_enabled=autosave_enabled,
            sort_mode=sort_mode,
            theme_mode=theme_mode,
            editor_font_size=editor_font_size,
            image_upload_mode=image_upload_mode,
            image_upload_subdir=image_upload_subdir,
            language=language,
        )
        # Settings and the active profile are one thing: whatever changes
        # here (Settings dialog, font +/-, …) is saved into that profile.
        self._sync_active_profile(user_key)
        return updated

    def list_profiles(self, user_key: str | None = None) -> list[SavedPreferencesProfile]:
        return self.repository.list_profiles(user_key)

    def create_profile(
        self,
        *,
        name: str,
        user_key: str | None = None,
        content_root: str,
        sort_mode: SortMode,
        theme_mode: ThemeMode,
        editor_font_size: int,
        source_type: SourceType = "local",
        sftp_host: str = "",
        sftp_port: int = 22,
        sftp_username: str = "",
        sftp_password: str = "",
        sftp_path: str = "/",
        gdrive_folder_id: str = "root",
        gdrive_credentials: str = "",
        autosave_enabled: bool = False,
        image_upload_mode: ImageUploadMode = "same_dir",
        image_upload_subdir: str = "assets",
        language: Language = "pl",
    ) -> SavedPreferencesProfile:
        profile_preferences = self._build_profile_preferences(
            content_root=content_root,
            sort_mode=sort_mode,
            theme_mode=theme_mode,
            editor_font_size=editor_font_size,
            source_type=source_type,
            sftp_host=sftp_host,
            sftp_port=sftp_port,
            sftp_username=sftp_username,
            sftp_password=sftp_password,
            sftp_path=sftp_path,
            gdrive_folder_id=gdrive_folder_id,
            gdrive_credentials=gdrive_credentials,
            autosave_enabled=autosave_enabled,
            image_upload_mode=image_upload_mode,
            image_upload_subdir=image_upload_subdir,
            language=language,
        )
        try:
            return self.repository.create_profile(name.strip(), profile_preferences, user_key)
        except sqlite3.IntegrityError as exc:
            raise PreferenceProfileConflictError("Saved settings profile name already exists.") from exc

    def update_profile(
        self,
        profile_id: int,
        *,
        name: str,
        user_key: str | None = None,
        content_root: str,
        sort_mode: SortMode,
        theme_mode: ThemeMode,
        editor_font_size: int,
        source_type: SourceType = "local",
        sftp_host: str = "",
        sftp_port: int = 22,
        sftp_username: str = "",
        sftp_password: str = "",
        sftp_path: str = "/",
        gdrive_folder_id: str = "root",
        gdrive_credentials: str = "",
        autosave_enabled: bool = False,
        image_upload_mode: ImageUploadMode = "same_dir",
        image_upload_subdir: str = "assets",
        language: Language = "pl",
    ) -> SavedPreferencesProfile:
        profile_preferences = self._build_profile_preferences(
            content_root=content_root,
            sort_mode=sort_mode,
            theme_mode=theme_mode,
            editor_font_size=editor_font_size,
            source_type=source_type,
            sftp_host=sftp_host,
            sftp_port=sftp_port,
            sftp_username=sftp_username,
            sftp_password=sftp_password,
            sftp_path=sftp_path,
            gdrive_folder_id=gdrive_folder_id,
            gdrive_credentials=gdrive_credentials,
            autosave_enabled=autosave_enabled,
            image_upload_mode=image_upload_mode,
            image_upload_subdir=image_upload_subdir,
            language=language,
        )
        try:
            profile = self.repository.update_profile(profile_id, name.strip(), profile_preferences, user_key)
        except sqlite3.IntegrityError as exc:
            raise PreferenceProfileConflictError("Saved settings profile name already exists.") from exc

        if profile is None:
            raise PreferenceProfileNotFoundError("Saved settings profile does not exist.")
        return profile

    def delete_profile(self, profile_id: int, user_key: str | None = None) -> None:
        deleted = self.repository.delete_profile(profile_id, user_key)
        if not deleted:
            raise PreferenceProfileNotFoundError("Saved settings profile does not exist.")
        if self.repository.get_active_profile_id(user_key) == profile_id:
            self.repository.set_active_profile_id(None, user_key)

    def reorder_profiles(self, ordered_ids: list[int], user_key: str | None = None) -> None:
        self.repository.reorder_profiles(ordered_ids, user_key)

    def apply_profile(self, profile_id: int, user_key: str | None = None) -> AppPreferences:
        profile_preferences = self.repository.get_profile_preferences(profile_id, user_key)
        if profile_preferences is None:
            raise PreferenceProfileNotFoundError("Saved settings profile does not exist.")

        # Mark as the active profile BEFORE running update_preferences so
        # that the returned AppPreferences carries the right active_profile_id.
        self.repository.set_active_profile_id(profile_id, user_key)

        # An empty password in update_preferences means "keep existing" —
        # which would carry the PREVIOUS profile's password over to this one.
        if profile_preferences.source_type == "sftp" and not profile_preferences.sftp_password:
            self.repository.clear_sftp_password()

        return self.update_preferences(
            user_key=user_key,
            content_root=profile_preferences.content_root,
            sort_mode=profile_preferences.sort_mode,
            theme_mode=profile_preferences.theme_mode,
            editor_font_size=profile_preferences.editor_font_size,
            source_type=profile_preferences.source_type,
            sftp_host=profile_preferences.sftp_host,
            sftp_port=profile_preferences.sftp_port,
            sftp_username=profile_preferences.sftp_username,
            sftp_password=profile_preferences.sftp_password,
            sftp_path=profile_preferences.sftp_path,
            gdrive_folder_id=profile_preferences.gdrive_folder_id,
            gdrive_credentials=profile_preferences.gdrive_credentials,
            autosave_enabled=profile_preferences.autosave_enabled,
            image_upload_mode=profile_preferences.image_upload_mode,
            image_upload_subdir=profile_preferences.image_upload_subdir,
            language=profile_preferences.language,
        )

    def _ensure_local_content_root(self, value: str | Path) -> Path:
        content_root = Path(value).expanduser().resolve()
        content_root.mkdir(parents=True, exist_ok=True)
        return content_root

    def _build_profile_preferences(
        self,
        *,
        content_root: str,
        sort_mode: SortMode,
        theme_mode: ThemeMode,
        editor_font_size: int,
        source_type: SourceType,
        sftp_host: str,
        sftp_port: int,
        sftp_username: str,
        sftp_password: str,
        sftp_path: str,
        gdrive_folder_id: str,
        gdrive_credentials: str,
        autosave_enabled: bool,
        image_upload_mode: ImageUploadMode,
        image_upload_subdir: str,
        language: Language = "pl",
    ) -> AppPreferences:
        normalized_content_root = content_root
        if source_type == "local":
            normalized_content_root = str(self._ensure_local_content_root(content_root))

        return AppPreferences(
            source_type=source_type,
            content_root=normalized_content_root,
            sftp_host=sftp_host,
            sftp_port=sftp_port,
            sftp_username=sftp_username,
            sftp_password=sftp_password,
            sftp_path=sftp_path,
            gdrive_folder_id=gdrive_folder_id,
            gdrive_credentials=gdrive_credentials,
            autosave_enabled=autosave_enabled,
            sort_mode=sort_mode,
            theme_mode=theme_mode,
            editor_font_size=editor_font_size,
            image_upload_mode=image_upload_mode,
            image_upload_subdir=image_upload_subdir,
            language=language,
        )
