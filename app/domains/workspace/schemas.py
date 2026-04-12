from typing import Literal

from pydantic import BaseModel, Field


class TreeNode(BaseModel):
    name: str
    path: str
    kind: Literal["directory", "file"]
    children: list["TreeNode"] = Field(default_factory=list)
    editable: bool = False
    symlink: bool = False


class FileDocument(BaseModel):
    name: str
    path: str
    editable: bool
    content: str
    message: str | None = None


class SaveFileRequest(BaseModel):
    path: str
    content: str


class CreateItemRequest(BaseModel):
    parent_path: str = ""
    name: str
    kind: Literal["directory", "file"]


class MoveItemRequest(BaseModel):
    source_path: str
    target_parent_path: str = ""


class DirectoryOption(BaseModel):
    name: str
    path: str


class DirectoryBrowserResponse(BaseModel):
    current_path: str
    parent_path: str | None = None
    directories: list[DirectoryOption] = Field(default_factory=list)


class CreatedItem(BaseModel):
    name: str
    path: str
    kind: Literal["directory", "file"]
    editable: bool = False


TreeNode.model_rebuild()
