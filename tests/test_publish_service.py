"""Tests for the publish service.

The published_items table lives in the same SQLite DB as preferences.
Each test gets a fresh tmp_path-rooted Settings so DBs are isolated.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.domains.publish.repository import PublishedItemsRepository
from app.domains.publish.service import (
    PublishService,
    PublishedItemAlreadyExistsError,
    PublishedItemNotFoundError,
)


def build_service(tmp_path: Path) -> PublishService:
    settings = Settings(
        content_root=tmp_path / "content",
        data_dir=tmp_path / ".noteeli",
        session_secret="test-secret",
        google_client_id="",
        google_client_secret="",
    )
    repo = PublishedItemsRepository(settings)
    return PublishService(settings, repo)


# ── Slug generation ─────────────────────────────────────────────


def test_slugify_strips_extension_and_diacritics():
    assert PublishService.slugify("My Note.md") == "my-note"
    assert PublishService.slugify("Café notes.md") == "cafe-notes"
    assert PublishService.slugify("Łódź — relacja.md") == "lodz-relacja"
    assert PublishService.slugify("a/b/c.txt") == "c"
    assert PublishService.slugify("") == "item"
    assert PublishService.slugify("!!!") == "item"


# ── Publish / unpublish round-trip ──────────────────────────────


def test_publish_creates_an_item_and_returns_public_url(tmp_path: Path):
    service = build_service(tmp_path)
    item = service.publish(kind="file", path="notes/hello.md")

    assert item.id > 0
    assert item.path == "notes/hello.md"
    assert item.slug == "hello"
    assert item.public_url == f"/{item.id}/hello"
    assert item.kind == "file"


def test_publish_directory(tmp_path: Path):
    service = build_service(tmp_path)
    item = service.publish(kind="directory", path="projects/alpha")
    assert item.kind == "directory"
    assert item.slug == "alpha"


def test_publish_rejects_duplicate_path(tmp_path: Path):
    service = build_service(tmp_path)
    service.publish(kind="file", path="dupe.md")
    with pytest.raises(PublishedItemAlreadyExistsError):
        service.publish(kind="file", path="dupe.md")


def test_unpublish_removes_the_entry(tmp_path: Path):
    service = build_service(tmp_path)
    item = service.publish(kind="file", path="x.md")
    service.unpublish(item.id)
    with pytest.raises(PublishedItemNotFoundError):
        service.find_by_id(item.id)


def test_unpublish_404_for_unknown_id(tmp_path: Path):
    service = build_service(tmp_path)
    with pytest.raises(PublishedItemNotFoundError):
        service.unpublish(99999)


def test_list_returns_recently_published(tmp_path: Path):
    service = build_service(tmp_path)
    service.publish(kind="file", path="a.md")
    service.publish(kind="file", path="b.md")
    items = service.list_published()
    assert len(items) == 2
    paths = {it.path for it in items}
    assert paths == {"a.md", "b.md"}


# ── Path scoping (security) ─────────────────────────────────────


def test_is_in_scope_for_file(tmp_path: Path):
    service = build_service(tmp_path)
    item = service.publish(kind="file", path="notes/secret.md")

    # the file itself is in scope
    assert service.is_in_scope(item, "notes/secret.md")
    # nothing else is — even a sibling
    assert not service.is_in_scope(item, "notes/other.md")
    # path traversal attempts are rejected
    assert not service.is_in_scope(item, "../etc/passwd")


def test_is_in_scope_for_directory(tmp_path: Path):
    service = build_service(tmp_path)
    item = service.publish(kind="directory", path="public/folder")

    assert service.is_in_scope(item, "public/folder")  # the folder
    assert service.is_in_scope(item, "public/folder/note.md")  # direct child
    assert service.is_in_scope(item, "public/folder/sub/deep.md")  # nested
    assert not service.is_in_scope(item, "public/other")  # sibling
    assert not service.is_in_scope(item, "secret/file.md")  # unrelated branch


def test_cleanup_for_removed_path_drops_descendants(tmp_path: Path):
    service = build_service(tmp_path)
    service.publish(kind="directory", path="projects")
    service.publish(kind="file", path="projects/sub/note.md")
    service.publish(kind="file", path="projects/intro.md")
    service.publish(kind="file", path="other/thing.md")

    deleted = service.cleanup_for_removed_path("projects")

    assert deleted == 3
    remaining = [it.path for it in service.list_published()]
    assert remaining == ["other/thing.md"]


# ── Routing & auth via TestClient ───────────────────────────────


@pytest.fixture
def client(tmp_path: Path, monkeypatch) -> TestClient:
    """An app whose backend points at tmp_path so the test owns its
    SQLite DB and content root."""
    monkeypatch.setenv("NOTEELI_CONTENT_ROOT", str(tmp_path / "content"))
    monkeypatch.setenv("NOTEELI_DATA_DIR", str(tmp_path / ".noteeli"))
    monkeypatch.setenv("NOTEELI_SESSION_SECRET", "test-secret")
    monkeypatch.setenv("NOTEELI_GOOGLE_CLIENT_ID", "")
    monkeypatch.setenv("NOTEELI_GOOGLE_CLIENT_SECRET", "")
    monkeypatch.delenv("NOTEELI_DEMO_MODE", raising=False)
    get_settings.cache_clear()

    from app.main import create_app

    # Seed a tiny content tree that publish targets can resolve.
    content = tmp_path / "content"
    content.mkdir(parents=True)
    (content / "public.md").write_text("# Hello\n", encoding="utf-8")
    public_dir = content / "shared"
    public_dir.mkdir()
    (public_dir / "doc.md").write_text("# Inside shared\n", encoding="utf-8")

    app = create_app()
    yield TestClient(app, base_url="http://app.example.com")
    get_settings.cache_clear()


def test_publish_api_requires_auth(client: TestClient):
    response = client.post("/api/publish", json={"path": "public.md"})
    # Non-local host without a session: 401.
    assert response.status_code == 401


def test_published_view_works_without_auth(tmp_path: Path, client: TestClient):
    # Pre-populate a publish entry directly so we can hit the public
    # route without going through the auth-protected create endpoint.
    settings = get_settings()
    repo = PublishedItemsRepository(settings)
    item_id = repo.insert("file", "public.md", "public")

    page = client.get(f"/{item_id}/public")
    assert page.status_code == 200
    assert b"Public view" in page.content

    # The scoped tree API also works without auth.
    tree = client.get(f"/api/public/{item_id}/tree")
    assert tree.status_code == 200
    body = tree.json()
    assert body["kind"] == "directory"

    # And the file content endpoint.
    file_resp = client.get(f"/api/public/{item_id}/file")
    assert file_resp.status_code == 200
    assert "# Hello" in file_resp.json()["content"]


def test_public_routes_block_path_traversal(tmp_path: Path, client: TestClient):
    settings = get_settings()
    repo = PublishedItemsRepository(settings)
    item_id = repo.insert("file", "public.md", "public")

    # Asking for a sibling file that wasn't published → 403
    response = client.get(f"/api/public/{item_id}/file?path=shared/doc.md")
    assert response.status_code == 403


def test_public_view_redirects_wrong_slug(tmp_path: Path, client: TestClient):
    settings = get_settings()
    repo = PublishedItemsRepository(settings)
    item_id = repo.insert("file", "public.md", "public")

    response = client.get(f"/{item_id}/wrong-slug", follow_redirects=False)
    assert response.status_code == 301
    assert response.headers["location"] == f"/{item_id}/public"


def test_public_view_404_for_unknown_id(client: TestClient):
    response = client.get("/99999/anything")
    assert response.status_code == 404
