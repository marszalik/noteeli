"""Tests for the SFTP storage backend.

We don't have a real SFTP server in CI, so paramiko is monkeypatched
with a `FakeSSHClient` whose `open_sftp()` returns a `FakeSFTP` that
delegates every operation to a real `tmp_path` directory. The backend
is exercised end to end (its actual code paths run, including stat
masks, recursive deletion, and the connection-cache liveness check),
but the network layer is replaced by a filesystem fake.

The fake implements only the slice of the paramiko `SFTPClient` API
that `SFTPStorageBackend` actually uses:

  stat, listdir_attr, open(path, "rb"|"wb"), mkdir, remove, rmdir,
  rename, close

If the production code starts using a new method, an AttributeError
will surface here — that's a deliberate canary, not a flaw.
"""
from __future__ import annotations

import os
import stat as _stat
from pathlib import Path

import pytest

from app.domains.workspace.storage import (
    SFTPStorageBackend,
    build_backend,
    session_sftp_password,
)


# ── Fakes ───────────────────────────────────────────────────────


class _StatResult:
    def __init__(self, st_mode: int) -> None:
        self.st_mode = st_mode


class _Attr:
    def __init__(self, filename: str, st_mode: int) -> None:
        self.filename = filename
        self.st_mode = st_mode


class FakeSFTP:
    def __init__(self, root: Path) -> None:
        self._root = root

    def _to_local(self, path: str) -> Path:
        # The backend builds absolute remote paths like "/remote/notes/foo.md".
        # We rebase them under the test's tmp_path so the fake operates on
        # a real filesystem.
        return self._root / path.lstrip("/")

    def stat(self, path: str) -> _StatResult:
        local = self._to_local(path)
        if not local.exists():
            raise FileNotFoundError(path)
        return _StatResult(local.stat().st_mode)

    def listdir_attr(self, path: str) -> list[_Attr]:
        local = self._to_local(path)
        return [
            _Attr(child.name, child.stat().st_mode)
            for child in sorted(local.iterdir())
        ]

    def open(self, path: str, mode: str):
        return open(self._to_local(path), mode)

    def mkdir(self, path: str) -> None:
        self._to_local(path).mkdir()

    def remove(self, path: str) -> None:
        self._to_local(path).unlink()

    def rmdir(self, path: str) -> None:
        self._to_local(path).rmdir()

    def rename(self, src: str, dst: str) -> None:
        self._to_local(src).rename(self._to_local(dst))

    def close(self) -> None:  # paramiko sftp clients have close()
        pass


class FakeSSHClient:
    def __init__(self, root: Path) -> None:
        self._root = root
        self.connected = False

    def set_missing_host_key_policy(self, *_args, **_kwargs) -> None:
        pass

    def connect(self, **_kwargs) -> None:
        self.connected = True

    def open_sftp(self) -> FakeSFTP:
        return FakeSFTP(self._root)

    def close(self) -> None:
        self.connected = False


@pytest.fixture
def fake_sftp(tmp_path: Path, monkeypatch):
    """Wires paramiko to a filesystem-backed fake rooted at tmp_path."""
    import paramiko

    monkeypatch.setattr(paramiko, "SSHClient", lambda: FakeSSHClient(tmp_path))
    monkeypatch.setattr(paramiko, "AutoAddPolicy", lambda: None)
    return tmp_path


def _build(remote_root: str = "/notes") -> SFTPStorageBackend:
    return SFTPStorageBackend(
        host="example.com",
        port=22,
        username="alice",
        password="hunter2",
        remote_path=remote_root,
    )


# ── Existence / type checks ─────────────────────────────────────


def test_exists_true_for_existing_file(fake_sftp: Path):
    (fake_sftp / "notes").mkdir()
    (fake_sftp / "notes" / "foo.md").write_text("hi", encoding="utf-8")

    backend = _build()
    assert backend.exists("foo.md") is True


def test_exists_false_for_missing_file(fake_sftp: Path):
    (fake_sftp / "notes").mkdir()
    backend = _build()
    assert backend.exists("missing.md") is False


def test_is_file_and_is_dir(fake_sftp: Path):
    notes = fake_sftp / "notes"
    notes.mkdir()
    (notes / "doc.md").write_text("x", encoding="utf-8")
    (notes / "sub").mkdir()

    backend = _build()
    assert backend.is_file("doc.md") is True
    assert backend.is_file("sub") is False
    assert backend.is_dir("sub") is True
    assert backend.is_dir("doc.md") is False
    # missing path returns False, not an exception
    assert backend.is_file("nope") is False
    assert backend.is_dir("nope") is False


# ── Read / write round-trip ─────────────────────────────────────


def test_read_text_round_trip(fake_sftp: Path):
    (fake_sftp / "notes").mkdir()
    (fake_sftp / "notes" / "story.md").write_text(
        "# Title\n\nAla ma kota — UTF-8 ✓", encoding="utf-8"
    )

    backend = _build()
    assert backend.read_text("story.md").startswith("# Title")
    assert "kota" in backend.read_text("story.md")


def test_write_text_creates_file(fake_sftp: Path):
    (fake_sftp / "notes").mkdir()

    backend = _build()
    backend.write_text("fresh.md", "hello sftp")
    assert (fake_sftp / "notes" / "fresh.md").read_text(encoding="utf-8") == "hello sftp"


def test_write_bytes_round_trip(fake_sftp: Path):
    (fake_sftp / "notes").mkdir()

    backend = _build()
    blob = bytes(range(256))
    backend.write_bytes("blob.bin", blob)
    assert backend.read_bytes("blob.bin") == blob


# ── Listing / browsing ───────────────────────────────────────────


def test_list_children_returns_names_and_directory_flag(fake_sftp: Path):
    notes = fake_sftp / "notes"
    notes.mkdir()
    (notes / "alpha").mkdir()
    (notes / "beta.md").write_text("b", encoding="utf-8")
    (notes / "zulu.md").write_text("z", encoding="utf-8")

    backend = _build()
    entries = backend.list_children("")

    by_name = {e.name: e for e in entries}
    assert "alpha" in by_name and by_name["alpha"].is_dir is True
    assert "beta.md" in by_name and by_name["beta.md"].is_dir is False
    assert "zulu.md" in by_name


def test_browse_dirs_returns_only_directories(fake_sftp: Path):
    notes = fake_sftp / "notes"
    nested = notes / "projects"
    nested.mkdir(parents=True)
    (notes / "scratch").mkdir()
    (notes / "todo.md").write_text("x", encoding="utf-8")

    backend = _build()
    result = backend.browse_dirs("/notes")

    names = [name for name, _path in result.directories]
    assert "projects" in names
    assert "scratch" in names
    # files are not listed in the directory browser
    assert "todo.md" not in names


def test_browse_dirs_falls_back_to_root_for_file_path(fake_sftp: Path):
    """Mirrors LocalStorageBackend behaviour — a non-directory input
    falls back to the configured root rather than raising."""
    notes = fake_sftp / "notes"
    notes.mkdir()
    (notes / "doc.md").write_text("x", encoding="utf-8")

    backend = _build()
    # Passing a file path: the resolver should drop back to /notes (root).
    result = backend.browse_dirs("/notes/doc.md")

    assert result.current_path == "/notes"


# ── Mutations ───────────────────────────────────────────────────


def test_create_dir_and_create_file(fake_sftp: Path):
    (fake_sftp / "notes").mkdir()

    backend = _build()
    backend.create_dir("new-folder")
    backend.create_file("note-stub.md")

    assert (fake_sftp / "notes" / "new-folder").is_dir()
    assert (fake_sftp / "notes" / "note-stub.md").is_file()


def test_rename_moves_file(fake_sftp: Path):
    notes = fake_sftp / "notes"
    notes.mkdir()
    (notes / "before.md").write_text("body", encoding="utf-8")

    backend = _build()
    backend.rename("before.md", "after.md")

    assert not (notes / "before.md").exists()
    assert (notes / "after.md").read_text(encoding="utf-8") == "body"


def test_delete_removes_file(fake_sftp: Path):
    notes = fake_sftp / "notes"
    notes.mkdir()
    (notes / "scrap.md").write_text("x", encoding="utf-8")

    backend = _build()
    backend.delete("scrap.md")
    assert not (notes / "scrap.md").exists()


def test_delete_removes_directory_recursively(fake_sftp: Path):
    notes = fake_sftp / "notes"
    folder = notes / "trash"
    nested = folder / "deep"
    nested.mkdir(parents=True)
    (folder / "a.md").write_text("a", encoding="utf-8")
    (nested / "b.md").write_text("b", encoding="utf-8")

    backend = _build()
    backend.delete("trash")

    assert not folder.exists()


# ── Recursive walk used by the ZIP downloader ──────────────────


def test_rglob_files_walks_into_subdirectories(fake_sftp: Path):
    notes = fake_sftp / "notes"
    sub = notes / "sub"
    sub.mkdir(parents=True)
    (notes / "a.md").write_text("", encoding="utf-8")
    (sub / "b.md").write_text("", encoding="utf-8")
    (sub / "c.md").write_text("", encoding="utf-8")

    backend = _build()
    paths = backend.rglob_files("")

    assert sorted(paths) == ["a.md", "sub/b.md", "sub/c.md"]


# ── Display string ──────────────────────────────────────────────


def test_root_display_renders_sftp_url(fake_sftp: Path):
    backend = _build("/srv/notes")
    assert backend.root_display == "sftp://alice@example.com/srv/notes"


# ── build_backend session-password fallback ─────────────────────


class _Prefs:
    """Bare-minimum prefs stand-in for build_backend()."""
    source_type = "sftp"
    sftp_host = "example.com"
    sftp_port = 22
    sftp_username = "alice"
    sftp_password = ""
    sftp_path = "/srv/notes"


def test_build_backend_uses_session_password_when_db_password_empty():
    # User opted out of "Remember password" — sftp_password in DB is "".
    # The middleware sets a session-scoped password; build_backend should
    # pass it through to the new SFTPStorageBackend instance.
    token = session_sftp_password.set("from-session")
    try:
        backend = build_backend(_Prefs())
        assert isinstance(backend, SFTPStorageBackend)
        assert backend._password == "from-session"
    finally:
        session_sftp_password.reset(token)


def test_build_backend_prefers_db_password_over_session():
    # If both are present, the persisted (Remember=on) password wins.
    class P(_Prefs):
        sftp_password = "from-db"

    token = session_sftp_password.set("from-session")
    try:
        backend = build_backend(P())
        assert backend._password == "from-db"
    finally:
        session_sftp_password.reset(token)
