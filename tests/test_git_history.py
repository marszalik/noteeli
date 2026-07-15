"""File history, blame and word-diff (the backend of the blame/history UI).

Hermetic: every test builds a real git repo under tmp_path with commits by
different authors, then exercises GitService.file_log / blame /
commit_word_diff and the parsing of git's porcelain formats.
"""
import subprocess
from pathlib import Path

import pytest

from app.core.config import Settings
from app.domains.git.service import GitError, GitService


def _git(repo: Path, *args: str, author: tuple[str, str] | None = None) -> str:
    cmd = ["git", "-C", str(repo)]
    if author:
        name, email = author
        cmd += ["-c", f"user.name={name}", "-c", f"user.email={email}"]
    proc = subprocess.run([*cmd, *args], check=True, capture_output=True, text=True)
    return proc.stdout


ANNA = ("Anna", "anna@example.com")
BART = ("Bartek", "bartek@example.com")


def _repo_with_history(tmp_path: Path) -> tuple[Path, GitService]:
    repo = tmp_path / "notes"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "ambient@example.com")
    _git(repo, "config", "user.name", "Ambient")
    _git(repo, "config", "commit.gpgsign", "false")

    (repo / "note.md").write_text("line one\nline two\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "first version", author=ANNA)

    (repo / "note.md").write_text("line one\nline two changed\nline three\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "second version", author=BART)

    settings = Settings(
        content_root=repo,
        data_dir=tmp_path / ".noteeli",
        session_secret="test",
    )
    return repo, GitService(settings)


# ── file_log ────────────────────────────────────────────────────────


def test_file_log_lists_commits_newest_first_with_authors(tmp_path: Path):
    _, service = _repo_with_history(tmp_path)
    entries = service.file_log("note.md")
    assert [e.subject for e in entries] == ["second version", "first version"]
    assert entries[0].author_email == "bartek@example.com"
    assert entries[1].author_name == "Anna"
    assert all(len(e.sha) == 40 for e in entries)
    assert all(e.author_time > 0 for e in entries)


def test_file_log_only_includes_commits_touching_the_file(tmp_path: Path):
    repo, service = _repo_with_history(tmp_path)
    (repo / "other.md").write_text("unrelated\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "unrelated change", author=ANNA)
    subjects = [e.subject for e in service.file_log("note.md")]
    assert "unrelated change" not in subjects
    assert len(subjects) == 2


def test_file_log_follows_renames(tmp_path: Path):
    repo, service = _repo_with_history(tmp_path)
    _git(repo, "mv", "note.md", "renamed.md")
    _git(repo, "commit", "-qm", "rename it", author=BART)
    subjects = [e.subject for e in service.file_log("renamed.md")]
    assert subjects == ["rename it", "second version", "first version"]


def test_file_log_rejects_path_traversal(tmp_path: Path):
    _, service = _repo_with_history(tmp_path)
    with pytest.raises(GitError):
        service.file_log("../outside.md")


def test_file_log_limit_is_clamped(tmp_path: Path):
    _, service = _repo_with_history(tmp_path)
    assert len(service.file_log("note.md", limit=1)) == 1
    # Nonsense limits fall back into [1, 200] instead of erroring.
    assert len(service.file_log("note.md", limit=0)) == 1
    assert len(service.file_log("note.md", limit=99999)) == 2


# ── blame ───────────────────────────────────────────────────────────


def test_blame_attributes_lines_to_their_authors(tmp_path: Path):
    _, service = _repo_with_history(tmp_path)
    lines = service.blame("note.md")
    assert [l.content for l in lines] == ["line one", "line two changed", "line three"]
    assert lines[0].author_name == "Anna"          # untouched since v1
    assert lines[1].author_email == "bartek@example.com"
    assert lines[2].author_email == "bartek@example.com"
    assert lines[0].summary == "first version"
    assert all(l.committed for l in lines)
    assert all(l.author_time > 0 for l in lines)


def test_blame_marks_uncommitted_working_tree_lines(tmp_path: Path):
    repo, service = _repo_with_history(tmp_path)
    text = (repo / "note.md").read_text(encoding="utf-8")
    (repo / "note.md").write_text(text + "fresh uncommitted line\n", encoding="utf-8")
    lines = service.blame("note.md")
    assert lines[-1].content == "fresh uncommitted line"
    assert lines[-1].committed is False
    assert lines[-1].author_name == ""
    assert all(l.committed for l in lines[:-1])


def test_blame_rejects_path_traversal(tmp_path: Path):
    _, service = _repo_with_history(tmp_path)
    with pytest.raises(GitError):
        service.blame("/etc/passwd")


# ── commit word-diff ────────────────────────────────────────────────


def test_word_diff_shows_word_level_changes(tmp_path: Path):
    _, service = _repo_with_history(tmp_path)
    sha = service.file_log("note.md")[0].sha   # "second version"
    lines = service.commit_word_diff("note.md", sha)
    assert any(l.hunk for l in lines)
    flat = [(s.kind, s.text) for l in lines for s in l.segments]
    # "line two" → "line two changed": the shared words stay context and
    # only the new word is marked added — the point of word-diff for prose.
    assert ("added", "changed") in flat
    assert any(k == "context" and "line two" in t for k, t in flat)
    assert ("added", "line three") in flat


def test_word_diff_works_for_the_root_commit(tmp_path: Path):
    _, service = _repo_with_history(tmp_path)
    root_sha = service.file_log("note.md")[-1].sha   # "first version"
    lines = service.commit_word_diff("note.md", root_sha)
    flat = [(s.kind, s.text) for l in lines for s in l.segments]
    assert ("added", "line one") in flat
    assert ("added", "line two") in flat


def test_word_diff_rejects_malicious_revision(tmp_path: Path):
    _, service = _repo_with_history(tmp_path)
    for bad in ("HEAD", "main", "--exec=evil", "abc;rm -rf /", "abc..def", ""):
        with pytest.raises(GitError):
            service.commit_word_diff("note.md", bad)


def test_word_diff_accepts_short_sha(tmp_path: Path):
    _, service = _repo_with_history(tmp_path)
    sha = service.file_log("note.md")[0].sha
    lines = service.commit_word_diff("note.md", sha[:8])
    assert lines  # resolves and diffs fine


def test_word_diff_empty_for_commit_not_touching_file(tmp_path: Path):
    repo, service = _repo_with_history(tmp_path)
    (repo / "other.md").write_text("unrelated\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "unrelated", author=ANNA)
    sha = _git(repo, "rev-parse", "HEAD").strip()
    assert service.commit_word_diff("note.md", sha) == []
