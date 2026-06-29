import subprocess
from pathlib import Path

from app.core.config import Settings
from app.domains.workspace.service import WorkspaceService
from app.domains.git.service import GitService


def _settings(notes: Path, data_dir: Path) -> Settings:
    return Settings(
        content_root=notes,
        data_dir=data_dir,
        session_secret="x",
        google_client_id="",
        google_client_secret="",
    )


def test_db_inside_notes_is_hidden_from_tree(tmp_path):
    notes = tmp_path / "notes"
    notes.mkdir()
    (notes / "real.md").write_text("hi\n", encoding="utf-8")
    # data_dir == notes root → the real DB is created among the notes.
    svc = WorkspaceService(_settings(notes, notes))
    assert (notes / "noteeli.sqlite3").exists()  # repo init created it
    (notes / "noteeli.sqlite3-wal").write_text("", encoding="utf-8")  # sidecar

    names = {c.name for c in svc.build_tree().children}
    assert "real.md" in names
    assert "noteeli.sqlite3" not in names
    assert "noteeli.sqlite3-wal" not in names


def test_data_subdir_inside_notes_is_hidden_from_tree(tmp_path):
    notes = tmp_path / "notes"
    data = notes / ".noteeli"
    data.mkdir(parents=True)
    (notes / "real.md").write_text("hi\n", encoding="utf-8")
    svc = WorkspaceService(_settings(notes, data))
    names = {c.name for c in svc.build_tree().children}
    assert "real.md" in names
    assert ".noteeli" not in names


def _git(repo, *a):
    subprocess.run(["git", "-C", str(repo), *a], check=True, capture_output=True, text=True)


def test_db_excluded_from_git_status(tmp_path):
    notes = tmp_path / "notes"
    notes.mkdir()
    _git(notes, "init", "-q")
    _git(notes, "config", "user.email", "t@e.com")
    _git(notes, "config", "user.name", "T")
    (notes / "real.md").write_text("hi\n", encoding="utf-8")
    # data_dir == notes → real DB created in the notes dir
    GitService(_settings(notes, notes))  # init creates the DB
    assert (notes / "noteeli.sqlite3").exists()
    (notes / "noteeli.sqlite3-wal").write_text("wal", encoding="utf-8")

    status = GitService(_settings(notes, notes)).status()
    assert status.is_repo is True
    paths = {f.path for f in status.files}
    assert "real.md" in paths
    assert "noteeli.sqlite3" not in paths
    assert "noteeli.sqlite3-wal" not in paths
