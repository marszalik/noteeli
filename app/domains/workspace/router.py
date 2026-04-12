import json

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse

from app.core.config import get_settings
from app.core.templates import render_template
from app.domains.preferences.schemas import (
    AppPreferences,
    ReorderItemsRequest,
    UpdatePreferencesRequest,
)
from app.domains.auth.service import AuthService
from app.domains.workspace.schemas import (
    CreateItemRequest,
    CreatedItem,
    DirectoryBrowserResponse,
    FileDocument,
    MoveItemRequest,
    SaveFileRequest,
    TreeNode,
)
from app.domains.workspace.service import (
    DocumentNotFoundError,
    ItemAlreadyExistsError,
    InvalidPathError,
    UnsupportedFileTypeError,
    WorkspaceService,
)


router = APIRouter(tags=["workspace"])
settings = get_settings()
auth_service = AuthService(settings)
workspace_service = WorkspaceService(settings)


@router.get("/", name="workspace_page")
async def workspace_page(request: Request):
    user = auth_service.get_current_user(request)
    if user is None:
        return RedirectResponse(url=request.url_for("login_page"), status_code=303)

    preferences = workspace_service.get_preferences()
    frontend_config = json.dumps(
        {
            "treeUrl": str(request.url_for("workspace_tree_api")),
            "fileUrl": str(request.url_for("workspace_file_api")),
            "saveUrl": str(request.url_for("workspace_save_api")),
            "preferencesUrl": str(request.url_for("workspace_preferences_api")),
            "orderUrl": str(request.url_for("workspace_reorder_api")),
            "createUrl": str(request.url_for("workspace_create_item_api")),
            "moveUrl": str(request.url_for("workspace_move_item_api")),
            "directoriesUrl": str(request.url_for("workspace_directories_api")),
        }
    )
    return render_template(
        "domains/workspace/views/index.mako",
        request,
        user=user,
        content_root=str(workspace_service.root_path),
        preferences=preferences,
        database_path=str(settings.database_path),
        frontend_config=frontend_config,
    )


@router.get("/api/tree", response_model=TreeNode, name="workspace_tree_api")
async def workspace_tree_api(request: Request):
    auth_service.require_api_access(request)
    return workspace_service.build_tree()


@router.get("/api/file", response_model=FileDocument, name="workspace_file_api")
async def workspace_file_api(request: Request, path: str):
    auth_service.require_api_access(request)
    try:
        return workspace_service.read_document(path)
    except InvalidPathError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put("/api/file", response_model=FileDocument, name="workspace_save_api")
async def workspace_save_api(request: Request, payload: SaveFileRequest):
    auth_service.require_api_access(request)
    try:
        return workspace_service.save_document(payload.path, payload.content)
    except InvalidPathError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except UnsupportedFileTypeError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/api/items", response_model=CreatedItem, name="workspace_create_item_api")
async def workspace_create_item_api(request: Request, payload: CreateItemRequest):
    auth_service.require_api_access(request)
    try:
        return workspace_service.create_item(payload.parent_path, payload.name, payload.kind)
    except InvalidPathError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ItemAlreadyExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.put("/api/items/move", response_model=CreatedItem, name="workspace_move_item_api")
async def workspace_move_item_api(request: Request, payload: MoveItemRequest):
    auth_service.require_api_access(request)
    try:
        return workspace_service.move_item(payload.source_path, payload.target_parent_path)
    except InvalidPathError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ItemAlreadyExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/api/directories", response_model=DirectoryBrowserResponse, name="workspace_directories_api")
async def workspace_directories_api(request: Request, path: str | None = None):
    auth_service.require_api_access(request)
    try:
        return workspace_service.browse_directories(path)
    except InvalidPathError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/api/preferences", response_model=AppPreferences, name="workspace_preferences_api")
async def workspace_preferences_api(request: Request):
    auth_service.require_api_access(request)
    return workspace_service.get_preferences()


@router.put("/api/preferences", response_model=AppPreferences, name="workspace_update_preferences_api")
async def workspace_update_preferences_api(request: Request, payload: UpdatePreferencesRequest):
    auth_service.require_api_access(request)
    return workspace_service.update_preferences(
        payload.content_root,
        payload.sort_mode,
        payload.theme_mode,
        payload.editor_font_size,
    )


@router.put("/api/order", response_model=AppPreferences, name="workspace_reorder_api")
async def workspace_reorder_api(request: Request, payload: ReorderItemsRequest):
    auth_service.require_api_access(request)
    try:
        return workspace_service.reorder_items(payload.parent_path, payload.ordered_paths)
    except InvalidPathError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
