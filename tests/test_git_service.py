import subprocess
from pathlib import Path

import pytest

from app.core.config import Settings
from app.domains.git.service import (
    GitNotConfiguredError,
    GitService,
    GitUnavailableError,
)


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True)


def _init_repo(repo: Path) -> None:
    repo.mkdir(parents=True, exist_ok=True)
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "t@example.com")
    _git(repo, "config", "user.name", "Test")
    _git(repo, "config", "commit.gpgsign", "false")


def _service(content_root: Path, *, demo: bool = False, source: str = "local") -> GitService:
    settings = Settings(
        content_root=content_root,
        data_dir=content_root.parent / ".noteeli",
        session_secret="test",
        google_client_id="",
        google_client_secret="",
        demo_mode=demo,
    )
    # Build a service whose preferences point at content_root with the
    # given source type, without touching a real preferences DB beyond
    # the default (which is local + this content_root).
    service = GitService(settings)
    return service


def test_non_repo_directory_reports_not_a_repo(tmp_path: Path):
    notes = tmp_path / "plain"
    notes.mkdir()
    service = _service(notes)
    status = service.status()
    assert status.available is True
    assert status.is_repo is False


def test_status_lists_untracked_and_modified(tmp_path: Path):
    repo = tmp_path / "notes"
    _init_repo(repo)
    (repo / "a.md").write_text("hello\n", encoding="utf-8")
    _git(repo, "add", "a.md")
    _git(repo, "commit", "-qm", "init")
    # modify tracked + add untracked
    (repo / "a.md").write_text("hello world\n", encoding="utf-8")
    (repo / "b.md").write_text("new\n", encoding="utf-8")

    service = _service(repo)
    status = service.status()
    assert status.is_repo is True
    assert status.clean is False
    by_path = {f.path: f.status for f in status.files}
    assert by_path.get("a.md") == "modified"
    assert by_path.get("b.md") == "untracked"


def test_commit_specific_path_only(tmp_path: Path):
    repo = tmp_path / "notes"
    _init_repo(repo)
    (repo / "keep.md").write_text("1\n", encoding="utf-8")
    (repo / "later.md").write_text("2\n", encoding="utf-8")

    service = _service(repo)
    result = service.commit("add keep", paths=["keep.md"])
    assert result.ok, result.message

    # later.md is still untracked after a path-scoped commit
    status = service.status()
    remaining = {f.path for f in status.files}
    assert "later.md" in remaining
    assert "keep.md" not in remaining


def test_commit_all_then_clean(tmp_path: Path):
    repo = tmp_path / "notes"
    _init_repo(repo)
    (repo / "a.md").write_text("x\n", encoding="utf-8")
    service = _service(repo)
    assert service.commit("everything").ok
    assert service.status().clean is True


def test_commit_nothing_to_commit(tmp_path: Path):
    repo = tmp_path / "notes"
    _init_repo(repo)
    (repo / "a.md").write_text("x\n", encoding="utf-8")
    service = _service(repo)
    service.commit("first")
    result = service.commit("again")
    assert result.ok is False
    assert "nothing to commit" in result.message.lower()


def test_commit_rejects_path_traversal(tmp_path: Path):
    repo = tmp_path / "notes"
    _init_repo(repo)
    (repo / "a.md").write_text("x\n", encoding="utf-8")
    service = _service(repo)
    with pytest.raises(Exception):
        service.commit("bad", paths=["../escape.md"])


def test_demo_mode_disables_git(tmp_path: Path):
    repo = tmp_path / "notes"
    _init_repo(repo)
    service = _service(repo, demo=True)
    assert service.available is False
    assert service.status().available is False
    with pytest.raises(GitUnavailableError):
        service.commit("x")


def test_branch_parsing_no_upstream(tmp_path: Path):
    repo = tmp_path / "notes"
    _init_repo(repo)
    (repo / "a.md").write_text("x\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "init")
    service = _service(repo)
    status = service.status()
    assert status.branch  # some branch name (main/master)
    assert status.upstream == ""
    assert status.ahead == 0 and status.behind == 0


# ── Router-level (TestClient) ───────────────────────────────────────


def test_git_api_status_commit_flow(tmp_path: Path):
    from fastapi.testclient import TestClient
    from app.main import create_app

    repo = tmp_path / "ws"
    _init_repo(repo)
    (repo / "n.md").write_text("hi\n", encoding="utf-8")

    import os
    env = {
        "NOTEELI_CONTENT_ROOT": str(repo),
        "NOTEELI_DATA_DIR": str(tmp_path / ".noteeli"),
        "NOTEELI_SESSION_SECRET": "x",
    }
    old = {k: os.environ.get(k) for k in env}
    os.environ.update(env)
    try:
        from app.core import config as cfg
        cfg.get_settings.cache_clear()
        client = TestClient(create_app(), base_url="http://127.0.0.1")

        status = client.get("/api/git/status").json()
        assert status["available"] is True and status["is_repo"] is True
        assert any(f["path"] == "n.md" for f in status["files"])

        commit = client.post("/api/git/commit", json={"message": "init", "paths": ["n.md"]}).json()
        assert commit["ok"] is True

        assert client.get("/api/git/status").json()["clean"] is True

        # Push with no remote → graceful failure, not a 500.
        push = client.post("/api/git/push")
        assert push.status_code == 200
        assert push.json()["ok"] is False
    finally:
        for k, v in old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        from app.core import config as cfg
        cfg.get_settings.cache_clear()


def test_dot_git_excluded_from_tree(tmp_path: Path):
    """The .git directory must never appear in the workspace tree."""
    from app.domains.workspace.service import WorkspaceService

    repo = tmp_path / "ws"
    _init_repo(repo)
    (repo / "note.md").write_text("hi\n", encoding="utf-8")

    settings = Settings(
        content_root=repo,
        data_dir=tmp_path / ".noteeli",
        session_secret="x",
        google_client_id="",
        google_client_secret="",
    )
    tree = WorkspaceService(settings).build_tree()
    top_names = {c.name for c in tree.children}
    assert ".git" not in top_names
    assert "note.md" in top_names


def test_commit_signed_with_author_identity(tmp_path: Path):
    """A commit carries the logged-in user as author + committer, not the
    repo's ambient git config."""
    repo = tmp_path / "ws"
    _init_repo(repo)
    # Ambient config is "Test <t@example.com>"; the commit should override.
    (repo / "n.md").write_text("hi\n", encoding="utf-8")

    service = _service(repo)
    result = service.commit(
        "collab note",
        author={"name": "Bob Collaborator", "email": "bob@gmail.com"},
    )
    assert result.ok, result.message

    out = subprocess.run(
        ["git", "-C", str(repo), "log", "-1", "--pretty=%an <%ae>|%cn <%ce>"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    author_part, committer_part = out.split("|")
    assert author_part == "Bob Collaborator <bob@gmail.com>"
    assert committer_part == "Bob Collaborator <bob@gmail.com>"


def test_commit_without_author_uses_ambient_config(tmp_path: Path):
    repo = tmp_path / "ws"
    _init_repo(repo)
    (repo / "n.md").write_text("hi\n", encoding="utf-8")
    service = _service(repo)
    assert service.commit("plain", author=None).ok
    an = subprocess.run(
        ["git", "-C", str(repo), "log", "-1", "--pretty=%ae"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    assert an == "t@example.com"
