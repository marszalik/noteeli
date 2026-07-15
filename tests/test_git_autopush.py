"""Auto-push after checkpoints (NOTEELI_GIT_AUTOCOMMIT_PUSH).

Safety contract under test: plain push when possible; clean divergence is
replayed with pull --rebase; a content conflict parks the sync WITHOUT
losing local commits or leaving a half-done rebase behind. Every test
runs against a real bare origin plus two clones (the workspace and a
"someone else" writer).
"""
import subprocess
from pathlib import Path

from app.core.config import Settings
from app.domains.git.checkpoint import CheckpointTracker
from app.domains.git.service import GitService


def _git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args], check=True, capture_output=True, text=True
    )
    return proc.stdout


def _configure(repo: Path) -> None:
    _git(repo, "config", "user.email", "clone@example.com")
    _git(repo, "config", "user.name", "Clone")
    _git(repo, "config", "commit.gpgsign", "false")


def _setup(tmp_path: Path):
    """bare origin + workspace clone (with one pushed commit) + other clone."""
    origin = tmp_path / "origin.git"
    origin.mkdir()
    _git(origin, "init", "-q", "--bare")

    work = tmp_path / "work"
    subprocess.run(
        ["git", "clone", "-q", str(origin), str(work)], check=True, capture_output=True
    )
    _configure(work)
    (work / "note.md").write_text("wspólna linia\n", encoding="utf-8")
    _git(work, "add", ".")
    _git(work, "commit", "-qm", "initial")
    _git(work, "push", "-q", "-u", "origin", "HEAD")

    other = tmp_path / "other"
    subprocess.run(
        ["git", "clone", "-q", str(origin), str(other)], check=True, capture_output=True
    )
    _configure(other)

    settings = Settings(
        content_root=work,
        data_dir=tmp_path / ".noteeli",
        session_secret="test",
        git_autocommit=True,
        git_autocommit_push=True,
        git_autocommit_idle_seconds=0,
    )
    return origin, work, other, settings, GitService(settings)


def _origin_subjects(origin: Path) -> list[str]:
    return _git(origin, "log", "--format=%s").splitlines()


ANNA = {"name": "Anna", "email": "anna@example.com"}


def _flush_checkpoint(work: Path, settings, service, filename="note.md", text="edycja Anny\n"):
    (work / filename).write_text(text, encoding="utf-8")
    tracker = CheckpointTracker(clock=lambda: 10_000.0)
    tracker.record_save(filename, ANNA)
    return tracker.flush_due(settings, git_service=service)


def test_checkpoint_is_pushed_to_origin(tmp_path: Path):
    origin, work, _other, settings, service = _setup(tmp_path)
    results = _flush_checkpoint(work, settings, service)
    assert [r.ok for r in results] == [True]
    assert _origin_subjects(origin)[0] == "Checkpoint: note.md"
    status = service.status()
    assert status.ahead == 0 and status.behind == 0


def test_clean_divergence_is_rebased_and_pushed(tmp_path: Path):
    origin, work, other, settings, service = _setup(tmp_path)
    # Someone else pushes a NON-conflicting change (different file).
    (other / "inny.md").write_text("z laptopa\n", encoding="utf-8")
    _git(other, "add", ".")
    _git(other, "commit", "-qm", "z laptopa")
    _git(other, "push", "-q")

    _flush_checkpoint(work, settings, service)

    subjects = _origin_subjects(origin)
    assert subjects[0] == "Checkpoint: note.md"   # replayed on top
    assert "z laptopa" in subjects
    status = service.status()
    assert status.ahead == 0 and status.behind == 0
    # The rebase preserved checkpoint authorship.
    assert _git(origin, "log", "-1", "--format=%ae").strip() == "anna@example.com"


def test_content_conflict_parks_without_losing_anything(tmp_path: Path):
    origin, work, other, settings, service = _setup(tmp_path)
    # Someone else pushes a CONFLICTING change to the same line.
    (other / "note.md").write_text("konfliktowa wersja z laptopa\n", encoding="utf-8")
    _git(other, "add", ".")
    _git(other, "commit", "-qm", "konflikt z laptopa")
    _git(other, "push", "-q")

    _flush_checkpoint(work, settings, service, text="edycja Anny w tej samej linii\n")

    # Origin was NOT force-overwritten.
    assert _origin_subjects(origin)[0] == "konflikt z laptopa"
    # No half-done rebase left behind; the repo is operational.
    assert not (work / ".git" / "rebase-merge").exists()
    assert not (work / ".git" / "rebase-apply").exists()
    # Local checkpoint commit survived, working tree content intact.
    assert _git(work, "log", "-1", "--format=%s").strip() == "Checkpoint: note.md"
    assert (work / "note.md").read_text(encoding="utf-8") == "edycja Anny w tej samej linii\n"
    # Parked state is visible: we're ahead AND behind.
    status = service.status()
    assert status.ahead >= 1 and status.behind >= 1


def test_sync_push_reports_parked_outcome(tmp_path: Path):
    _origin, work, other, settings, service = _setup(tmp_path)
    (other / "note.md").write_text("A\n", encoding="utf-8")
    _git(other, "add", ".")
    _git(other, "commit", "-qm", "remote edit")
    _git(other, "push", "-q")
    (work / "note.md").write_text("B\n", encoding="utf-8")
    _git(work, "add", ".")
    _git(work, "commit", "-qm", "local edit")

    result = service.sync_push()
    assert result.ok is False
    assert result.output == "parked"


def test_no_remote_is_a_silent_no_op(tmp_path: Path):
    repo = tmp_path / "solo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _configure(repo)
    (repo / "note.md").write_text("solo\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "initial")

    settings = Settings(
        content_root=repo,
        data_dir=tmp_path / ".noteeli",
        session_secret="test",
        git_autocommit=True,
        git_autocommit_push=True,
        git_autocommit_idle_seconds=0,
    )
    service = GitService(settings)
    results = _flush_checkpoint(repo, settings, service)
    # The commit itself succeeds; the missing remote never breaks the flush.
    assert [r.ok for r in results] == [True]
    result = service.sync_push()
    assert result.ok is False and result.output == "no_remote"


def test_autopush_disabled_leaves_commits_local(tmp_path: Path):
    origin, work, _other, settings, service = _setup(tmp_path)
    settings = settings.model_copy(update={"git_autocommit_push": False})
    _flush_checkpoint(work, settings, service)
    assert _origin_subjects(origin)[0] == "initial"   # nothing pushed
    assert service.status().ahead == 1
