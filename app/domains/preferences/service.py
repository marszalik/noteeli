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

    def get_preferences(self) -> AppPreferences:
        preferences = self.repository.get_app_preferences()
        if preferences.source_type == "local":
            try:
                content_root = self._ensure_local_content_root(preferences.content_root)
            except OSError:
                fallback_root = self._ensure_local_content_root(self.settings.content_root)
                preferences = self.repository.update_app_preferences(
                    content_root=str(fallback_root),
                )
                return preferences
            if str(content_root) != preferences.content_root:
                preferences = self.repository.update_app_preferences(
                    content_root=str(content_root),
                )
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
        image_upload_mode: ImageUploadMode = "same_dir",
        image_upload_subdir: str = "assets",
        language: Language = "pl",
    ) -> AppPreferences:
        if source_type == "local":
            resolved_root = self._ensure_local_content_root(content_root)
            content_root = str(resolved_root)

        return self.repository.update_app_preferences(
            source_type=source_type,
            content_root=content_root,
            sftp_host=sftp_host,
            sftp_port=sftp_port,
            sftp_username=sftp_username,
            sftp_password=sftp_password,
            sftp_path=sftp_path,
            gdrive_folder_id=gdrive_folder_id,
            gdrive_credentials=gdrive_credentials,
            sort_mode=sort_mode,
            theme_mode=theme_mode,
            editor_font_size=editor_font_size,
            image_upload_mode=image_upload_mode,
            image_upload_subdir=image_upload_subdir,
            language=language,
        )

    def list_profiles(self) -> list[SavedPreferencesProfile]:
        return self.repository.list_profiles()

    def create_profile(
        self,
        *,
        name: str,
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
            image_upload_mode=image_upload_mode,
            image_upload_subdir=image_upload_subdir,
            language=language,
        )
        try:
            return self.repository.create_profile(name.strip(), profile_preferences)
        except sqlite3.IntegrityError as exc:
            raise PreferenceProfileConflictError("Saved settings profile name already exists.") from exc

    def update_profile(
        self,
        profile_id: int,
        *,
        name: str,
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
            image_upload_mode=image_upload_mode,
            image_upload_subdir=image_upload_subdir,
            language=language,
        )
        try:
            profile = self.repository.update_profile(profile_id, name.strip(), profile_preferences)
        except sqlite3.IntegrityError as exc:
            raise PreferenceProfileConflictError("Saved settings profile name already exists.") from exc

        if profile is None:
            raise PreferenceProfileNotFoundError("Saved settings profile does not exist.")
        return profile

    def delete_profile(self, profile_id: int) -> None:
        deleted = self.repository.delete_profile(profile_id)
        if not deleted:
            raise PreferenceProfileNotFoundError("Saved settings profile does not exist.")

    def apply_profile(self, profile_id: int) -> AppPreferences:
        profile_preferences = self.repository.get_profile_preferences(profile_id)
        if profile_preferences is None:
            raise PreferenceProfileNotFoundError("Saved settings profile does not exist.")

        return self.update_preferences(
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
            sort_mode=sort_mode,
            theme_mode=theme_mode,
            editor_font_size=editor_font_size,
            image_upload_mode=image_upload_mode,
            image_upload_subdir=image_upload_subdir,
            language=language,
        )
