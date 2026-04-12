from typing import Literal

from pydantic import BaseModel, Field


SortMode = Literal["alphabetical", "manual"]
ThemeMode = Literal["light", "dark"]


class AppPreferences(BaseModel):
    content_root: str
    sort_mode: SortMode = "alphabetical"
    theme_mode: ThemeMode = "light"
    editor_font_size: int = Field(default=16, ge=12, le=28)


class UpdatePreferencesRequest(BaseModel):
    content_root: str
    sort_mode: SortMode
    theme_mode: ThemeMode
    editor_font_size: int = Field(ge=12, le=28)


class ReorderItemsRequest(BaseModel):
    parent_path: str
    ordered_paths: list[str]
