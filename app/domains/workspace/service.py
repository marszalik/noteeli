import tempfile
import zipfile
from pathlib import Path

from app.core.config import Settings, get_settings
from app.domains.preferences.repository import PreferencesRepository
from app.domains.preferences.schemas import AppPreferences, SavedPreferencesProfile, SortMode, SourceType
from app.domains.preferences.service import PreferencesService
from app.domains.workspace.schemas import (
    CreatedItem,
    DirectoryBrowserResponse,
    DirectoryOption,
    FileDocument,
    TreeNode,
    UploadItemsResponse,
    UploadedItemError,
)
from app.domains.workspace.storage import StorageBackend, StorageEntry, build_backend, invalidate_sftp_cache


class WorkspaceError(Exception):
    """Base error for workspace operations."""


class InvalidPathError(WorkspaceError):
    """Raised when a path points outside the configured content root."""


class DocumentNotFoundError(WorkspaceError):
    """Raised when the requested document does not exist."""


class UnsupportedFileTypeError(WorkspaceError):
    """Raised when the requested document is not supported by the editor."""


class ItemAlreadyExistsError(WorkspaceError):
    """Raised when the target file or directory already exists."""


class WorkspaceService:
    IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp", ".avif"}
    PDF_EXTENSIONS = {".pdf"}
    JSON_EXTENSIONS = {".json"}
    MAX_TEXT_FILE_BYTES = 1024 * 1024

    def __init__(
        self,
        settings: Settings | None = None,
        preferences_repository: PreferencesRepository | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.preferences_repository = preferences_repository or PreferencesRepository(self.settings)
        self.preferences_service = PreferencesService(self.settings, self.preferences_repository)

    def _get_backend(self) -> StorageBackend:
        return build_backend(self.preferences_service.get_preferences())

    @property
    def root_display(self) -> str:
        return self._get_backend().root_display

    def get_preferences(self) -> AppPreferences:
        return self.preferences_service.get_preferences()

    def update_preferences(
        self,
        content_root: str,
        sort_mode: SortMode,
        theme_mode: str,
        editor_font_size: int,
        source_type: SourceType = "local",
        sftp_host: str = "",
        sftp_port: int = 22,
        sftp_username: str = "",
        sftp_password: str = "",
        sftp_path: str = "/",
        gdrive_folder_id: str = "root",
        gdrive_credentials: str | None = None,
        autosave_enabled: bool = False,
        image_upload_mode: str = "same_dir",
        image_upload_subdir: str = "assets",
        language: str = "pl",
    ) -> AppPreferences:
        invalidate_sftp_cache()
        return self.preferences_service.update_preferences(
            content_root=content_root,
            sort_mode=sort_mode,
            theme_mode=theme_mode,
            editor_font_size=editor_font_size,
            source_type=source_type,
            sftp_host=sftp_host,
            sftp_port=sftp_port,
            sftp_username=sftp_username,
            sftp_password=sftp_password,
            sftp_path=sftp_path,
            gdrive_folder_id=gdrive_folder_id,
            gdrive_credentials=gdrive_credentials,
            autosave_enabled=autosave_enabled,
            image_upload_mode=image_upload_mode,
            image_upload_subdir=image_upload_subdir,
            language=language,
        )

    def list_preference_profiles(self) -> list[SavedPreferencesProfile]:
        return self.preferences_service.list_profiles()

    def save_preference_profile(
        self,
        *,
        name: str,
        content_root: str,
        sort_mode: SortMode,
        theme_mode: str,
        editor_font_size: int,
        source_type: SourceType = "local",
        sftp_host: str = "",
        sftp_port: int = 22,
        sftp_username: str = "",
        sftp_password: str = "",
        sftp_path: str = "/",
        gdrive_folder_id: str = "root",
        gdrive_credentials: str = "",
        autosave_enabled: bool = False,
        image_upload_mode: str = "same_dir",
        image_upload_subdir: str = "assets",
        language: str = "pl",
    ) -> SavedPreferencesProfile:
        return self.preferences_service.create_profile(
            name=name,
            content_root=content_root,
            sort_mode=sort_mode,
            theme_mode=theme_mode,
            editor_font_size=editor_font_size,
            source_type=source_type,
            sftp_host=sftp_host,
            sftp_port=sftp_port,
            sftp_username=sftp_username,
            sftp_password=sftp_password,
            sftp_path=sftp_path,
            gdrive_folder_id=gdrive_folder_id,
            gdrive_credentials=gdrive_credentials,
            autosave_enabled=autosave_enabled,
            image_upload_mode=image_upload_mode,
            image_upload_subdir=image_upload_subdir,
            language=language,
        )

    def update_preference_profile(
        self,
        profile_id: int,
        *,
        name: str,
        content_root: str,
        sort_mode: SortMode,
        theme_mode: str,
        editor_font_size: int,
        source_type: SourceType = "local",
        sftp_host: str = "",
        sftp_port: int = 22,
        sftp_username: str = "",
        sftp_password: str = "",
        sftp_path: str = "/",
        gdrive_folder_id: str = "root",
        gdrive_credentials: str = "",
        autosave_enabled: bool = False,
        image_upload_mode: str = "same_dir",
        image_upload_subdir: str = "assets",
        language: str = "pl",
    ) -> SavedPreferencesProfile:
        return self.preferences_service.update_profile(
            profile_id,
            name=name,
            content_root=content_root,
            sort_mode=sort_mode,
            theme_mode=theme_mode,
            editor_font_size=editor_font_size,
            source_type=source_type,
            sftp_host=sftp_host,
            sftp_port=sftp_port,
            sftp_username=sftp_username,
            sftp_password=sftp_password,
            sftp_path=sftp_path,
            gdrive_folder_id=gdrive_folder_id,
            gdrive_credentials=gdrive_credentials,
            autosave_enabled=autosave_enabled,
            image_upload_mode=image_upload_mode,
            image_upload_subdir=image_upload_subdir,
            language=language,
        )

    def delete_preference_profile(self, profile_id: int) -> None:
        self.preferences_service.delete_profile(profile_id)

    def apply_preference_profile(self, profile_id: int) -> AppPreferences:
        invalidate_sftp_cache()
        return self.preferences_service.apply_profile(profile_id)

    def build_tree(self) -> TreeNode:
        prefs = self.get_preferences()
        backend = build_backend(prefs)
        display = backend.root_display
        root_name = display.rstrip("/").rsplit("/", 1)[-1] or display
        return self._build_directory_node("", root_name, prefs.sort_mode, backend)

    def read_document(self, relative_path: str) -> FileDocument:
        backend = self._get_backend()
        rel = self._get_file_path(relative_path, backend)
        name = Path(rel).name

        if self.is_editable(rel):
            return FileDocument(
                name=name,
                path=relative_path,
                editable=True,
                file_type=self.get_editor_file_type(rel),
                content=backend.read_text(rel),
            )

        preview_kind = self.get_preview_kind(rel)
        if preview_kind is not None:
            return FileDocument(
                name=name,
                path=relative_path,
                editable=False,
                content="",
                previewable=True,
                preview_kind=preview_kind,
                message="This file is available in preview mode.",
            )

        text_content = self._read_small_text_file(rel, backend)
        if text_content is not None:
            return FileDocument(
                name=name,
                path=relative_path,
                editable=True,
                file_type="text",
                content=text_content,
                message="This file is opened as plain text.",
            )

        return FileDocument(
            name=name,
            path=relative_path,
            editable=False,
            content="",
            previewable=False,
            preview_kind=None,
            message="This file is too large, binary, or not supported for editing.",
        )

    def save_document(self, relative_path: str, content: str) -> FileDocument:
        backend = self._get_backend()
        rel = self._get_file_path(relative_path, backend)
        if not self.is_editable(rel) and self.get_preview_kind(rel) is not None:
            raise UnsupportedFileTypeError("Preview-only files cannot be saved from the editor.")
        if not self.is_editable(rel) and self._read_small_text_file(rel, backend) is None:
            raise UnsupportedFileTypeError("Only Markdown, JSON, and small text files can be saved.")
        backend.write_text(rel, content)
        return self.read_document(relative_path)

    def get_document_path(self, relative_path: str) -> str:
        return self._get_file_path(relative_path, self._get_backend())

    def get_local_path(self, relative_path: str) -> tuple[Path, bool]:
        return self._get_backend().get_as_local_path(relative_path)

    def create_item(self, parent_path: str, name: str, kind: str) -> CreatedItem:
        backend = self._get_backend()
        parent_rel = self._resolve_dir_path(parent_path, backend)

        normalized_name = self._normalize_item_name(name, kind)
        target_rel = f"{parent_rel}/{normalized_name}" if parent_rel else normalized_name

        if backend.exists(target_rel):
            raise ItemAlreadyExistsError("An item with this name already exists.")

        if kind == "directory":
            backend.create_dir(target_rel)
        else:
            backend.create_file(target_rel)

        return self._build_item_response(target_rel, backend)

    def rename_item(self, path: str, new_name: str) -> CreatedItem:
        backend = self._get_backend()
        src_rel = self._resolve_path(path, backend)
        kind = "directory" if backend.is_dir(src_rel) else "file"
        normalized = self._normalize_item_name(new_name, kind)
        parent_rel = str(Path(src_rel).parent)
        if parent_rel == ".":
            parent_rel = ""
        dst_rel = f"{parent_rel}/{normalized}" if parent_rel else normalized
        if backend.exists(dst_rel):
            raise ItemAlreadyExistsError(f"Item '{normalized}' already exists.")
        backend.rename(src_rel, dst_rel)
        return self._build_item_response(dst_rel, backend)

    def delete_item(self, path: str) -> None:
        backend = self._get_backend()
        rel = self._resolve_path(path, backend)
        backend.delete(rel)

    def move_item(self, source_path: str, target_parent_path: str) -> CreatedItem:
        backend = self._get_backend()
        src_rel = self._resolve_path(source_path, backend)
        target_parent_rel = self._resolve_dir_path(target_parent_path, backend)

        src_name = Path(src_rel).name
        src_parent = str(Path(src_rel).parent)
        if src_parent == ".":
            src_parent = ""

        if src_parent == target_parent_rel:
            return self._build_item_response(src_rel, backend)

        if backend.is_dir(src_rel) and self._is_subpath(target_parent_rel, src_rel):
            raise InvalidPathError("A directory cannot be moved into itself or one of its children.")

        dst_rel = f"{target_parent_rel}/{src_name}" if target_parent_rel else src_name
        if backend.exists(dst_rel):
            raise ItemAlreadyExistsError("An item with this name already exists in the target directory.")

        backend.rename(src_rel, dst_rel)

        if self.get_preferences().sort_mode == "manual":
            self._refresh_manual_order(src_parent, backend)
            self._refresh_manual_order(target_parent_rel, backend)

        return self._build_item_response(dst_rel, backend)

    def upload_files(self, parent_path: str, uploads: list[tuple[str, bytes]]) -> UploadItemsResponse:
        backend = self._get_backend()
        parent_rel = self._resolve_dir_path(parent_path, backend)

        created_items: list[CreatedItem] = []
        skipped_items: list[UploadedItemError] = []
        seen_names: set[str] = set()

        for original_name, content in uploads:
            try:
                normalized_name = self._normalize_uploaded_name(original_name)
            except InvalidPathError as exc:
                skipped_items.append(UploadedItemError(name=original_name or "(unnamed)", message=str(exc)))
                continue

            if normalized_name in seen_names:
                skipped_items.append(UploadedItemError(
                    name=normalized_name,
                    message="This upload batch already contains a file with the same name.",
                ))
                continue
            seen_names.add(normalized_name)

            target_rel = f"{parent_rel}/{normalized_name}" if parent_rel else normalized_name
            if backend.exists(target_rel):
                skipped_items.append(UploadedItemError(
                    name=normalized_name,
                    message="An item with this name already exists in the target directory.",
                ))
                continue

            backend.write_bytes(target_rel, content)
            created_items.append(self._build_item_response(target_rel, backend))

        if self.get_preferences().sort_mode == "manual" and created_items:
            self._refresh_manual_order(parent_rel, backend)

        return UploadItemsResponse(
            parent_path=parent_path,
            created_items=created_items,
            skipped_items=skipped_items,
        )

    def reorder_items(self, parent_path: str, ordered_paths: list[str]) -> AppPreferences:
        preferences = self.get_preferences()
        if preferences.sort_mode != "manual":
            raise InvalidPathError("Manual order is available only in manual sort mode.")

        backend = self._get_backend()
        parent_rel = self._resolve_dir_path(parent_path, backend)

        existing_paths = {entry.relative_path for entry in backend.list_children(parent_rel)}
        if existing_paths != set(ordered_paths) or len(existing_paths) != len(ordered_paths):
            raise InvalidPathError("Ordered paths must match the current directory contents exactly.")

        self.preferences_repository.set_manual_order(parent_path, ordered_paths)
        return self.get_preferences()

    def browse_directories(self, directory_path: str | None = None) -> DirectoryBrowserResponse:
        result = self._get_backend().browse_dirs(directory_path)
        return DirectoryBrowserResponse(
            current_path=result.current_path,
            parent_path=result.parent_path,
            directories=[DirectoryOption(name=name, path=path) for name, path in result.directories],
        )

    def create_browsed_directory(self, parent_path: str, name: str) -> DirectoryBrowserResponse:
        normalized_name = name.strip()
        if not normalized_name:
            raise InvalidPathError("Directory name cannot be empty.")
        if Path(normalized_name).name != normalized_name or normalized_name in {".", ".."}:
            raise InvalidPathError("Directory name is invalid.")

        target_parent = Path(parent_path).expanduser().resolve()
        if not target_parent.exists() or not target_parent.is_dir():
            raise InvalidPathError("Selected parent directory does not exist.")

        target = target_parent / normalized_name
        if target.exists():
            raise ItemAlreadyExistsError("A directory with this name already exists.")

        try:
            target.mkdir()
        except PermissionError as exc:
            raise InvalidPathError("Cannot create a directory in this location.") from exc
        except OSError as exc:
            raise InvalidPathError(f"Cannot create directory: {exc.strerror or 'unknown error'}") from exc

        return self.browse_directories(str(target))

    def prepare_download(self, relative_path: str) -> tuple[Path, str, bool]:
        backend = self._get_backend()
        rel = self._resolve_path(relative_path, backend)

        if backend.is_file(rel):
            local_path, is_temp = backend.get_as_local_path(rel)
            return local_path, Path(rel).name, is_temp

        temp_file = tempfile.NamedTemporaryFile(prefix="noteeli-download-", suffix=".zip", delete=False)
        temp_path = Path(temp_file.name)
        temp_file.close()

        dir_name = Path(rel).name if rel else "noteeli"
        all_files = backend.rglob_files(rel)
        parent_rel = str(Path(rel).parent) if rel else ""
        if parent_rel == ".":
            parent_rel = ""

        with zipfile.ZipFile(temp_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for file_rel in all_files:
                content = backend.read_bytes(file_rel)
                if parent_rel:
                    arcname = file_rel[len(parent_rel):].lstrip("/")
                else:
                    arcname = file_rel
                archive.writestr(arcname, content)

        return temp_path, f"{dir_name}.zip", True

    def resolve_embedded_asset(self, source_document_path: str, asset_reference: str) -> tuple[str, str]:
        backend = self._get_backend()
        source_rel = self._get_file_path(source_document_path, backend)
        normalized_reference = self._normalize_asset_reference(asset_reference)
        if not normalized_reference:
            raise InvalidPathError("Embedded asset reference is empty.")

        if normalized_reference.startswith("/"):
            base_rel = normalized_reference.lstrip("/")
        else:
            doc_dir = str(Path(source_rel).parent)
            if doc_dir == ".":
                doc_dir = ""
            base_rel = self._join_paths(doc_dir, normalized_reference)

        candidate_rels = [base_rel]
        if base_rel.endswith(".excalidraw"):
            stem = base_rel[:-len(".excalidraw")]
            candidate_rels.extend([
                f"{base_rel}.png", f"{base_rel}.svg",
                f"{stem}.png", f"{stem}.svg",
                f"{stem}.jpg", f"{stem}.jpeg", f"{stem}.webp",
            ])

        for candidate in candidate_rels:
            safe = self._sanitize_path(candidate)
            if safe is None:
                continue
            if not backend.exists(safe) or not backend.is_file(safe):
                continue
            preview_kind = self.get_preview_kind(safe)
            if preview_kind is not None:
                return safe, preview_kind

        safe_base = self._sanitize_path(base_rel)
        if safe_base is not None and backend.exists(safe_base):
            raise UnsupportedFileTypeError("This embedded asset type is not available in preview mode.")
        raise DocumentNotFoundError("Embedded asset does not exist.")

    def is_editable(self, path: str) -> bool:
        suffix = Path(path).suffix.lower()
        return (
            suffix in self.settings.allowed_markdown_extensions
            or suffix in self.JSON_EXTENSIONS
        )

    def is_openable_from_tree(self, path: str) -> bool:
        return self.is_editable(path) or self.get_preview_kind(path) is None

    def get_editor_file_type(self, path: str) -> str:
        if self.is_json(path):
            return "json"
        if Path(path).suffix.lower() in self.settings.allowed_markdown_extensions:
            return "markdown"
        return "text"

    def is_json(self, path: str) -> bool:
        return Path(path).suffix.lower() in self.JSON_EXTENSIONS

    def get_preview_kind(self, path: str) -> str | None:
        suffix = Path(path).suffix.lower()
        if suffix in self.IMAGE_EXTENSIONS:
            return "image"
        if suffix in self.PDF_EXTENSIONS:
            return "pdf"
        return None

    def is_small_text_file(self, path: str, backend: StorageBackend) -> bool:
        return self._read_small_text_file(path, backend) is not None

    def _read_small_text_file(self, path: str, backend: StorageBackend) -> str | None:
        try:
            content = backend.read_bytes(path)
        except Exception:
            return None
        if len(content) > self.MAX_TEXT_FILE_BYTES or b"\x00" in content:
            return None
        try:
            return content.decode("utf-8")
        except UnicodeDecodeError:
            return None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_file_path(self, relative_path: str, backend: StorageBackend) -> str:
        rel = self._resolve_path(relative_path, backend)
        if not backend.is_file(rel):
            raise DocumentNotFoundError("Document does not exist.")
        return rel

    def _resolve_dir_path(self, relative_path: str, backend: StorageBackend) -> str:
        if not relative_path:
            return ""
        rel = self._resolve_path(relative_path, backend)
        if not backend.is_dir(rel):
            raise InvalidPathError("The selected path is not a directory.")
        return rel

    def _resolve_path(self, relative_path: str, backend: StorageBackend) -> str:
        if not relative_path:
            raise InvalidPathError("A file path is required.")
        sanitized = self._sanitize_path(relative_path)
        if sanitized is None:
            raise InvalidPathError("Path escapes the configured content root.")
        if not backend.exists(sanitized):
            raise DocumentNotFoundError("Document does not exist.")
        return sanitized

    @staticmethod
    def _sanitize_path(path: str) -> str | None:
        parts = path.replace("\\", "/").split("/")
        normalized = []
        for part in parts:
            if part == "..":
                return None
            if part and part != ".":
                normalized.append(part)
        return "/".join(normalized)

    @staticmethod
    def _join_paths(base: str, rel: str) -> str:
        parts = (base + "/" + rel).split("/")
        normalized: list[str] = []
        for part in parts:
            if part == "..":
                if normalized:
                    normalized.pop()
            elif part and part != ".":
                normalized.append(part)
        return "/".join(normalized)

    def _build_directory_node(
        self,
        relative_path: str,
        name: str,
        sort_mode: SortMode,
        backend: StorageBackend,
    ) -> TreeNode:
        children: list[TreeNode] = []
        entries = backend.list_children(relative_path)
        sorted_entries = self._sort_entries(entries, relative_path, sort_mode)

        for entry in sorted_entries:
            if entry.is_dir and not entry.is_symlink:
                children.append(
                    self._build_directory_node(entry.relative_path, entry.name, sort_mode, backend)
                )
            else:
                children.append(TreeNode(
                    name=entry.name,
                    path=entry.relative_path,
                    kind="file",
                    editable=self.is_openable_from_tree(entry.relative_path),
                    symlink=entry.is_symlink,
                ))

        return TreeNode(name=name, path=relative_path, kind="directory", children=children, editable=False)

    def _build_item_response(self, relative_path: str, backend: StorageBackend) -> CreatedItem:
        return CreatedItem(
            name=Path(relative_path).name,
            path=relative_path,
            kind="directory" if backend.is_dir(relative_path) else "file",
            editable=backend.is_file(relative_path) and self.is_openable_from_tree(relative_path),
        )

    def _sort_entries(
        self,
        entries: list[StorageEntry],
        parent_rel: str,
        sort_mode: SortMode,
    ) -> list[StorageEntry]:
        if sort_mode != "manual":
            return sorted(entries, key=lambda e: (0 if e.is_dir and not e.is_symlink else 1, e.name.lower()))

        order_map = self.preferences_repository.get_manual_order(parent_rel)
        unordered_offset = len(order_map) + 1000
        return sorted(
            entries,
            key=lambda e: (order_map.get(e.relative_path, unordered_offset), e.name.lower()),
        )

    def _refresh_manual_order(self, parent_rel: str, backend: StorageBackend) -> None:
        if not backend.is_dir(parent_rel if parent_rel else ""):
            return
        entries = backend.list_children(parent_rel)
        sorted_entries = self._sort_entries(entries, parent_rel, "manual")
        self.preferences_repository.set_manual_order(parent_rel, [e.relative_path for e in sorted_entries])

    def _normalize_item_name(self, name: str, kind: str) -> str:
        candidate = name.strip()
        if not candidate:
            raise InvalidPathError("A name is required.")
        if candidate in {".", ".."} or "/" in candidate or "\\" in candidate:
            raise InvalidPathError("The item name contains unsupported path separators.")
        known_extensions = set(self.settings.allowed_markdown_extensions) | self.JSON_EXTENSIONS
        if kind == "file" and not any(
            candidate.lower().endswith(ext) for ext in known_extensions
        ):
            candidate = f"{candidate}.md"
        return candidate

    @staticmethod
    def _normalize_uploaded_name(name: str) -> str:
        candidate = Path(name.strip()).name
        if not candidate or candidate in {".", ".."}:
            raise InvalidPathError("The uploaded file name is invalid.")
        if "/" in candidate or "\\" in candidate:
            raise InvalidPathError("The uploaded file name contains unsupported path separators.")
        return candidate

    @staticmethod
    def _is_subpath(potential_child: str, parent: str) -> bool:
        return potential_child == parent or potential_child.startswith(parent + "/")

    @staticmethod
    def _normalize_asset_reference(asset_reference: str) -> str:
        candidate = asset_reference.strip()
        if candidate.startswith("<") and candidate.endswith(">"):
            candidate = candidate[1:-1]
        if "|" in candidate:
            candidate = candidate.split("|", 1)[0]
        if "#" in candidate:
            candidate = candidate.split("#", 1)[0]
        return candidate.strip()
