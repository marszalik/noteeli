"""Git integration for the workspace.

Git operates on the directory a workspace points at — the local
content_root for `source_type=local`, or the remote `sftp_path` for
`source_type=sftp` (commands run over SSH using the SFTP credentials).
Google Drive has no git.

Activation is automatic: if the workspace directory is inside a git work
tree, the git features light up. Remote + upstream are assumed to be
already configured (the user set them up via the CLI).

Commands are executed through a small runner abstraction:
  - LocalGitRunner  → subprocess `git -C <dir> …`
  - SftpGitRunner   → paramiko `cd <dir> && git …` over SSH

Only a fixed allow-list of subcommands is ever run, and every path that
originates from the client is validated (no absolute paths, no `..`) and
shell-quoted before reaching the remote shell.
"""
from __future__ import annotations

import re
import shlex
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path, PurePosixPath

from app.core.config import Settings, get_settings
from app.domains.git.schemas import (
    GitBlameLine,
    GitDiffLine,
    GitDiffSegment,
    GitFileChange,
    GitLogEntry,
    GitOpResult,
    GitStatus,
)
from app.domains.preferences.service import PreferencesService


class GitError(Exception):
    """Base class for git failures surfaced to the API layer."""


class GitUnavailableError(GitError):
    """Storage backend cannot host git (e.g. Google Drive)."""


class GitNotConfiguredError(GitError):
    """The workspace directory is not a git repository."""


# Subcommands we are ever willing to run. Belt-and-suspenders against a
# bug constructing an unexpected argv.
_ALLOWED_SUBCOMMANDS = {
    "rev-parse", "status", "add", "commit", "push", "pull", "fetch",
    "log", "blame", "show",
}


def _check_subcommand(args: list[str]) -> None:
    # Skip leading global options so the real subcommand is validated even
    # when we prepend `-c user.name=… -c user.email=…` for commit identity.
    i = 0
    while i < len(args) and args[i] == "-c":
        i += 2  # `-c` plus its `key=value`
    sub = args[i] if i < len(args) else None
    if sub not in _ALLOWED_SUBCOMMANDS:
        raise GitError(f"Refusing to run git subcommand: {sub if sub else '(none)'}")


class _GitRunner(ABC):
    @abstractmethod
    def run(self, args: list[str], timeout: int = 30) -> tuple[int, str, str]:
        """Run `git <args>` in the workspace dir. Returns (code, stdout, stderr)."""


class LocalGitRunner(_GitRunner):
    def __init__(self, repo_path: Path) -> None:
        self.repo_path = Path(repo_path)

    def run(self, args: list[str], timeout: int = 30) -> tuple[int, str, str]:
        _check_subcommand(args)
        try:
            proc = subprocess.run(
                ["git", "-C", str(self.repo_path), *args],
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except FileNotFoundError as exc:  # git binary missing
            raise GitError("git is not installed on the server.") from exc
        except subprocess.TimeoutExpired as exc:
            raise GitError("git command timed out.") from exc
        return proc.returncode, proc.stdout, proc.stderr


class SftpGitRunner(_GitRunner):
    def __init__(self, host: str, port: int, username: str, password: str, repo_path: str) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.repo_path = repo_path or "/"

    def run(self, args: list[str], timeout: int = 30) -> tuple[int, str, str]:
        _check_subcommand(args)
        import paramiko

        remote_cmd = "cd " + shlex.quote(self.repo_path) + " && git " + " ".join(
            shlex.quote(a) for a in args
        )
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            ssh.connect(
                hostname=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                timeout=10,
                allow_agent=False,
                look_for_keys=False,
            )
            _stdin, stdout, stderr = ssh.exec_command(remote_cmd, timeout=timeout)
            out = stdout.read().decode("utf-8", "replace")
            err = stderr.read().decode("utf-8", "replace")
            code = stdout.channel.recv_exit_status()
            return code, out, err
        except GitError:
            raise
        except Exception as exc:  # connection / auth / channel errors
            raise GitError(f"SSH error: {type(exc).__name__}: {exc}") from exc
        finally:
            try:
                ssh.close()
            except Exception:
                pass


class GitService:
    def __init__(self, settings: Settings | None = None, preferences=None) -> None:
        self.settings = settings or get_settings()
        self.preferences = preferences or PreferencesService(self.settings).get_preferences()
        self._runner = self._build_runner()

    # ── Runner wiring ───────────────────────────────────────────────

    def _build_runner(self) -> _GitRunner | None:
        # Demo mode is read-only and not a place for VCS operations.
        if getattr(self.settings, "demo_mode", False):
            return None
        source = getattr(self.preferences, "source_type", "local")
        if source == "local":
            return LocalGitRunner(Path(self.preferences.content_root))
        if source == "sftp":
            return SftpGitRunner(
                host=self.preferences.sftp_host,
                port=self.preferences.sftp_port,
                username=self.preferences.sftp_username,
                password=self.preferences.sftp_password,
                repo_path=self.preferences.sftp_path,
            )
        return None  # gdrive / unknown

    @property
    def available(self) -> bool:
        return self._runner is not None

    def _require_runner(self) -> _GitRunner:
        if self._runner is None:
            raise GitUnavailableError("Git is not available for this storage backend.")
        return self._runner

    # ── Read ────────────────────────────────────────────────────────

    def is_repo(self) -> bool:
        if self._runner is None:
            return False
        try:
            code, out, _ = self._runner.run(["rev-parse", "--is-inside-work-tree"])
        except GitError:
            return False
        return code == 0 and out.strip() == "true"

    def status(self) -> GitStatus:
        if self._runner is None:
            return GitStatus(available=False, is_repo=False)
        if not self.is_repo():
            return GitStatus(available=True, is_repo=False)

        code, out, err = self._runner.run(
            ["status", "--porcelain=v1", "--branch", "-z"]
        )
        if code != 0:
            # Repo exists but status failed — surface as not-a-repo rather
            # than 500ing the page.
            return GitStatus(available=True, is_repo=False)

        status = self._parse_status(out)
        skip = self._runtime_skip_relpaths()
        if skip and status.files:
            status.files = [f for f in status.files if not self._is_runtime_path(f.path, skip)]
            status.clean = not status.files
        return status

    @staticmethod
    def _is_runtime_path(path: str, skip: set[str]) -> bool:
        return any(path == s or path.startswith(s + "/") for s in skip)

    def _runtime_skip_relpaths(self) -> set[str]:
        """DB + sidecars + data_dir expressed relative to the workspace
        dir, so Noteeli's own runtime files never show up in git status
        when the operator put NOTEELI_DATA_DIR inside the notes folder.
        Only meaningful for the local source (the DB is always local)."""
        from pathlib import Path
        if getattr(self.preferences, "source_type", "local") != "local":
            return set()
        skip: set[str] = set()
        try:
            root = Path(self.preferences.content_root).resolve()
        except OSError:
            return skip
        db = self.settings.database_path
        candidates = [self.settings.data_dir, db]
        candidates += [db.parent / f"{db.name}{s}" for s in ("-wal", "-shm", "-journal")]
        for p in candidates:
            try:
                rel = Path(p).resolve().relative_to(root).as_posix()
            except (ValueError, OSError):
                continue
            if rel and rel != ".":
                skip.add(rel)
        return skip

    @staticmethod
    def _parse_status(raw: str) -> GitStatus:
        tokens = raw.split("\0")
        branch = ""
        upstream = ""
        ahead = 0
        behind = 0
        files: list[GitFileChange] = []

        i = 0
        # Branch header line (present because of --branch).
        if tokens and tokens[0].startswith("## "):
            header = tokens[0][3:]
            i = 1
            if header.startswith("HEAD (no branch)"):
                branch = "HEAD (detached)"
            else:
                # "main...origin/main [ahead 1, behind 2]"
                m = re.match(r"^(?P<branch>[^.\s]+)(?:\.\.\.(?P<up>\S+))?(?:\s+\[(?P<track>[^\]]+)\])?", header)
                if m:
                    branch = m.group("branch") or ""
                    upstream = m.group("up") or ""
                    track = m.group("track") or ""
                    am = re.search(r"ahead (\d+)", track)
                    bm = re.search(r"behind (\d+)", track)
                    ahead = int(am.group(1)) if am else 0
                    behind = int(bm.group(1)) if bm else 0

        while i < len(tokens):
            entry = tokens[i]
            i += 1
            if not entry:
                continue
            if len(entry) < 3:
                continue
            xy = entry[:2]
            path = entry[3:]
            # Renames/copies carry the original path in the next NUL token.
            if xy[0] in ("R", "C") or xy[1] in ("R", "C"):
                if i < len(tokens):
                    i += 1  # consume original path (we keep the new one)
            # Only decorate paths inside the workspace dir. Changes outside
            # (when the workspace is a subdir of a larger repo) come out as
            # ../something — skip them.
            if path.startswith("../") or path.startswith("/"):
                continue
            files.append(
                GitFileChange(
                    path=path.rstrip("/"),
                    status=GitService._display_status(xy),
                    staged=xy[0] not in (" ", "?"),
                )
            )

        return GitStatus(
            available=True,
            is_repo=True,
            branch=branch,
            upstream=upstream,
            ahead=ahead,
            behind=behind,
            clean=not files,
            files=files,
        )

    @staticmethod
    def _display_status(xy: str) -> str:
        if xy == "??":
            return "untracked"
        if "U" in xy or xy in ("AA", "DD"):
            return "conflict"
        flags = set(xy.replace(" ", ""))
        if "R" in flags:
            return "renamed"
        if "D" in flags:
            return "deleted"
        if "A" in flags:
            return "added"
        if "M" in flags:
            return "modified"
        return "modified"

    # ── History / blame / diff (read-only) ──────────────────────────

    _NULL_SHA = "0" * 40

    @staticmethod
    def _safe_rev(rev: str) -> str:
        """Validate a client-supplied revision before it reaches a shell.
        Only bare hex object names are accepted — no ranges, refs or flags."""
        cleaned = (rev or "").strip().lower()
        if not re.fullmatch(r"[0-9a-f]{4,40}", cleaned):
            raise GitError("Invalid revision.")
        return cleaned

    def _require_repo(self) -> _GitRunner:
        runner = self._require_runner()
        if not self.is_repo():
            raise GitNotConfiguredError("The workspace is not a git repository.")
        return runner

    def file_log(self, path: str, limit: int = 30) -> list[GitLogEntry]:
        """Commits that touched a file, newest first. Follows renames."""
        runner = self._require_repo()
        safe = self._safe_rel(path)
        limit = max(1, min(int(limit), 200))
        code, out, err = runner.run(
            [
                "log",
                f"-{limit}",
                "--follow",
                "--format=%H%x1f%an%x1f%ae%x1f%at%x1f%s%x1e",
                "--",
                safe,
            ]
        )
        if code != 0:
            raise GitError((err or out or "git log failed").strip())
        entries: list[GitLogEntry] = []
        for record in out.split("\x1e"):
            parts = record.strip("\n").split("\x1f")
            if len(parts) != 5:
                continue
            sha, name, email, timestamp, subject = parts
            entries.append(
                GitLogEntry(
                    sha=sha.strip(),
                    author_name=name,
                    author_email=email,
                    author_time=int(timestamp or 0),
                    subject=subject,
                )
            )
        return entries

    def blame(self, path: str) -> list[GitBlameLine]:
        """Per-line authorship of the working-tree version of a file."""
        runner = self._require_repo()
        safe = self._safe_rel(path)
        code, out, err = runner.run(["blame", "--porcelain", "--", safe], timeout=60)
        if code != 0:
            raise GitError((err or out or "git blame failed").strip())
        return self._parse_blame_porcelain(out)

    @classmethod
    def _parse_blame_porcelain(cls, raw: str) -> list[GitBlameLine]:
        # Porcelain repeats a "<sha> <orig> <final> [count]" header before
        # every line; full metadata (author, summary, …) appears only the
        # first time a commit is seen, so it is accumulated per sha.
        meta: dict[str, dict] = {}
        lines: list[GitBlameLine] = []
        current_sha = ""
        for entry in raw.split("\n"):
            if entry.startswith("\t"):
                info = meta.get(current_sha, {})
                email = info.get("author-mail", "").strip("<>")
                committed = current_sha != cls._NULL_SHA
                lines.append(
                    GitBlameLine(
                        sha=current_sha,
                        author_name=info.get("author", "") if committed else "",
                        author_email=email if committed else "",
                        author_time=int(info.get("author-time") or 0),
                        summary=info.get("summary", "") if committed else "",
                        committed=committed,
                        content=entry[1:],
                    )
                )
                continue
            head = entry.split(" ", 1)[0]
            if re.fullmatch(r"[0-9a-f]{40}", head):
                current_sha = head
                meta.setdefault(current_sha, {})
                continue
            if current_sha and entry:
                key, _, value = entry.partition(" ")
                meta[current_sha].setdefault(key, value)
        return lines

    def commit_word_diff(self, path: str, sha: str) -> list[GitDiffLine]:
        """Word-level diff a single commit introduced to a single file.
        Word granularity because notes are prose — a reflowed paragraph as a
        full-line diff is unreadable."""
        runner = self._require_repo()
        safe = self._safe_rel(path)
        rev = self._safe_rev(sha)
        # `show` (not `diff rev^ rev`) so root commits work too.
        code, out, err = runner.run(
            ["show", rev, "--format=", "--word-diff=porcelain", "--follow", "--", safe],
            timeout=60,
        )
        if code != 0:
            raise GitError((err or out or "git show failed").strip())
        return self._parse_word_diff_porcelain(out)

    @staticmethod
    def _parse_word_diff_porcelain(raw: str) -> list[GitDiffLine]:
        # Inside a hunk, porcelain word-diff emits one chunk per line
        # (prefix ' ' context, '+' added, '-' removed) and a bare '~' to
        # mark the end of each source line.
        result: list[GitDiffLine] = []
        segments: list[GitDiffSegment] = []
        in_hunk = False
        for entry in raw.split("\n"):
            if entry.startswith("@@"):
                if segments:
                    result.append(GitDiffLine(segments=segments))
                    segments = []
                in_hunk = True
                result.append(GitDiffLine(hunk=entry))
                continue
            if not in_hunk:
                continue  # diff/index/---/+++ headers
            if entry == "~":
                result.append(GitDiffLine(segments=segments))
                segments = []
                continue
            if not entry:
                continue
            prefix, text = entry[0], entry[1:]
            kind = {"+": "added", "-": "removed", " ": "context"}.get(prefix)
            if kind is None:
                continue
            segments.append(GitDiffSegment(kind=kind, text=text))
        if segments:
            result.append(GitDiffLine(segments=segments))
        return result

    # ── Write ───────────────────────────────────────────────────────

    @staticmethod
    def _safe_rel(path: str) -> str:
        """Validate a client-supplied workspace-relative path before it
        reaches a shell. Reject absolute paths and any `..` traversal."""
        cleaned = (path or "").strip().lstrip("/")
        if not cleaned:
            raise GitError("Empty path.")
        parts = PurePosixPath(cleaned).parts
        if any(p == ".." for p in parts):
            raise GitError("Path traversal is not allowed.")
        return cleaned

    @staticmethod
    def _identity_args(author: dict | None) -> list[str]:
        """Build `-c user.name=… -c user.email=…` so the commit is signed by
        the logged-in user (author AND committer) rather than the instance's
        ambient git config. Shared/collaborative workspaces thus attribute
        each commit to whoever made it."""
        if not author:
            return []
        email = (author.get("email") or "").strip()
        if not email:
            return []
        name = (author.get("name") or "").strip() or email
        return ["-c", f"user.name={name}", "-c", f"user.email={email}"]

    def commit(self, message: str, paths: list[str] | None = None, author: dict | None = None) -> GitOpResult:
        runner = self._require_runner()
        if not self.is_repo():
            raise GitNotConfiguredError("The workspace is not a git repository.")
        message = (message or "").strip()
        if not message:
            raise GitError("Commit message is required.")

        if paths:
            safe = [self._safe_rel(p) for p in paths]
            code, out, err = runner.run(["add", "--", *safe])
        else:
            code, out, err = runner.run(["add", "-A"])
        if code != 0:
            return GitOpResult(ok=False, message=(err or out or "git add failed").strip())

        code, out, err = runner.run([*self._identity_args(author), "commit", "-m", message])
        if code != 0:
            text = (out + "\n" + err).lower()
            if "nothing to commit" in text or "no changes added" in text:
                return GitOpResult(ok=False, message="Nothing to commit.")
            return GitOpResult(ok=False, message=(err or out or "git commit failed").strip())
        return GitOpResult(ok=True, message="Committed.", output=out.strip())

    def push(self) -> GitOpResult:
        return self._network_op(["push"], "Pushed.")

    def pull(self) -> GitOpResult:
        return self._network_op(["pull", "--ff-only"], "Pulled.")

    def fetch(self) -> GitOpResult:
        return self._network_op(["fetch"], "Fetched.")

    def _network_op(self, args: list[str], ok_message: str) -> GitOpResult:
        runner = self._require_runner()
        if not self.is_repo():
            raise GitNotConfiguredError("The workspace is not a git repository.")
        code, out, err = runner.run(args, timeout=90)
        combined = (out + ("\n" if out and err else "") + err).strip()
        if code != 0:
            return GitOpResult(ok=False, message=(err or out or "git failed").strip(), output=combined)
        return GitOpResult(ok=True, message=ok_message, output=combined)
