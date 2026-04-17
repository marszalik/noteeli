import json
import mimetypes
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, RedirectResponse

from app.core.config import get_settings
from app.core.templates import render_template
from app.domains.preferences.schemas import (
    AppPreferences,
    ReorderItemsRequest,
    SavePreferencesProfileRequest,
    SavedPreferencesProfilesResponse,
    SavedPreferencesProfile,
    UpdatePreferencesRequest,
)
from app.domains.auth.service import AuthService
from app.domains.preferences.service import PreferenceProfileConflictError, PreferenceProfileNotFoundError
from app.domains.workspace.schemas import (
    CreateDirectoryBrowserRequest,
    CreateItemRequest,
    CreatedItem,
    DirectoryBrowserResponse,
    FileDocument,
    MoveItemRequest,
    RenameItemRequest,
    SaveFileRequest,
    TreeNode,
    UploadItemsResponse,
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
            "preferenceProfilesUrl": str(request.url_for("workspace_preference_profiles_api")),
            "orderUrl": str(request.url_for("workspace_reorder_api")),
            "createUrl": str(request.url_for("workspace_create_item_api")),
            "moveUrl": str(request.url_for("workspace_move_item_api")),
            "uploadUrl": str(request.url_for("workspace_upload_items_api")),
            "downloadUrl": str(request.url_for("workspace_download_item_api")),
            "deleteUrl": str(request.url_for("workspace_delete_item_api")),
            "renameUrl": str(request.url_for("workspace_rename_item_api")),
            "directoriesUrl": str(request.url_for("workspace_directories_api")),
            "createDirectoryUrl": str(request.url_for("workspace_create_directory_api")),
            "previewUrl": str(request.url_for("workspace_file_preview_api")),
            "embeddedAssetUrl": str(request.url_for("workspace_embedded_asset_preview_api")),
        }
    )
    return render_template(
        "domains/workspace/views/index.mako",
        request,
        user=user,
        content_root=workspace_service.root_display,
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


@router.get("/api/file/preview", name="workspace_file_preview_api")
async def workspace_file_preview_api(request: Request, background_tasks: BackgroundTasks, path: str):
    auth_service.require_api_access(request)
    try:
        rel_path = workspace_service.get_document_path(path)
    except InvalidPathError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    preview_kind = workspace_service.get_preview_kind(rel_path)
    if preview_kind is None:
        raise HTTPException(status_code=422, detail="This file type is not available in preview mode.")

    local_path, is_temporary = workspace_service.get_local_path(rel_path)
    if is_temporary:
        background_tasks.add_task(Path.unlink, local_path, missing_ok=True)

    media_type, _ = mimetypes.guess_type(str(local_path))
    return FileResponse(path=local_path, media_type=media_type or "application/octet-stream")


@router.get("/api/embedded-asset", name="workspace_embedded_asset_preview_api")
async def workspace_embedded_asset_preview_api(
    request: Request,
    background_tasks: BackgroundTasks,
    source_path: str,
    target: str,
):
    auth_service.require_api_access(request)
    try:
        rel_path, _preview_kind = workspace_service.resolve_embedded_asset(source_path, target)
    except InvalidPathError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except UnsupportedFileTypeError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    local_path, is_temporary = workspace_service.get_local_path(rel_path)
    if is_temporary:
        background_tasks.add_task(Path.unlink, local_path, missing_ok=True)

    media_type, _ = mimetypes.guess_type(str(local_path))
    return FileResponse(path=local_path, media_type=media_type or "application/octet-stream")


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


@router.post("/api/items/upload", response_model=UploadItemsResponse, name="workspace_upload_items_api")
async def workspace_upload_items_api(
    request: Request,
    parent_path: str = Form(""),
    files: list[UploadFile] = File(...),
):
    auth_service.require_api_access(request)
    if not files:
        raise HTTPException(status_code=400, detail="At least one file is required.")

    uploads: list[tuple[str, bytes]] = []
    for upload in files:
        uploads.append((upload.filename or "", await upload.read()))

    try:
        return workspace_service.upload_files(parent_path, uploads)
    except InvalidPathError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/api/download", name="workspace_download_item_api")
async def workspace_download_item_api(request: Request, background_tasks: BackgroundTasks, path: str):
    auth_service.require_api_access(request)
    try:
        download_path, filename, is_temporary = workspace_service.prepare_download(path)
    except InvalidPathError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    if is_temporary:
        background_tasks.add_task(Path.unlink, download_path, missing_ok=True)

    media_type, _ = mimetypes.guess_type(str(download_path))
    return FileResponse(
        path=download_path,
        media_type=media_type or "application/octet-stream",
        filename=filename,
    )


@router.post("/api/items/rename", response_model=CreatedItem, name="workspace_rename_item_api")
async def workspace_rename_item_api(request: Request, payload: RenameItemRequest):
    auth_service.require_api_access(request)
    try:
        return workspace_service.rename_item(payload.path, payload.new_name)
    except InvalidPathError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ItemAlreadyExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.delete("/api/items", name="workspace_delete_item_api")
async def workspace_delete_item_api(request: Request, path: str):
    auth_service.require_api_access(request)
    try:
        workspace_service.delete_item(path)
    except InvalidPathError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"status": "deleted"}


@router.get("/api/directories", response_model=DirectoryBrowserResponse, name="workspace_directories_api")
async def workspace_directories_api(request: Request, path: str | None = None):
    auth_service.require_api_access(request)
    try:
        return workspace_service.browse_directories(path)
    except InvalidPathError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/api/directories", response_model=DirectoryBrowserResponse, name="workspace_create_directory_api")
async def workspace_create_directory_api(request: Request, payload: CreateDirectoryBrowserRequest):
    auth_service.require_api_access(request)
    try:
        return workspace_service.create_browsed_directory(payload.parent_path, payload.name)
    except InvalidPathError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ItemAlreadyExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/api/preferences", response_model=AppPreferences, name="workspace_preferences_api")
async def workspace_preferences_api(request: Request):
    auth_service.require_api_access(request)
    return workspace_service.get_preferences()


@router.put("/api/preferences", response_model=AppPreferences, name="workspace_update_preferences_api")
async def workspace_update_preferences_api(request: Request, payload: UpdatePreferencesRequest):
    auth_service.require_api_access(request)
    return workspace_service.update_preferences(
        content_root=payload.content_root,
        sort_mode=payload.sort_mode,
        theme_mode=payload.theme_mode,
        editor_font_size=payload.editor_font_size,
        source_type=payload.source_type,
        sftp_host=payload.sftp_host,
        sftp_port=payload.sftp_port,
        sftp_username=payload.sftp_username,
        sftp_password=payload.sftp_password,
        sftp_path=payload.sftp_path,
        gdrive_folder_id=payload.gdrive_folder_id,
        image_upload_mode=payload.image_upload_mode,
        image_upload_subdir=payload.image_upload_subdir,
    )


@router.get(
    "/api/preferences/profiles",
    response_model=SavedPreferencesProfilesResponse,
    name="workspace_preference_profiles_api",
)
async def workspace_preference_profiles_api(request: Request):
    auth_service.require_api_access(request)
    return SavedPreferencesProfilesResponse(profiles=workspace_service.list_preference_profiles())


@router.post(
    "/api/preferences/profiles",
    response_model=SavedPreferencesProfile,
    name="workspace_save_preference_profile_api",
)
async def workspace_save_preference_profile_api(request: Request, payload: SavePreferencesProfileRequest):
    auth_service.require_api_access(request)
    try:
        return workspace_service.save_preference_profile(
            name=payload.name,
            content_root=payload.content_root,
            sort_mode=payload.sort_mode,
            theme_mode=payload.theme_mode,
            editor_font_size=payload.editor_font_size,
            source_type=payload.source_type,
            sftp_host=payload.sftp_host,
            sftp_port=payload.sftp_port,
            sftp_username=payload.sftp_username,
            sftp_password=payload.sftp_password,
            sftp_path=payload.sftp_path,
            gdrive_folder_id=payload.gdrive_folder_id,
            gdrive_credentials=payload.gdrive_credentials,
            image_upload_mode=payload.image_upload_mode,
            image_upload_subdir=payload.image_upload_subdir,
        )
    except PreferenceProfileConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.put(
    "/api/preferences/profiles/{profile_id}",
    response_model=SavedPreferencesProfile,
    name="workspace_update_preference_profile_api",
)
async def workspace_update_preference_profile_api(
    request: Request,
    profile_id: int,
    payload: SavePreferencesProfileRequest,
):
    auth_service.require_api_access(request)
    try:
        return workspace_service.update_preference_profile(
            profile_id,
            name=payload.name,
            content_root=payload.content_root,
            sort_mode=payload.sort_mode,
            theme_mode=payload.theme_mode,
            editor_font_size=payload.editor_font_size,
            source_type=payload.source_type,
            sftp_host=payload.sftp_host,
            sftp_port=payload.sftp_port,
            sftp_username=payload.sftp_username,
            sftp_password=payload.sftp_password,
            sftp_path=payload.sftp_path,
            gdrive_folder_id=payload.gdrive_folder_id,
            gdrive_credentials=payload.gdrive_credentials,
            image_upload_mode=payload.image_upload_mode,
            image_upload_subdir=payload.image_upload_subdir,
        )
    except PreferenceProfileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PreferenceProfileConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.delete(
    "/api/preferences/profiles/{profile_id}",
    name="workspace_delete_preference_profile_api",
)
async def workspace_delete_preference_profile_api(request: Request, profile_id: int):
    auth_service.require_api_access(request)
    try:
        workspace_service.delete_preference_profile(profile_id)
    except PreferenceProfileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"status": "deleted"}


@router.post(
    "/api/preferences/profiles/{profile_id}/apply",
    response_model=AppPreferences,
    name="workspace_apply_preference_profile_api",
)
async def workspace_apply_preference_profile_api(request: Request, profile_id: int):
    auth_service.require_api_access(request)
    try:
        return workspace_service.apply_preference_profile(profile_id)
    except PreferenceProfileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put("/api/order", response_model=AppPreferences, name="workspace_reorder_api")
async def workspace_reorder_api(request: Request, payload: ReorderItemsRequest):
    auth_service.require_api_access(request)
    try:
        return workspace_service.reorder_items(payload.parent_path, payload.ordered_paths)
    except InvalidPathError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
