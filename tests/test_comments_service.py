"""Review comments: sidecar file format + CommentsService against tmp_path."""
from pathlib import Path

import pytest

from app.core.config import Settings
from app.domains.comments.service import (
    CommentAlreadyExistsError,
    CommentNotFoundError,
    CommentsService,
    comments_path_for,
    parse_comments,
    serialize_comments,
    strip_markers,
)
from app.domains.comments.schemas import Comment
from app.domains.workspace.service import (
    DemoReadOnlyError,
    InvalidPathError,
    WorkspaceService,
)


def build_service(root: Path, demo_mode: bool = False) -> CommentsService:
    settings = Settings(
        content_root=root,
        data_dir=root.parent / ".noteeli",
        session_secret="test-secret",
        google_client_id="",
        google_client_secret="",
        demo_mode=demo_mode,
    )
    return CommentsService(WorkspaceService(settings))


SAMPLE = """---
document: article.md
---
## c_a7f3d2
status: open
created: 2026-09-23T20:41:00+02:00

Czy to zdanie nie jest zbyt absolutne?
Sprawdzić, czy dalej konsekwentnie mówimy o braku accepted instrument.

## c_0b1c2d
status: resolved
created: 2026-09-22T10:00:00+02:00

Done.
"""


def test_comments_path_is_a_sibling_with_suffix():
    assert comments_path_for("article.md") == "article_comments.md"
    assert comments_path_for("notes/deep/article.md") == "notes/deep/article_comments.md"
    assert comments_path_for("notes/README.MD") == "notes/README_comments.md"


def test_parse_reads_frontmatter_metadata_and_multiline_body():
    document, comments = parse_comments(SAMPLE)
    assert document == "article.md"
    assert [c.id for c in comments] == ["c_a7f3d2", "c_0b1c2d"]
    first, second = comments
    assert first.status == "open"
    assert first.created == "2026-09-23T20:41:00+02:00"
    assert first.text == (
        "Czy to zdanie nie jest zbyt absolutne?\n"
        "Sprawdzić, czy dalej konsekwentnie mówimy o braku accepted instrument."
    )
    assert second.status == "resolved"
    assert second.text == "Done."


def test_serialize_round_trips_and_matches_the_documented_layout():
    document, comments = parse_comments(SAMPLE)
    assert serialize_comments(document, comments) == SAMPLE
    assert parse_comments(serialize_comments(document, comments)) == (document, comments)


def test_parse_is_tolerant_of_missing_frontmatter_and_stray_prose():
    text = "Some intro nobody asked for.\n\n## c_abcdef\nstatus: open\nnote: kept as body\n\nBody line.\n"
    document, comments = parse_comments(text)
    assert document == ""
    assert len(comments) == 1
    assert comments[0].status == "open"
    assert comments[0].created == ""
    # An unknown key is not metadata — it's the first body line.
    assert comments[0].text == "note: kept as body\n\nBody line."


def test_strip_markers_removes_range_fences_only():
    md = "A <!--comment:c_a7f3d2:start-->ranged<!--comment:c_a7f3d2:end--> word <!-- keep -->."
    assert strip_markers(md) == "A ranged word <!-- keep -->."


def test_add_comment_creates_sidecar_next_to_the_note(tmp_path: Path):
    notes = tmp_path / "vault"
    (notes / "docs").mkdir(parents=True)
    (notes / "docs" / "article.md").write_text("# Article\n", encoding="utf-8")
    service = build_service(notes)

    result = service.add_comment("docs/article.md", "Too absolute?", "c_a7f3d2")

    sidecar = notes / "docs" / "article_comments.md"
    assert result.exists is True
    assert result.comments_path == "docs/article_comments.md"
    assert [c.id for c in result.comments] == ["c_a7f3d2"]
    text = sidecar.read_text(encoding="utf-8")
    assert text.startswith("---\ndocument: article.md\n---\n## c_a7f3d2\nstatus: open\ncreated: ")
    assert text.rstrip().endswith("Too absolute?")
    # A generated id is used when the client does not send one.
    generated = service.add_comment("docs/article.md", "Second")
    assert len(generated.comments) == 2
    assert generated.comments[1].id.startswith("c_") and generated.comments[1].id != "c_a7f3d2"


def test_list_comments_without_sidecar_is_empty_not_an_error(tmp_path: Path):
    notes = tmp_path / "vault"
    notes.mkdir()
    (notes / "note.md").write_text("hello", encoding="utf-8")
    result = build_service(notes).list_comments("note.md")
    assert result.exists is False
    assert result.comments == []
    assert result.comments_path == "note_comments.md"


def test_update_resolve_and_delete(tmp_path: Path):
    notes = tmp_path / "vault"
    notes.mkdir()
    (notes / "note.md").write_text("hello", encoding="utf-8")
    service = build_service(notes)
    service.add_comment("note.md", "first", "c_111111")
    service.add_comment("note.md", "second", "c_222222")

    edited = service.update_comment("note.md", "c_111111", text="first (edited)")
    assert edited.comments[0].text == "first (edited)"
    assert edited.comments[0].status == "open"

    resolved = service.update_comment("note.md", "c_111111", status="resolved")
    assert resolved.comments[0].status == "resolved"
    assert "status: resolved" in (notes / "note_comments.md").read_text(encoding="utf-8")

    after_delete = service.delete_comment("note.md", "c_111111")
    assert [c.id for c in after_delete.comments] == ["c_222222"]
    assert after_delete.exists is True

    # Deleting the last comment removes the sidecar entirely.
    final = service.delete_comment("note.md", "c_222222")
    assert final.exists is False
    assert not (notes / "note_comments.md").exists()


def test_errors_for_missing_comment_duplicate_id_and_bad_targets(tmp_path: Path):
    notes = tmp_path / "vault"
    notes.mkdir()
    (notes / "note.md").write_text("hello", encoding="utf-8")
    (notes / "data.json").write_text("{}", encoding="utf-8")
    service = build_service(notes)
    service.add_comment("note.md", "first", "c_111111")

    with pytest.raises(CommentAlreadyExistsError):
        service.add_comment("note.md", "dup", "c_111111")
    with pytest.raises(CommentNotFoundError):
        service.update_comment("note.md", "c_999999", status="resolved")
    with pytest.raises(CommentNotFoundError):
        service.delete_comment("note.md", "c_999999")
    with pytest.raises(InvalidPathError):
        service.list_comments("data.json")
    with pytest.raises(InvalidPathError):
        service.list_comments("note_comments.md")
    with pytest.raises(InvalidPathError):
        service.list_comments("../note.md")


def test_demo_mode_blocks_writes_but_allows_reading(tmp_path: Path):
    notes = tmp_path / "vault"
    notes.mkdir()
    (notes / "note.md").write_text("hello", encoding="utf-8")
    (notes / "note_comments.md").write_text(SAMPLE, encoding="utf-8")
    service = build_service(notes, demo_mode=True)
    assert len(service.list_comments("note.md").comments) == 2
    with pytest.raises(DemoReadOnlyError):
        service.add_comment("note.md", "nope")
    with pytest.raises(DemoReadOnlyError):
        service.delete_comment("note.md", "c_a7f3d2")
