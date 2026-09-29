"""The git menu's Pull / Push buttons when the branches have diverged.

Regression for the "colleague pushed from a second machine" case: the
workspace had one local commit, origin had one commit nobody pulled, and
both touched the SAME file on DIFFERENT lines. Push answered "Updates were
rejected … tip of your current branch is behind", Pull answered "Not
possible to fast-forward", and the git menu offered no way out. Both
buttons now replay local commits on top of the remote when the replay is
clean, and leave the repo untouched when it isn't.

Same fixtures as the auto-push suite: a bare origin plus two clones.
"""
from pathlib import Path

from tests.test_git_autopush import _configure, _git, _origin_subjects, _setup

_BASE = "Kody: 01, 02, 09\n\n| Godziny | Sobota | Niedziela |\n| --- | --- | --- |\n| 15:20 |  |  |\n"


def _diverge_on_different_lines(work: Path, other: Path) -> None:
    """Base file pushed; origin edits line 1, workspace edits the last line."""
    (work / "note.md").write_text(_BASE, encoding="utf-8")
    _git(work, "add", ".")
    _git(work, "commit", "-qm", "rozklad godzin")
    _git(work, "push", "-q")
    _git(other, "pull", "-q")

    (other / "note.md").write_text(_BASE.replace("01, 02, 09", "01, 02"), encoding="utf-8")
    _git(other, "add", ".")
    _git(other, "commit", "-qm", "poprawiny opis godzin")
    _git(other, "push", "-q")

    (work / "note.md").write_text(_BASE.replace("| 15:20 |  |  |", "| 15:20 |  | 08 |"), encoding="utf-8")
    _git(work, "add", ".")
    _git(work, "commit", "-qm", "Godziny dla 08-Governance")


def _diverge_on_same_line(work: Path, other: Path) -> None:
    (other / "note.md").write_text("wersja z laptopa\n", encoding="utf-8")
    _git(other, "add", ".")
    _git(other, "commit", "-qm", "remote edit")
    _git(other, "push", "-q")
    (work / "note.md").write_text("wersja z serwera\n", encoding="utf-8")
    _git(work, "add", ".")
    _git(work, "commit", "-qm", "local edit")


def _no_rebase_in_progress(work: Path) -> bool:
    return not (work / ".git" / "rebase-merge").exists() and not (work / ".git" / "rebase-apply").exists()


def test_push_replays_clean_divergence_in_same_file(tmp_path: Path):
    origin, work, other, _settings, service = _setup(tmp_path)
    _diverge_on_different_lines(work, other)

    result = service.push()

    assert result.ok is True
    assert result.output == "pushed"
    subjects = _origin_subjects(origin)
    assert subjects[0] == "Godziny dla 08-Governance"
    assert subjects[1] == "poprawiny opis godzin"
    status = service.status()
    assert status.ahead == 0 and status.behind == 0
    # Both edits survived in the merged file.
    merged = (work / "note.md").read_text(encoding="utf-8")
    assert "01, 02\n" in merged and "| 15:20 |  | 08 |" in merged


def test_pull_replays_clean_divergence_in_same_file(tmp_path: Path):
    origin, work, other, _settings, service = _setup(tmp_path)
    _diverge_on_different_lines(work, other)

    result = service.pull()

    assert result.ok is True
    assert "replayed" in result.message
    # Nothing pushed by Pull itself — we're now cleanly ahead by one.
    assert _origin_subjects(origin)[0] == "poprawiny opis godzin"
    status = service.status()
    assert status.ahead == 1 and status.behind == 0
    merged = (work / "note.md").read_text(encoding="utf-8")
    assert "01, 02\n" in merged and "| 15:20 |  | 08 |" in merged
    assert _git(work, "log", "-1", "--format=%s").strip() == "Godziny dla 08-Governance"


def test_pull_fast_forwards_when_not_diverged(tmp_path: Path):
    _origin, work, other, _settings, service = _setup(tmp_path)
    (other / "inny.md").write_text("z laptopa\n", encoding="utf-8")
    _git(other, "add", ".")
    _git(other, "commit", "-qm", "z laptopa")
    _git(other, "push", "-q")

    result = service.pull()

    assert result.ok is True and result.message == "Pulled."
    assert (work / "inny.md").exists()
    status = service.status()
    assert status.ahead == 0 and status.behind == 0


def test_pull_conflict_aborts_and_leaves_repo_untouched(tmp_path: Path):
    origin, work, other, _settings, service = _setup(tmp_path)
    _diverge_on_same_line(work, other)

    result = service.pull()

    assert result.ok is False
    assert "conflict" in result.message.lower()
    assert _no_rebase_in_progress(work)
    assert _git(work, "log", "-1", "--format=%s").strip() == "local edit"
    assert (work / "note.md").read_text(encoding="utf-8") == "wersja z serwera\n"
    assert _origin_subjects(origin)[0] == "remote edit"
    status = service.status()
    assert status.ahead == 1 and status.behind == 1


def test_push_conflict_parks_and_leaves_repo_untouched(tmp_path: Path):
    origin, work, other, _settings, service = _setup(tmp_path)
    _diverge_on_same_line(work, other)

    result = service.push()

    assert result.ok is False and result.output == "parked"
    assert _no_rebase_in_progress(work)
    assert _git(work, "log", "-1", "--format=%s").strip() == "local edit"
    assert _origin_subjects(origin)[0] == "remote edit"


def test_pull_rebase_keeps_uncommitted_edits(tmp_path: Path):
    """Autostash: an unsaved-to-git edit in another file must not block the
    replay, and must still be there afterwards."""
    _origin, work, other, _settings, service = _setup(tmp_path)
    _diverge_on_different_lines(work, other)
    (work / "draft.md").write_text("szkic\n", encoding="utf-8")
    _git(work, "add", "draft.md")
    _git(work, "commit", "-qm", "draft")  # tracked, so the next write is an unstaged change
    (work / "draft.md").write_text("szkic po edycji\n", encoding="utf-8")

    result = service.pull()

    assert result.ok is True
    assert (work / "draft.md").read_text(encoding="utf-8") == "szkic po edycji\n"
    assert service.status().behind == 0


def test_pull_without_upstream_reports_git_error(tmp_path: Path):
    repo = tmp_path / "solo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _configure(repo)
    (repo / "note.md").write_text("solo\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "initial")
    from app.core.config import Settings
    from app.domains.git.service import GitService

    service = GitService(Settings(content_root=repo, data_dir=tmp_path / ".noteeli", session_secret="test"))
    result = service.pull()
    assert result.ok is False
    assert "conflict" not in result.message.lower()
