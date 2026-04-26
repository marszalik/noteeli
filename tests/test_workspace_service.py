from pathlib import Path
import zipfile

import pytest

from app.core.config import Settings
from app.domains.workspace.service import (
    ItemAlreadyExistsError,
    InvalidPathError,
    UnsupportedFileTypeError,
    WorkspaceService,
)


def build_service(root: Path) -> WorkspaceService:
    settings = Settings(
        content_root=root,
        data_dir=root.parent / ".noteeli",
        session_secret="test-secret",
        google_client_id="",
        google_client_secret="",
    )
    return WorkspaceService(settings)


def test_build_tree_keeps_directory_hierarchy(tmp_path: Path):
    notes = tmp_path / "vault"
    nested = notes / "projekty"
    nested.mkdir(parents=True)
    (notes / "README.md").write_text("# Start\n", encoding="utf-8")
    (nested / "plan.md").write_text("## Plan\n", encoding="utf-8")
    (notes / "image.png").write_bytes(b"png")

    service = build_service(notes)
    tree = service.build_tree()

    assert tree.kind == "directory"
    assert [child.name for child in tree.children] == ["projekty", "image.png", "README.md"]
    assert tree.children[0].children[0].path == "projekty/plan.md"
    assert tree.children[1].editable is False
    assert tree.children[2].editable is True


def test_save_document_updates_markdown_file(tmp_path: Path):
    notes = tmp_path / "vault"
    notes.mkdir()
    target = notes / "todo.md"
    target.write_text("stara tresc", encoding="utf-8")

    service = build_service(notes)
    document = service.save_document("todo.md", "nowa tresc")

    assert target.read_text(encoding="utf-8") == "nowa tresc"
    assert document.content == "nowa tresc"
    assert document.editable is True


def test_path_traversal_is_blocked(tmp_path: Path):
    notes = tmp_path / "vault"
    notes.mkdir()
    outside = tmp_path / "outside.md"
    outside.write_text("sekret", encoding="utf-8")

    service = build_service(notes)

    with pytest.raises(InvalidPathError):
        service.read_document("../outside.md")


def test_non_markdown_file_cannot_be_saved(tmp_path: Path):
    notes = tmp_path / "vault"
    notes.mkdir()
    binary = notes / "archive.zip"
    binary.write_bytes(b"PK\x00\x01")

    service = build_service(notes)

    with pytest.raises(UnsupportedFileTypeError):
        service.save_document("archive.zip", "nope")


def test_unknown_text_file_opens_and_saves_as_plain_text(tmp_path: Path):
    notes = tmp_path / "vault"
    notes.mkdir()
    target = notes / "config.env"
    target.write_text("A=1\n", encoding="utf-8")

    service = build_service(notes)
    document = service.read_document("config.env")

    assert document.editable is True
    assert document.file_type == "text"
    assert document.content == "A=1\n"

    service.save_document("config.env", "A=2\n")
    assert target.read_text(encoding="utf-8") == "A=2\n"


def test_create_directory_and_markdown_file(tmp_path: Path):
    notes = tmp_path / "vault"
    notes.mkdir()

    service = build_service(notes)
    created_directory = service.create_item("", "Projekty", "directory")
    created_file = service.create_item("Projekty", "Plan", "file")

    assert created_directory.path == "Projekty"
    assert created_directory.kind == "directory"
    assert created_file.path == "Projekty/Plan.md"
    assert created_file.editable is True
    assert (notes / "Projekty").is_dir()
    assert (notes / "Projekty" / "Plan.md").is_file()


def test_create_item_rejects_duplicates(tmp_path: Path):
    notes = tmp_path / "vault"
    notes.mkdir()
    (notes / "duplikat.md").write_text("", encoding="utf-8")

    service = build_service(notes)

    with pytest.raises(ItemAlreadyExistsError):
        service.create_item("", "duplikat.md", "file")


def test_move_item_to_another_directory(tmp_path: Path):
    notes = tmp_path / "vault"
    notes.mkdir()
    (notes / "todo.md").write_text("", encoding="utf-8")
    (notes / "archiwum").mkdir()

    service = build_service(notes)
    moved = service.move_item("todo.md", "archiwum")

    assert moved.path == "archiwum/todo.md"
    assert moved.kind == "file"
    assert (notes / "archiwum" / "todo.md").is_file()
    assert not (notes / "todo.md").exists()


def test_move_directory_into_child_is_blocked(tmp_path: Path):
    notes = tmp_path / "vault"
    notes.mkdir()
    (notes / "projekty" / "aktywny").mkdir(parents=True)

    service = build_service(notes)

    with pytest.raises(InvalidPathError):
        service.move_item("projekty", "projekty/aktywny")


def test_manual_order_is_persisted_in_sqlite(tmp_path: Path):
    notes = tmp_path / "vault"
    notes.mkdir()
    (notes / "a.md").write_text("a", encoding="utf-8")
    (notes / "b.md").write_text("b", encoding="utf-8")
    (notes / "c.md").write_text("c", encoding="utf-8")

    service = build_service(notes)
    preferences = service.update_preferences(str(notes), "manual", "dark", 19)

    assert preferences.sort_mode == "manual"
    assert preferences.theme_mode == "dark"
    assert preferences.editor_font_size == 19

    service.reorder_items("", ["a.md", "c.md", "b.md"])
    tree = service.build_tree()

    assert [child.name for child in tree.children] == ["a.md", "c.md", "b.md"]


def test_browse_directories_returns_sorted_subdirectories(tmp_path: Path):
    notes = tmp_path / "vault"
    notes.mkdir()
    (notes / "zeta").mkdir()
    (notes / "alfa").mkdir()
    (notes / "plik.md").write_text("", encoding="utf-8")

    service = build_service(notes)
    browser = service.browse_directories(str(notes))

    assert browser.current_path == str(notes.resolve())
    assert browser.parent_path == str(notes.parent.resolve())
    assert [directory.name for directory in browser.directories] == ["alfa", "zeta"]


def test_browse_directories_rejects_file_path(tmp_path: Path):
    notes = tmp_path / "vault"
    notes.mkdir()
    file_path = notes / "todo.md"
    file_path.write_text("", encoding="utf-8")

    service = build_service(notes)

    with pytest.raises(InvalidPathError):
        service.browse_directories(str(file_path))


def test_read_document_returns_image_preview_metadata(tmp_path: Path):
    notes = tmp_path / "vault"
    notes.mkdir()
    image = notes / "cover.png"
    image.write_bytes(b"png")

    service = build_service(notes)
    document = service.read_document("cover.png")

    assert document.editable is False
    assert document.previewable is True
    assert document.preview_kind == "image"


def test_read_document_returns_pdf_preview_metadata(tmp_path: Path):
    notes = tmp_path / "vault"
    notes.mkdir()
    pdf = notes / "guide.pdf"
    pdf.write_bytes(b"%PDF-1.7")

    service = build_service(notes)
    document = service.read_document("guide.pdf")

    assert document.editable is False
    assert document.previewable is True
    assert document.preview_kind == "pdf"


def test_resolve_embedded_asset_for_relative_image(tmp_path: Path):
    notes = tmp_path / "vault" / "notes"
    notes.mkdir(parents=True)
    source = notes / "entry.md"
    source.write_text("![img](../assets/photo.png)", encoding="utf-8")
    asset = notes.parent / "assets" / "photo.png"
    asset.parent.mkdir()
    asset.write_bytes(b"png")

    service = build_service(notes)
    resolved_path, preview_kind = service.resolve_embedded_asset("entry.md", "../assets/photo.png")

    assert resolved_path == asset.resolve()
    assert preview_kind == "image"


def test_resolve_embedded_asset_uses_excalidraw_export_when_available(tmp_path: Path):
    notes = tmp_path / "vault" / "notes"
    notes.mkdir(parents=True)
    source = notes / "journal.md"
    source.write_text("![[../Excalidraw/Drawing.excalidraw]]", encoding="utf-8")
    excalidraw = notes.parent / "Excalidraw" / "Drawing.excalidraw"
    excalidraw.parent.mkdir()
    excalidraw.write_text("{}", encoding="utf-8")
    exported_image = excalidraw.with_suffix(".png")
    exported_image.write_bytes(b"png")

    service = build_service(notes)
    resolved_path, preview_kind = service.resolve_embedded_asset("journal.md", "../Excalidraw/Drawing.excalidraw")

    assert resolved_path == exported_image.resolve()
    assert preview_kind == "image"


def test_upload_files_creates_multiple_items_and_skips_duplicates(tmp_path: Path):
    notes = tmp_path / "vault"
    notes.mkdir()
    (notes / "existing.png").write_bytes(b"old")

    service = build_service(notes)
    result = service.upload_files(
        "",
        [
            ("photo.png", b"png"),
            ("existing.png", b"new"),
            ("photo.png", b"dup"),
        ],
    )

    assert [item.path for item in result.created_items] == ["photo.png"]
    assert len(result.skipped_items) == 2
    assert (notes / "photo.png").read_bytes() == b"png"
    assert (notes / "existing.png").read_bytes() == b"old"


def test_prepare_download_returns_zip_for_directory(tmp_path: Path):
    notes = tmp_path / "vault"
    notes.mkdir()
    target_dir = notes / "assets"
    target_dir.mkdir()
    (target_dir / "cover.png").write_bytes(b"png")

    service = build_service(notes)
    archive_path, filename, is_temporary = service.prepare_download("assets")

    assert is_temporary is True
    assert filename == "assets.zip"
    assert archive_path.exists()
    with zipfile.ZipFile(archive_path) as archive:
        assert "assets/cover.png" in archive.namelist()


def test_prepare_download_returns_original_file_for_regular_file(tmp_path: Path):
    notes = tmp_path / "vault"
    notes.mkdir()
    target_file = notes / "note.md"
    target_file.write_text("hello", encoding="utf-8")

    service = build_service(notes)
    download_path, filename, is_temporary = service.prepare_download("note.md")

    assert is_temporary is False
    assert filename == "note.md"
    assert download_path == target_file
