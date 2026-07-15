"""Routes for the publish feature.

Two surfaces:
- /api/publish/* — auth-protected mutation API for the workspace UI
- /{id}/{slug}   — public, no auth, renders a scoped read-only Noteeli
- /api/public/*  — public, no auth, scoped tree/file/preview reads
"""
from __future__ import annotations

import json
import mimetypes
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, Response

from app import __version__ as app_version
from app.core.config import get_settings
from app.core.templates import render_template
from app.domains.auth.service import AuthService
from app.domains.publish.schemas import (
    PublicNavItem,
    PublicNavResponse,
    PublishedItem,
    PublishedItemsResponse,
    PublishRequest,
)
from app.domains.publish.service import (
    PublishedItemAlreadyExistsError,
    PublishedItemNotFoundError,
    PublishService,
)
from app.domains.workspace.schemas import FileDocument, TreeNode
from app.domains.workspace.service import (
    DemoReadOnlyError,
    DocumentNotFoundError,
    InvalidPathError,
    UnsupportedFileTypeError,
    WorkspaceService,
)


router = APIRouter(tags=["publish"])


# These are tiny factories rather than module-level singletons so that
# tests with different content_root/data_dir env settings see a fresh
# service that uses *their* SQLite DB. The caches here are cheap.
def _auth_service() -> AuthService:
    return AuthService(get_settings())


def _publish_service() -> PublishService:
    return PublishService(get_settings())


def _workspace_service() -> WorkspaceService:
    return WorkspaceService(get_settings())


# ── Mutation API (auth required) ─────────────────────────────────


@router.get(
    "/api/publish",
    response_model=PublishedItemsResponse,
    name="publish_list_api",
)
async def publish_list_api(request: Request):
    _auth_service().require_api_access(request)
    return PublishedItemsResponse(items=_publish_service().list_published())


@router.post(
    "/api/publish",
    response_model=PublishedItem,
    name="publish_create_api",
)
async def publish_create_api(request: Request, payload: PublishRequest):
    _auth_service().require_api_access(request)
    if get_settings().demo_mode:
        raise HTTPException(
            status_code=403,
            detail="Demo mode: publishing is disabled.",
        )
    # Confirm the target really is what the client claims it is — no
    # publishing of non-existent paths or path-traversal escapes.
    try:
        rel = _workspace_service().get_document_path(payload.path)
    except (InvalidPathError, DocumentNotFoundError):
        # Try as directory
        try:
            backend = _workspace_service()._get_backend()
            rel = _workspace_service()._resolve_path(payload.path, backend)
        except (InvalidPathError, DocumentNotFoundError) as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    backend = _workspace_service()._get_backend()
    is_dir = backend.is_dir(rel)
    kind = "directory" if is_dir else "file"

    try:
        return _publish_service().publish(kind=kind, path=rel)
    except PublishedItemAlreadyExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.delete(
    "/api/publish/{item_id}",
    name="publish_delete_api",
)
async def publish_delete_api(request: Request, item_id: int):
    _auth_service().require_api_access(request)
    if get_settings().demo_mode:
        raise HTTPException(
            status_code=403,
            detail="Demo mode: publishing is disabled.",
        )
    try:
        _publish_service().unpublish(item_id)
    except PublishedItemNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"ok": True}


# ── Public HTML (no auth) ────────────────────────────────────────


def _gone_page() -> HTMLResponse:
    """Human-readable 404 for dead public links. This is a browser-facing
    HTML route — a bare JSON `{"detail": …}` here reads as a broken app.
    Links die legitimately: unpublishing, or renaming/deleting the source
    file auto-drops its publish entry."""
    return HTMLResponse(
        status_code=404,
        content="""<!doctype html>
<html lang="pl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Noteeli</title>
<style>
  body { font-family: system-ui, sans-serif; display: grid; place-items: center;
         min-height: 100vh; margin: 0; background: #f6f4ef; color: #2b2a27; }
  main { text-align: center; padding: 2rem; max-width: 26rem; }
  h1 { font-size: 1.3rem; margin-bottom: 0.4rem; }
  p { color: #6b6a66; line-height: 1.5; }
  @media (prefers-color-scheme: dark) {
    body { background: #12151c; color: #e8e6e3; }
    p { color: #9a999f; }
  }
</style>
</head>
<body>
<main>
  <h1>Ta strona nie jest już opublikowana</h1>
  <p>Notatka została wycofana z publikacji albo przeniesiona.
     Poproś autora o nowy link.</p>
  <p lang="en">This page is no longer published. The note was unpublished
     or moved — ask the author for a fresh link.</p>
</main>
</body>
</html>""",
    )


@router.get("/{item_id:int}/{slug}", name="publish_view_page")
async def publish_view_page(request: Request, item_id: int, slug: str):
    try:
        item = _publish_service().find_by_id(item_id)
    except PublishedItemNotFoundError:
        return _gone_page()

    # Slug mismatch → redirect to the canonical URL so users that
    # bookmark the wrong slug end up on the right page.
    if slug != item.slug:
        return RedirectResponse(url=item.public_url, status_code=301)

    # Build the frontend config to point every API call at the public,
    # scoped routes — same template, restricted backend.
    public_config = {
        "treeUrl": str(request.url_for("publish_public_tree_api", id=item_id)),
        "fileUrl": str(request.url_for("publish_public_file_api", id=item_id)),
        "previewUrl": str(request.url_for("publish_public_file_preview_api", id=item_id)),
        "embeddedAssetUrl": str(
            request.url_for("publish_public_file_preview_api", id=item_id)
        ),
        "pygmentsCssUrl": str(request.url_for("publish_pygments_css")),
        "publishedNavUrl": str(request.url_for("publish_public_published_api")),
        "isPublic": True,
    }

    preferences = _workspace_service().get_preferences()
    return render_template(
        "domains/workspace/views/index.mako",
        request,
        user={
            "email": "public@noteeli",
            "name": "Public visitor",
            "is_local": True,
            "is_public": True,
        },
        # Show only the basename of the published item in the sidebar —
        # leaking the full filesystem path on a public URL would be a
        # security smell. The basename matches what visitors expect to
        # see ("psi.md", "FadingSuns") and nothing more.
        content_root=Path(item.path).name or item.slug,
        preferences=preferences,
        database_path="",
        app_version=app_version,
        demo_mode=False,
        public_view=item,
        frontend_config=json.dumps(public_config),
    )


# ── Public CSS ──────────────────────────────────────────────────


@router.get(
    "/api/public/pygments.css",
    name="publish_pygments_css",
)
async def publish_pygments_css() -> Response:
    """Pygments stylesheet for the syntax-highlighted code blocks
    rendered server-side. Cached aggressively — the body only changes
    when Pygments itself is upgraded."""
    from app.domains.publish import render as _render

    return Response(
        content=_render.pygments_css(),
        media_type="text/css",
        headers={"Cache-Control": "public, max-age=86400"},
    )


# ── Public scoped API (no auth) ──────────────────────────────────


@router.get(
    "/api/public/published",
    response_model=PublicNavResponse,
    name="publish_public_published_api",
)
async def publish_public_published_api() -> PublicNavResponse:
    """All published items of this instance, as display names + public
    URLs — powers the cross-item nav in the shared-page sidebar. Every
    entry here is already public by definition; filesystem paths are
    deliberately not included."""
    items = [
        PublicNavItem(
            name=Path(item.path).name or item.slug,
            kind=item.kind,
            public_url=item.public_url,
        )
        for item in _publish_service().list_published()
    ]
    return PublicNavResponse(items=items)


@router.get(
    "/api/public/{id}/tree",
    response_model=TreeNode,
    name="publish_public_tree_api",
)
async def publish_public_tree_api(id: int):
    try:
        item = _publish_service().find_by_id(id)
    except PublishedItemNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    # For a published file, return a synthetic single-leaf tree so the
    # frontend can render the sidebar consistently.
    if item.kind == "file":
        return TreeNode(
            name=Path(item.path).name,
            path="",
            kind="directory",
            children=[
                TreeNode(
                    name=Path(item.path).name,
                    path=item.path,
                    kind="file",
                    children=[],
                    editable=True,
                )
            ],
            editable=False,
        )

    full_tree = _workspace_service().build_tree()
    scoped = _find_subtree(full_tree, item.path)
    if scoped is None:
        raise HTTPException(status_code=404, detail="Published path no longer exists.")
    # Reset the scope-root path so the frontend's relative-path math
    # works (paths inside the response are still original-relative,
    # which is what the file API expects).
    return scoped


@router.get(
    "/api/public/{id}/file",
    response_model=FileDocument,
    name="publish_public_file_api",
)
async def publish_public_file_api(request: Request, id: int, path: str = ""):
    try:
        item = _publish_service().find_by_id(id)
    except PublishedItemNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    # Default to the published file/the first viewable file in the folder.
    if not path:
        if item.kind == "file":
            path = item.path
        else:
            path = item.path  # the folder itself; the frontend handles the empty-state
    if not _publish_service().is_in_scope(item, path):
        raise HTTPException(
            status_code=403,
            detail="That path is not part of the published item.",
        )
    try:
        document = _workspace_service().read_document(path)
    except (InvalidPathError, DocumentNotFoundError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    # Server-render the content so the public viewer can drop the HTML
    # straight into a <div> instead of bringing up Toast UI / CodeMirror /
    # JSONEditor on a read-only page.
    from app.domains.publish import render as _render

    if document.editable:
        asset_url = str(
            request.url_for("publish_public_file_preview_api", id=id)
        )
        if document.file_type == "markdown":
            document.html = _render.render_markdown_html(
                document.content,
                source_path=document.path,
                asset_url=asset_url,
            )
        elif document.file_type == "json":
            document.html = _render.render_json_html(document.content)
        else:
            # Code / text fallback — Pygments by extension if known,
            # plain <pre> otherwise.
            document.html = _render.render_code_html(
                document.content, document.name
            )
    return document


@router.get(
    "/api/public/{id}/file/preview",
    name="publish_public_file_preview_api",
)
async def publish_public_file_preview_api(
    request: Request,
    background_tasks: BackgroundTasks,
    id: int,
    path: str = "",
    source_path: str = "",
    target: str = "",
):
    try:
        item = _publish_service().find_by_id(id)
    except PublishedItemNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    # The same endpoint serves two flows:
    #  - direct preview: /api/public/file/preview?id=...&path=foo.png
    #  - embedded asset: ?source_path=note.md&target=../images/foo.png
    if source_path and target:
        try:
            resolved, _kind = _workspace_service().resolve_embedded_asset(
                source_path, target
            )
        except (InvalidPathError, DocumentNotFoundError) as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except UnsupportedFileTypeError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        rel_path = resolved
    else:
        rel_path = path

    if not _publish_service().is_in_scope(item, rel_path):
        raise HTTPException(
            status_code=403,
            detail="That asset is not part of the published item.",
        )

    preview_kind = _workspace_service().get_preview_kind(rel_path)
    if preview_kind in ("docx", "xlsx", "pptx"):
        return HTMLResponse(content=_workspace_service().render_office_preview(rel_path))

    local_path, is_temporary = _workspace_service().get_local_path(rel_path)
    if is_temporary:
        background_tasks.add_task(Path.unlink, local_path, missing_ok=True)
    media_type, _ = mimetypes.guess_type(str(local_path))
    return FileResponse(
        path=local_path,
        media_type=media_type or "application/octet-stream",
    )


# ── Helpers ──────────────────────────────────────────────────────


def _find_subtree(node: TreeNode, target_path: str) -> TreeNode | None:
    """Walk a TreeNode and return the descendant whose path matches."""
    if node.path == target_path:
        return node
    for child in node.children or []:
        found = _find_subtree(child, target_path)
        if found is not None:
            return found
    return None
