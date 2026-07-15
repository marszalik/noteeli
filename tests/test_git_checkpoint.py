"""Silent checkpoint commits (idle-debounced git auto-commit).

The tracker approximates "end of an editing session" with an idle window:
saves queue a path, and a flush commits paths whose last save is older
than `git_autocommit_idle_seconds`, signed by the last saver. Tests use
an injected fake clock — no sleeping.
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


def _init_repo(repo: Path) -> None:
    repo.mkdir(parents=True, exist_ok=True)
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "ambient@example.com")
    _git(repo, "config", "user.name", "Ambient")
    _git(repo, "config", "commit.gpgsign", "false")
    (repo / "note.md").write_text("hello\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "initial")


def _settings(content_root: Path, *, enabled: bool = True, idle: int = 300, demo: bool = False) -> Settings:
    return Settings(
        content_root=content_root,
        data_dir=content_root.parent / ".noteeli",
        session_secret="test",
        git_autocommit=enabled,
        git_autocommit_idle_seconds=idle,
        demo_mode=demo,
    )


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def _setup(tmp_path: Path, **settings_kwargs):
    repo = tmp_path / "notes"
    _init_repo(repo)
    settings = _settings(repo, **settings_kwargs)
    clock = FakeClock()
    tracker = CheckpointTracker(clock=clock)
    service = GitService(settings)
    return repo, settings, clock, tracker, service


ANNA = {"name": "Anna Prowadząca", "email": "anna@example.com"}
BART = {"name": "Bartek", "email": "bartek@example.com"}


def _log(repo: Path, n: int = 5) -> list[str]:
    out = _git(repo, "log", f"-{n}", "--format=%ae|%an|%s")
    return [line for line in out.splitlines() if line]


def test_no_checkpoint_before_idle_window(tmp_path: Path):
    repo, settings, clock, tracker, service = _setup(tmp_path)
    (repo / "note.md").write_text("edited\n", encoding="utf-8")
    tracker.record_save("note.md", ANNA)
    clock.advance(299)
    assert tracker.flush_due(settings, git_service=service) == []
    assert tracker.pending_paths() == ["note.md"]


def test_checkpoint_commits_after_idle_signed_by_last_saver(tmp_path: Path):
    repo, settings, clock, tracker, service = _setup(tmp_path)
    (repo / "note.md").write_text("edited\n", encoding="utf-8")
    tracker.record_save("note.md", ANNA)
    clock.advance(301)
    results = tracker.flush_due(settings, git_service=service)
    assert [r.ok for r in results] == [True]
    assert _log(repo)[0] == "anna@example.com|Anna Prowadząca|Checkpoint: note.md"
    assert tracker.pending_paths() == []
    assert service.status().clean


def test_resave_resets_idle_timer_and_takes_over_authorship(tmp_path: Path):
    repo, settings, clock, tracker, service = _setup(tmp_path)
    (repo / "note.md").write_text("anna's edit\n", encoding="utf-8")
    tracker.record_save("note.md", ANNA)
    clock.advance(250)
    (repo / "note.md").write_text("bartek's edit\n", encoding="utf-8")
    tracker.record_save("note.md", BART)
    clock.advance(250)  # 500s since Anna, 250s since Bartek — still hot
    assert tracker.flush_due(settings, git_service=service) == []
    clock.advance(51)
    results = tracker.flush_due(settings, git_service=service)
    assert [r.ok for r in results] == [True]
    assert _log(repo)[0].startswith("bartek@example.com|")


def test_each_author_gets_their_own_commit(tmp_path: Path):
    repo, settings, clock, tracker, service = _setup(tmp_path)
    (repo / "note.md").write_text("anna\n", encoding="utf-8")
    (repo / "second.md").write_text("bartek\n", encoding="utf-8")
    tracker.record_save("note.md", ANNA)
    tracker.record_save("second.md", BART)
    clock.advance(301)
    results = tracker.flush_due(settings, git_service=service)
    assert sorted(r.ok for r in results) == [True, True]
    authors = {line.split("|")[0] for line in _log(repo, 2)}
    assert authors == {"anna@example.com", "bartek@example.com"}


def test_same_author_files_batch_into_one_commit(tmp_path: Path):
    repo, settings, clock, tracker, service = _setup(tmp_path)
    for name in ("a.md", "b.md", "c.md", "d.md"):
        (repo / name).write_text("x\n", encoding="utf-8")
        tracker.record_save(name, ANNA)
    clock.advance(301)
    results = tracker.flush_due(settings, git_service=service)
    assert len(results) == 1 and results[0].ok
    assert _log(repo)[0].endswith("|Checkpoint: a.md, b.md, c.md (+1 more)")


def test_local_saves_use_ambient_repo_identity(tmp_path: Path):
    repo, settings, clock, tracker, service = _setup(tmp_path)
    (repo / "note.md").write_text("local edit\n", encoding="utf-8")
    tracker.record_save("note.md", None)
    clock.advance(301)
    results = tracker.flush_due(settings, git_service=service)
    assert [r.ok for r in results] == [True]
    assert _log(repo)[0].startswith("ambient@example.com|Ambient|")


def test_disabled_setting_never_commits_or_drains_queue(tmp_path: Path):
    repo, settings, clock, tracker, service = _setup(tmp_path, enabled=False)
    (repo / "note.md").write_text("edited\n", encoding="utf-8")
    tracker.record_save("note.md", ANNA)
    clock.advance(10_000)
    assert tracker.flush_due(settings, git_service=service) == []
    assert len(_log(repo)) == 1  # only the initial commit


def test_demo_mode_never_commits(tmp_path: Path):
    repo, settings, clock, tracker, _ = _setup(tmp_path, demo=True)
    tracker.record_save("note.md", ANNA)
    clock.advance(10_000)
    assert tracker.flush_due(settings) == []


def test_path_already_committed_by_hand_is_dropped_gracefully(tmp_path: Path):
    repo, settings, clock, tracker, service = _setup(tmp_path)
    (repo / "note.md").write_text("edited\n", encoding="utf-8")
    tracker.record_save("note.md", ANNA)
    _git(repo, "add", "note.md")
    _git(repo, "commit", "-qm", "manual commit beat the checkpoint")
    clock.advance(301)
    results = tracker.flush_due(settings, git_service=service)
    # The attempted commit reports "nothing to commit" but nothing blows
    # up and the queue is drained.
    assert all(not r.ok for r in results)
    assert tracker.pending_paths() == []
    assert len(_log(repo)) == 2


def test_force_flush_ignores_idle_window(tmp_path: Path):
    """Shutdown behavior: pending checkpoints commit immediately."""
    repo, settings, clock, tracker, service = _setup(tmp_path)
    (repo / "note.md").write_text("edited\n", encoding="utf-8")
    tracker.record_save("note.md", ANNA)
    results = tracker.flush_due(settings, git_service=service, force=True)
    assert [r.ok for r in results] == [True]
    assert service.status().clean


def test_non_repo_directory_drops_entries_without_error(tmp_path: Path):
    plain = tmp_path / "plain"
    plain.mkdir()
    (plain / "note.md").write_text("x\n", encoding="utf-8")
    settings = _settings(plain)
    clock = FakeClock()
    tracker = CheckpointTracker(clock=clock)
    tracker.record_save("note.md", ANNA)
    clock.advance(301)
    assert tracker.flush_due(settings, git_service=GitService(settings)) == []
    assert tracker.pending_paths() == []


def test_blank_env_value_disables_autocommit():
    # `NOTEELI_GIT_AUTOCOMMIT=` (bare line in .env) must mean "off", not
    # a pydantic bool-parse crash — same rule as the other flags.
    assert Settings(git_autocommit="", session_secret="t").git_autocommit is False
