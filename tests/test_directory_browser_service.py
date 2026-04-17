from pathlib import Path

import pytest

from app.core.config import Settings
from app.domains.workspace.service import ItemAlreadyExistsError, InvalidPathError, WorkspaceService


def build_service(root: Path) -> WorkspaceService:
    settings = Settings(
        content_root=root,
        data_dir=root.parent / ".noteeli",
        session_secret="test-secret",
        google_client_id="",
        google_client_secret="",
    )
    return WorkspaceService(settings)


def test_create_browsed_directory_creates_and_opens_new_folder(tmp_path: Path):
    notes = tmp_path / "vault"
    notes.mkdir()
    service = build_service(notes)

    result = service.create_browsed_directory(str(notes), "Nowy Folder")

    assert result.current_path == str((notes / "Nowy Folder").resolve())
    assert (notes / "Nowy Folder").is_dir()


def test_create_browsed_directory_rejects_duplicate_name(tmp_path: Path):
    notes = tmp_path / "vault"
    notes.mkdir()
    (notes / "Istnieje").mkdir()
    service = build_service(notes)

    with pytest.raises(ItemAlreadyExistsError):
        service.create_browsed_directory(str(notes), "Istnieje")


def test_create_browsed_directory_rejects_invalid_name(tmp_path: Path):
    notes = tmp_path / "vault"
    notes.mkdir()
    service = build_service(notes)

    with pytest.raises(InvalidPathError):
        service.create_browsed_directory(str(notes), "../zle")
