from typing import Literal

from pydantic import BaseModel, Field


SortMode = Literal["alphabetical", "manual"]
ThemeMode = Literal["light", "dark", "obsidian", "noteeli", "webnote"]
SourceType = Literal["local", "sftp", "gdrive"]
ImageUploadMode = Literal["same_dir", "subdir"]
Language = Literal["pl", "en", "es", "de", "ru"]


class AppPreferences(BaseModel):
    source_type: SourceType = "local"
    content_root: str
    sftp_host: str = ""
    sftp_port: int = Field(default=22, ge=1, le=65535)
    sftp_username: str = ""
    sftp_password: str = ""
    has_stored_sftp_password: bool = False  # read-only, server-set
    sftp_path: str = "/"
    gdrive_folder_id: str = "root"
    gdrive_credentials: str = ""
    sort_mode: SortMode = "alphabetical"
    theme_mode: ThemeMode = "noteeli"
    editor_font_size: int = Field(default=16, ge=12, le=28)
    autosave_enabled: bool = False
    image_upload_mode: ImageUploadMode = "same_dir"
    image_upload_subdir: str = "assets"
    language: Language = "en"


class UpdatePreferencesRequest(BaseModel):
    source_type: SourceType = "local"
    content_root: str
    sftp_host: str = ""
    sftp_port: int = Field(default=22, ge=1, le=65535)
    sftp_username: str = ""
    sftp_password: str = ""              # empty = "keep existing"; non-empty = "replace"
    sftp_path: str = "/"
    gdrive_folder_id: str = "root"
    sort_mode: SortMode
    theme_mode: ThemeMode
    editor_font_size: int = Field(ge=12, le=28)
    autosave_enabled: bool = False
    image_upload_mode: ImageUploadMode = "same_dir"
    image_upload_subdir: str = "assets"
    language: Language = "en"


class SavedPreferencesProfile(BaseModel):
    id: int
    name: str
    source_type: SourceType = "local"
    content_root: str
    sftp_host: str = ""
    sftp_port: int = Field(default=22, ge=1, le=65535)
    sftp_username: str = ""
    sftp_password: str = ""
    sftp_path: str = "/"
    gdrive_folder_id: str = "root"
    gdrive_credentials: str = ""
    sort_mode: SortMode = "alphabetical"
    theme_mode: ThemeMode = "noteeli"
    editor_font_size: int = Field(default=16, ge=12, le=28)
    autosave_enabled: bool = False
    image_upload_mode: ImageUploadMode = "same_dir"
    image_upload_subdir: str = "assets"
    language: Language = "en"


class SavedPreferencesProfilesResponse(BaseModel):
    profiles: list[SavedPreferencesProfile]


class SavePreferencesProfileRequest(UpdatePreferencesRequest):
    name: str = Field(min_length=1, max_length=120)
    gdrive_credentials: str = ""


class ReorderItemsRequest(BaseModel):
    parent_path: str
    ordered_paths: list[str]
