"""HTTP API for review comments — thin wrapper over CommentsService."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app.core.config import get_settings
from app.domains.auth.service import AuthService
from app.domains.comments.schemas import CommentsDocument, CreateCommentRequest, UpdateCommentRequest
from app.domains.comments.service import (
    CommentAlreadyExistsError,
    CommentError,
    CommentNotFoundError,
    CommentsService,
)
from app.domains.workspace.router import record_checkpoint_save, workspace_service
from app.domains.workspace.service import (
    DemoReadOnlyError,
    DocumentNotFoundError,
    InvalidPathError,
    StorageNotConfiguredError,
)

router = APIRouter(tags=["comments"])
auth_service = AuthService(get_settings())
comments_service = CommentsService(workspace_service)


def _run(fn):
    try:
        return fn()
    except InvalidPathError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except CommentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except CommentAlreadyExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except DemoReadOnlyError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except StorageNotConfiguredError as exc:
        raise HTTPException(status_code=402, detail=str(exc)) from exc
    except CommentError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _after_write(result: CommentsDocument, user: dict) -> CommentsDocument:
    # The sidecar is a regular file in the workspace: let the silent
    # git checkpoint pick it up like any other save.
    record_checkpoint_save(result.comments_path, user)
    return result


@router.get("/api/comments", response_model=CommentsDocument, name="comments_list_api")
async def comments_list_api(request: Request, path: str):
    auth_service.require_api_access(request)
    return _run(lambda: comments_service.list_comments(path))


@router.post("/api/comments", response_model=CommentsDocument, name="comments_create_api")
async def comments_create_api(request: Request, payload: CreateCommentRequest):
    user = auth_service.require_api_access(request)
    result = _run(lambda: comments_service.add_comment(payload.path, payload.text, payload.id))
    return _after_write(result, user)


@router.patch("/api/comments/{comment_id}", response_model=CommentsDocument, name="comments_update_api")
async def comments_update_api(request: Request, comment_id: str, payload: UpdateCommentRequest):
    user = auth_service.require_api_access(request)
    result = _run(
        lambda: comments_service.update_comment(
            payload.path, comment_id, text=payload.text, status=payload.status
        )
    )
    return _after_write(result, user)


@router.delete("/api/comments/{comment_id}", response_model=CommentsDocument, name="comments_delete_api")
async def comments_delete_api(request: Request, comment_id: str, path: str):
    user = auth_service.require_api_access(request)
    result = _run(lambda: comments_service.delete_comment(path, comment_id))
    return _after_write(result, user)
