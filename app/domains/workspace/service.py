import tempfile
import zipfile
from pathlib import Path

from app.core.config import Settings, get_settings
from app.domains.preferences.repository import PreferencesRepository
from app.domains.preferences.schemas import AppPreferences, SortMode
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

    def __init__(
        self,
        settings: Settings | None = None,
        preferences_repository: PreferencesRepository | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.preferences_repository = preferences_repository or PreferencesRepository(self.settings)
        self.preferences_service = PreferencesService(self.settings, self.preferences_repository)
        self.preferences_service.get_preferences()

    @property
    def root_path(self) -> Path:
        return Path(self.get_preferences().content_root)

    def get_preferences(self) -> AppPreferences:
        return self.preferences_service.get_preferences()

    def update_preferences(
        self,
        content_root: str,
        sort_mode: SortMode,
        theme_mode: str,
        editor_font_size: int,
    ) -> AppPreferences:
        return self.preferences_service.update_preferences(
            content_root,
            sort_mode,
            theme_mode,
            editor_font_size,
        )

    def build_tree(self) -> TreeNode:
        preferences = self.get_preferences()
        root_name = self.root_path.name or str(self.root_path)
        return self._build_directory_node(
            self.root_path,
            root_name,
            "",
            preferences.sort_mode,
        )

    def read_document(self, relative_path: str) -> FileDocument:
        path = self.get_document_path(relative_path)
        if self.is_editable(path):
            return FileDocument(
                name=path.name,
                path=relative_path,
                editable=True,
                content=path.read_text(encoding="utf-8"),
            )

        preview_kind = self.get_preview_kind(path)
        if preview_kind is not None:
            return FileDocument(
                name=path.name,
                path=relative_path,
                editable=False,
                content="",
                previewable=True,
                preview_kind=preview_kind,
                message="Ten plik jest dostepny w trybie podgladu.",
            )

        return FileDocument(
            name=path.name,
            path=relative_path,
            editable=False,
            content="",
            previewable=False,
            preview_kind=None,
            message="Ten typ pliku nie jest obslugiwany. Edytor zapisuje tylko Markdown.",
        )

    def save_document(self, relative_path: str, content: str) -> FileDocument:
        path = self.get_document_path(relative_path)
        if not self.is_editable(path):
            raise UnsupportedFileTypeError("Only Markdown files can be saved.")

        path.write_text(content, encoding="utf-8")
        return self.read_document(relative_path)

    def create_item(self, parent_path: str, name: str, kind: str) -> CreatedItem:
        parent = self.root_path if not parent_path else self._resolve_path(parent_path)
        if not parent.is_dir():
            raise InvalidPathError("The selected parent path is not a directory.")

        normalized_name = self._normalize_item_name(name, kind)
        target = parent / normalized_name
        if target.exists():
            raise ItemAlreadyExistsError("An item with this name already exists.")

        if kind == "directory":
            target.mkdir(parents=False, exist_ok=False)
        else:
            target.write_text("", encoding="utf-8")

        relative_target = target.relative_to(self.root_path).as_posix()
        return CreatedItem(
            name=target.name,
            path=relative_target,
            kind=kind,
            editable=kind == "file" and self.is_editable(target),
        )

    def move_item(self, source_path: str, target_parent_path: str) -> CreatedItem:
        source = self._resolve_path(source_path)
        target_parent = self.root_path if not target_parent_path else self._resolve_path(target_parent_path)

        if not target_parent.is_dir():
            raise InvalidPathError("The target parent path is not a directory.")
        if source == self.root_path:
            raise InvalidPathError("The content root cannot be moved.")
        if source.parent == target_parent:
            return self._build_item_response(source)

        if source.is_dir() and self._is_relative_to(target_parent, source):
            raise InvalidPathError("A directory cannot be moved into itself or one of its children.")

        destination = target_parent / source.name
        if destination.exists():
            raise ItemAlreadyExistsError("An item with this name already exists in the target directory.")

        previous_parent = source.parent
        source.rename(destination)

        if self.get_preferences().sort_mode == "manual":
            self._refresh_manual_order(previous_parent)
            self._refresh_manual_order(target_parent)

        return self._build_item_response(destination)

    def upload_files(self, parent_path: str, uploads: list[tuple[str, bytes]]) -> UploadItemsResponse:
        parent = self.root_path if not parent_path else self._resolve_path(parent_path)
        if not parent.is_dir():
            raise InvalidPathError("The selected parent path is not a directory.")

        created_items: list[CreatedItem] = []
        skipped_items: list[UploadedItemError] = []
        seen_names: set[str] = set()

        for original_name, content in uploads:
            try:
                normalized_name = self._normalize_uploaded_name(original_name)
            except InvalidPathError as exc:
                skipped_items.append(UploadedItemError(name=original_name or "(brak nazwy)", message=str(exc)))
                continue

            if normalized_name in seen_names:
                skipped_items.append(
                    UploadedItemError(
                        name=normalized_name,
                        message="This upload batch already contains a file with the same name.",
                    )
                )
                continue
            seen_names.add(normalized_name)

            target = parent / normalized_name
            if target.exists():
                skipped_items.append(
                    UploadedItemError(
                        name=normalized_name,
                        message="An item with this name already exists in the target directory.",
                    )
                )
                continue

            target.write_bytes(content)
            created_items.append(self._build_item_response(target))

        if self.get_preferences().sort_mode == "manual" and created_items:
            self._refresh_manual_order(parent)

        return UploadItemsResponse(
            parent_path=parent_path,
            created_items=created_items,
            skipped_items=skipped_items,
        )

    def reorder_items(self, parent_path: str, ordered_paths: list[str]) -> AppPreferences:
        preferences = self.get_preferences()
        if preferences.sort_mode != "manual":
            raise InvalidPathError("Manual order is available only in manual sort mode.")

        parent = self.root_path if not parent_path else self._resolve_path(parent_path)
        if not parent.is_dir():
            raise InvalidPathError("The selected parent path is not a directory.")

        existing_paths = [
            child.relative_to(self.root_path).as_posix()
            for child in parent.iterdir()
        ]
        if set(existing_paths) != set(ordered_paths) or len(existing_paths) != len(ordered_paths):
            raise InvalidPathError("Ordered paths must match the current directory contents exactly.")

        self.preferences_repository.set_manual_order(parent_path, ordered_paths)
        return self.get_preferences()

    def browse_directories(self, directory_path: str | None = None) -> DirectoryBrowserResponse:
        if directory_path:
            current = Path(directory_path).expanduser().resolve()
        else:
            current = self.root_path

        if not current.exists():
            raise DocumentNotFoundError("Directory does not exist.")
        if not current.is_dir():
            raise InvalidPathError("The selected path is not a directory.")

        directories: list[DirectoryOption] = []
        try:
            children = sorted(
                (child for child in current.iterdir() if child.is_dir()),
                key=lambda child: child.name.lower(),
            )
        except PermissionError as exc:
            raise InvalidPathError("This directory cannot be read.") from exc

        for child in children:
            directories.append(
                DirectoryOption(
                    name=child.name,
                    path=str(child.resolve()),
                )
            )

        parent_path = str(current.parent.resolve()) if current.parent != current else None
        return DirectoryBrowserResponse(
            current_path=str(current),
            parent_path=parent_path,
            directories=directories,
        )

    def prepare_download(self, relative_path: str) -> tuple[Path, str, bool]:
        source = self._resolve_path(relative_path)
        if source.is_file():
            return source, source.name, False

        temp_file = tempfile.NamedTemporaryFile(prefix="noteeli-download-", suffix=".zip", delete=False)
        temp_path = Path(temp_file.name)
        temp_file.close()

        with zipfile.ZipFile(temp_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for child in source.rglob("*"):
                archive.write(child, arcname=child.relative_to(source.parent))

        return temp_path, f"{source.name}.zip", True

    def is_editable(self, path: Path) -> bool:
        return path.suffix.lower() in self.settings.allowed_markdown_extensions

    def get_preview_kind(self, path: Path) -> str | None:
        suffix = path.suffix.lower()
        if suffix in self.IMAGE_EXTENSIONS:
            return "image"
        if suffix in self.PDF_EXTENSIONS:
            return "pdf"
        return None

    def resolve_embedded_asset(self, source_document_path: str, asset_reference: str) -> tuple[Path, str]:
        source_document = self.get_document_path(source_document_path)
        normalized_reference = self._normalize_asset_reference(asset_reference)
        if not normalized_reference:
            raise InvalidPathError("Embedded asset reference is empty.")

        if normalized_reference.startswith("/"):
            base_candidate = (self.root_path / normalized_reference.lstrip("/")).resolve()
        else:
            base_candidate = (source_document.parent / normalized_reference).resolve()

        candidate_paths = [base_candidate]
        if base_candidate.suffix.lower() == ".excalidraw":
            stem_candidate = base_candidate.with_suffix("")
            candidate_paths.extend(
                [
                    Path(f"{base_candidate}.png"),
                    Path(f"{base_candidate}.svg"),
                    stem_candidate.with_suffix(".png"),
                    stem_candidate.with_suffix(".svg"),
                    stem_candidate.with_suffix(".jpg"),
                    stem_candidate.with_suffix(".jpeg"),
                    stem_candidate.with_suffix(".webp"),
                ]
            )

        for candidate in candidate_paths:
            self._ensure_embedded_asset_in_allowed_roots(candidate)
            if not candidate.exists() or not candidate.is_file():
                continue

            preview_kind = self.get_preview_kind(candidate)
            if preview_kind is not None:
                return candidate, preview_kind

        if base_candidate.exists():
            raise UnsupportedFileTypeError("This embedded asset type is not available in preview mode.")
        raise DocumentNotFoundError("Embedded asset does not exist.")

    def _build_directory_node(
        self,
        directory: Path,
        name: str,
        relative_path: str,
        sort_mode: SortMode,
    ) -> TreeNode:
        children: list[TreeNode] = []
        for child in self._sorted_children(directory, relative_path, sort_mode):
            child_relative = child.relative_to(self.root_path).as_posix()
            is_directory = child.is_dir(follow_symlinks=False)
            is_symlink = child.is_symlink()

            if is_directory and not is_symlink:
                children.append(
                    self._build_directory_node(
                        child,
                        child.name,
                        child_relative,
                        sort_mode,
                    )
                )
                continue

            children.append(
                TreeNode(
                    name=child.name,
                    path=child_relative,
                    kind="file",
                    editable=self.is_editable(child),
                    symlink=is_symlink,
                )
            )

        return TreeNode(
            name=name,
            path=relative_path,
            kind="directory",
            children=children,
            editable=False,
        )

    def _resolve_file_path(self, relative_path: str) -> Path:
        candidate = self._resolve_path(relative_path)
        if not candidate.is_file():
            raise DocumentNotFoundError("Document does not exist.")
        return candidate

    def get_document_path(self, relative_path: str) -> Path:
        return self._resolve_file_path(relative_path)

    def _resolve_path(self, relative_path: str) -> Path:
        if not relative_path:
            raise InvalidPathError("A file path is required.")

        candidate = (self.root_path / relative_path).resolve()
        try:
            candidate.relative_to(self.root_path)
        except ValueError as exc:
            raise InvalidPathError("Path escapes the configured content root.") from exc

        if not candidate.exists():
            raise DocumentNotFoundError("Document does not exist.")

        return candidate

    def _normalize_item_name(self, name: str, kind: str) -> str:
        candidate = name.strip()
        if not candidate:
            raise InvalidPathError("A name is required.")

        invalid_names = {".", ".."}
        if candidate in invalid_names or "/" in candidate or "\\" in candidate:
            raise InvalidPathError("The item name contains unsupported path separators.")

        if kind == "file" and not any(
            candidate.lower().endswith(extension)
            for extension in self.settings.allowed_markdown_extensions
        ):
            candidate = f"{candidate}.md"

        return candidate

    def _normalize_uploaded_name(self, name: str) -> str:
        candidate = Path(name.strip()).name
        if not candidate or candidate in {".", ".."}:
            raise InvalidPathError("The uploaded file name is invalid.")
        if "/" in candidate or "\\" in candidate:
            raise InvalidPathError("The uploaded file name contains unsupported path separators.")
        return candidate

    def _build_item_response(self, path: Path) -> CreatedItem:
        return CreatedItem(
            name=path.name,
            path=path.relative_to(self.root_path).as_posix(),
            kind="directory" if path.is_dir() else "file",
            editable=path.is_file() and self.is_editable(path),
        )

    def _normalize_asset_reference(self, asset_reference: str) -> str:
        candidate = asset_reference.strip()
        if candidate.startswith("<") and candidate.endswith(">"):
            candidate = candidate[1:-1]
        if "|" in candidate:
            candidate = candidate.split("|", 1)[0]
        if "#" in candidate:
            candidate = candidate.split("#", 1)[0]
        return candidate.strip()

    def _ensure_embedded_asset_in_allowed_roots(self, candidate: Path) -> None:
        content_root = self.root_path.resolve()
        allowed_roots = [content_root]
        if content_root.parent != content_root:
            allowed_roots.append(content_root.parent.resolve())

        if any(self._is_relative_to(candidate, allowed_root) for allowed_root in allowed_roots):
            return
        raise InvalidPathError("Embedded asset path escapes the allowed note roots.")

    def _refresh_manual_order(self, parent: Path) -> None:
        if not parent.exists() or not parent.is_dir():
            return

        parent_relative = "" if parent == self.root_path else parent.relative_to(self.root_path).as_posix()
        ordered_paths = [
            child.relative_to(self.root_path).as_posix()
            for child in self._sorted_children(parent, parent_relative, "manual")
        ]
        self.preferences_repository.set_manual_order(parent_relative, ordered_paths)

    @staticmethod
    def _is_relative_to(path: Path, base: Path) -> bool:
        try:
            path.relative_to(base)
            return True
        except ValueError:
            return False

    @staticmethod
    def _alphabetical_sort_key(path: Path) -> tuple[int, str]:
        is_directory = path.is_dir(follow_symlinks=False) and not path.is_symlink()
        return (0 if is_directory else 1, path.name.lower())

    def _sorted_children(
        self,
        directory: Path,
        parent_relative_path: str,
        sort_mode: SortMode,
    ) -> list[Path]:
        children = list(directory.iterdir())
        if sort_mode != "manual":
            return sorted(children, key=self._alphabetical_sort_key)

        order_map = self.preferences_repository.get_manual_order(parent_relative_path)
        unordered_offset = len(order_map) + 1000
        return sorted(
            children,
            key=lambda child: (
                order_map.get(child.relative_to(self.root_path).as_posix(), unordered_offset),
                child.name.lower(),
            ),
        )
