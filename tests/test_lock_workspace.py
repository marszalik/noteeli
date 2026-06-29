from pathlib import Path

import pytest

from app.core.config import Settings
from app.domains.workspace.service import InvalidPathError, WorkspaceService


def _service(root: Path, *, locked: bool) -> WorkspaceService:
    settings = Settings(
        content_root=root,
        data_dir=root.parent / ".noteeli",
        session_secret="x",
        google_client_id="",
        google_client_secret="",
        lock_workspace=locked,
    )
    return WorkspaceService(settings)


def test_browse_confined_cannot_escape_root(tmp_path: Path):
    root = tmp_path / "vault"
    (root / "sub").mkdir(parents=True)
    svc = _service(root, locked=True)

    # At the root: no parent is exposed (can't walk up the disk).
    at_root = svc.browse_directories(str(root))
    assert at_root.parent_path is None

    # Asking for a path OUTSIDE the root snaps back to the root.
    escaped = svc.browse_directories(str(tmp_path))
    assert escaped.current_path == str(root.resolve())

    # A subdir inside the root still exposes a parent (stays inside).
    inside = svc.browse_directories(str(root / "sub"))
    assert inside.parent_path == str(root.resolve())


def test_browse_unconfined_can_walk_up(tmp_path: Path):
    root = tmp_path / "vault"
    root.mkdir()
    svc = _service(root, locked=False)
    at_root = svc.browse_directories(str(root))
    assert at_root.parent_path == str(tmp_path.resolve())


def test_locked_update_preferences_pins_storage(tmp_path: Path):
    root = tmp_path / "vault"
    root.mkdir()
    svc = _service(root, locked=True)

    before = svc.get_preferences()
    assert before.source_type == "local"
    assert before.content_root == str(root.resolve())

    # Try to repoint the workspace elsewhere + switch source — must be ignored.
    evil = tmp_path / "elsewhere"
    evil.mkdir()
    updated = svc.update_preferences(
        content_root=str(evil),
        sort_mode="alphabetical",
        theme_mode="dark",          # non-storage change should still apply
        editor_font_size=18,
        source_type="sftp",
        sftp_host="evil.example.com",
        sftp_path="/etc",
    )
    assert updated.source_type == "local"
    assert updated.content_root == str(root.resolve())
    assert updated.sftp_host == ""
    assert updated.theme_mode == "dark"      # allowed field changed


def test_locked_blocks_creating_dirs_outside(tmp_path: Path):
    root = tmp_path / "vault"
    root.mkdir()
    svc = _service(root, locked=True)
    with pytest.raises(InvalidPathError):
        svc.create_browsed_directory(str(tmp_path), "newdir")
