"""Silent auto-checkpoint commits for shared workspaces.

"End of an editing session" is not an observable event, so we approximate
it with an idle debounce: every successful save records the file here,
and once a file has been quiet for `git_autocommit_idle_seconds` a
background loop (started from the app lifespan) commits it — signed by
whoever saved it last, exactly like a manual commit from the git menu.
One commit per author per flush, so attribution stays truthful when
several people go idle inside the same window.

The tracker is in-memory by design: a restart loses only *pending*
checkpoints, and anything still dirty gets picked up by the next editing
session. The app shutdown hook force-flushes, so a clean restart loses
nothing. Checkpoints are best-effort and must never break saving — every
failure is logged and swallowed.
"""
from __future__ import annotations

import asyncio
import logging
import threading
import time

from app.core.config import Settings, get_settings

logger = logging.getLogger("noteeli.git.checkpoint")


class CheckpointTracker:
    def __init__(self, clock=time.monotonic) -> None:
        self._clock = clock
        self._lock = threading.Lock()
        # path -> {"at": monotonic timestamp of last save, "author": dict|None}
        self._pending: dict[str, dict] = {}

    def record_save(self, path: str, author: dict | None = None) -> None:
        """Mark a file as saved. Re-saving resets its idle timer and takes
        over authorship (last writer wins)."""
        cleaned = (path or "").strip().lstrip("/")
        if not cleaned:
            return
        with self._lock:
            self._pending[cleaned] = {"at": self._clock(), "author": author}

    def pending_paths(self) -> list[str]:
        with self._lock:
            return sorted(self._pending)

    def _pop_due(self, idle_seconds: float, *, force: bool = False) -> list[tuple[str, dict | None]]:
        now = self._clock()
        due: list[tuple[str, dict | None]] = []
        with self._lock:
            for path, entry in list(self._pending.items()):
                if force or now - entry["at"] >= idle_seconds:
                    due.append((path, entry["author"]))
                    del self._pending[path]
        return due

    def flush_due(
        self,
        settings: Settings | None = None,
        git_service=None,
        *,
        force: bool = False,
    ) -> list:
        """Commit every file that has been idle long enough (or everything,
        when force=True — used on shutdown). Returns the GitOpResults of the
        commits actually attempted."""
        settings = settings or get_settings()
        if not settings.git_autocommit or settings.demo_mode:
            return []
        due = self._pop_due(settings.git_autocommit_idle_seconds, force=force)
        if not due:
            return []

        from app.domains.git.service import GitError, GitService

        results = []
        try:
            service = git_service or GitService(settings)
            if not service.available or not service.is_repo():
                # Not a repo (or gdrive) — nothing to checkpoint; the popped
                # entries are dropped so the queue can't grow forever.
                return []
            # Group by author so each person's edits land in their own
            # commit. Key "" collects local/anonymous saves (ambient repo
            # identity, same rule as manual commits).
            groups: dict[str, tuple[dict | None, list[str]]] = {}
            for path, author in due:
                key = (author or {}).get("email", "") or ""
                groups.setdefault(key, (author, []))[1].append(path)
            for author, paths in groups.values():
                result = service.commit(self._message(paths), paths, author=author)
                results.append(result)
                if result.ok:
                    logger.info("checkpoint committed: %s", ", ".join(paths))
                elif "nothing to commit" not in result.message.lower():
                    logger.warning("checkpoint commit failed: %s", result.message)
            if getattr(settings, "git_autocommit_push", False) and any(
                r.ok for r in results
            ):
                sync = service.sync_push()
                if sync.ok:
                    logger.info("checkpoint push: %s", sync.message)
                elif sync.output == "no_remote":
                    logger.debug("checkpoint push skipped: no remote")
                else:
                    logger.warning("checkpoint push %s: %s", sync.output, sync.message)
        except GitError as exc:
            logger.warning("checkpoint flush failed: %s", exc)
        except Exception:
            logger.exception("checkpoint flush failed")
        return results

    @staticmethod
    def _message(paths: list[str]) -> str:
        names = [p.rsplit("/", 1)[-1] for p in sorted(paths)]
        shown = ", ".join(names[:3])
        if len(names) > 3:
            shown += f" (+{len(names) - 3} more)"
        return f"Checkpoint: {shown}"


checkpoint_tracker = CheckpointTracker()


async def run_checkpoint_loop(interval_seconds: float = 1.0) -> None:
    """Tick the tracker until cancelled. The tick itself is a dict scan —
    git only runs when something is actually due."""
    while True:
        await asyncio.sleep(interval_seconds)
        try:
            await asyncio.to_thread(checkpoint_tracker.flush_due)
        except Exception:
            logger.exception("checkpoint loop iteration failed")
