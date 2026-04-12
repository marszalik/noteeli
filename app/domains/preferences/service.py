from pathlib import Path

from app.core.config import Settings, get_settings
from app.domains.preferences.repository import PreferencesRepository
from app.domains.preferences.schemas import AppPreferences, SortMode, ThemeMode


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
        content_root = Path(preferences.content_root).expanduser().resolve()
        content_root.mkdir(parents=True, exist_ok=True)
        if str(content_root) != preferences.content_root:
            preferences = self.repository.update_app_preferences(
                content_root=str(content_root),
                sort_mode=preferences.sort_mode,
                theme_mode=preferences.theme_mode,
                editor_font_size=preferences.editor_font_size,
            )
        return preferences

    def update_preferences(
        self,
        content_root: str,
        sort_mode: SortMode,
        theme_mode: ThemeMode,
        editor_font_size: int,
    ) -> AppPreferences:
        resolved_root = Path(content_root).expanduser().resolve()
        resolved_root.mkdir(parents=True, exist_ok=True)
        return self.repository.update_app_preferences(
            content_root=str(resolved_root),
            sort_mode=sort_mode,
            theme_mode=theme_mode,
            editor_font_size=editor_font_size,
        )
