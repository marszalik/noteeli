"""HTTP API for git integration.

All routes are auth-protected (same gate as the workspace API). Mutations
are blocked in demo mode. Git availability itself is decided per request
from the active preferences (local / sftp → available, gdrive → not).
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app.core.config import get_settings
from app.domains.auth.service import AuthService
from app.domains.git.schemas import (
    GitBlameResponse,
    GitCommitRequest,
    GitFileDiff,
    GitFileLog,
    GitOpResult,
    GitStatus,
)
from app.domains.git.service import (
    GitError,
    GitNotConfiguredError,
    GitService,
    GitUnavailableError,
)

router = APIRouter()
auth_service = AuthService()


def _service() -> GitService:
    return GitService(get_settings())


def _block_demo() -> None:
    if get_settings().demo_mode:
        raise HTTPException(status_code=403, detail="Read-only demo: git is disabled.")


@router.get("/api/git/status", response_model=GitStatus, name="git_status_api")
async def git_status_api(request: Request) -> GitStatus:
    auth_service.require_api_access(request)
    try:
        return _service().status()
    except GitError:
        # Never let a git hiccup break the workspace page — degrade to
        # "no git here".
        return GitStatus(available=False, is_repo=False)


def _read_op(request: Request, fn):
    """Shared wrapper for the read-only history endpoints: same auth gate,
    same error mapping as the mutating ones (but no demo block — reading
    history is harmless; demo has no git runner anyway)."""
    auth_service.require_api_access(request)
    try:
        return fn(_service())
    except GitUnavailableError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except GitNotConfiguredError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except GitError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/api/git/log", response_model=GitFileLog, name="git_log_api")
async def git_log_api(request: Request, path: str, limit: int = 30) -> GitFileLog:
    return _read_op(
        request,
        lambda s: GitFileLog(path=path, entries=s.file_log(path, limit)),
    )


@router.get("/api/git/blame", response_model=GitBlameResponse, name="git_blame_api")
async def git_blame_api(request: Request, path: str) -> GitBlameResponse:
    return _read_op(
        request,
        lambda s: GitBlameResponse(path=path, lines=s.blame(path)),
    )


@router.get("/api/git/diff", response_model=GitFileDiff, name="git_diff_api")
async def git_diff_api(request: Request, path: str, sha: str) -> GitFileDiff:
    return _read_op(
        request,
        lambda s: GitFileDiff(path=path, sha=sha, lines=s.commit_word_diff(path, sha)),
    )


@router.post("/api/git/commit", response_model=GitOpResult, name="git_commit_api")
async def git_commit_api(request: Request, payload: GitCommitRequest) -> GitOpResult:
    user = auth_service.require_api_access(request)
    _block_demo()
    service = _service()
    # Sign the commit as the logged-in user so shared workspaces attribute
    # each commit to whoever made it. Only real (Google) logins override the
    # repo's git config — localhost/demo synthetic users keep the repo's own
    # ambient identity so a solo self-hoster isn't stamped "local@noteeli".
    author = None
    if not user.get("is_local"):
        author = {"name": user.get("name", ""), "email": user.get("email", "")}
    try:
        result = service.commit(payload.message, payload.paths or None, author=author)
        if result.ok and payload.push:
            push = service.push()
            if not push.ok:
                return GitOpResult(
                    ok=False,
                    message=f"Committed, but push failed: {push.message}",
                    output=push.output,
                )
            return GitOpResult(ok=True, message="Committed and pushed.", output=push.output)
        return result
    except GitUnavailableError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except GitNotConfiguredError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except GitError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/api/git/push", response_model=GitOpResult, name="git_push_api")
async def git_push_api(request: Request) -> GitOpResult:
    return await _network(request, "push")


@router.post("/api/git/pull", response_model=GitOpResult, name="git_pull_api")
async def git_pull_api(request: Request) -> GitOpResult:
    return await _network(request, "pull")


@router.post("/api/git/fetch", response_model=GitOpResult, name="git_fetch_api")
async def git_fetch_api(request: Request) -> GitOpResult:
    return await _network(request, "fetch")


async def _network(request: Request, op: str) -> GitOpResult:
    auth_service.require_api_access(request)
    _block_demo()
    service = _service()
    try:
        return getattr(service, op)()
    except GitUnavailableError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except GitNotConfiguredError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except GitError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
