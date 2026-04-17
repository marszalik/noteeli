from typing import Literal

from pydantic import BaseModel, Field


SortMode = Literal["alphabetical", "manual"]
ThemeMode = Literal["light", "dark", "obsidian"]
SourceType = Literal["local", "sftp", "gdrive"]
ImageUploadMode = Literal["same_dir", "subdir"]


class AppPreferences(BaseModel):
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
    theme_mode: ThemeMode = "light"
    editor_font_size: int = Field(default=16, ge=12, le=28)
    image_upload_mode: ImageUploadMode = "same_dir"
    image_upload_subdir: str = "assets"


class UpdatePreferencesRequest(BaseModel):
    source_type: SourceType = "local"
    content_root: str
    sftp_host: str = ""
    sftp_port: int = Field(default=22, ge=1, le=65535)
    sftp_username: str = ""
    sftp_password: str = ""
    sftp_path: str = "/"
    gdrive_folder_id: str = "root"
    sort_mode: SortMode
    theme_mode: ThemeMode
    editor_font_size: int = Field(ge=12, le=28)
    image_upload_mode: ImageUploadMode = "same_dir"
    image_upload_subdir: str = "assets"


class ReorderItemsRequest(BaseModel):
    parent_path: str
    ordered_paths: list[str]
