"""The public (published) view must build preview URLs with a real query
string.

Regression: `renderPublicFile` interpolated `config.previewUrl` with
`&path=` instead of `?path=`. In the workspace view the same helper is
used correctly (two other call sites), so previews worked when logged in
and broke only on a published page — the request arrived as
`/api/public/2/file/preview&path=…` (a path segment, no query) and every
image, PDF and Office preview 404'd.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.domains.publish.repository import PublishedItemsRepository
from app.domains.publish.service import PublishService
from app.main import create_app


APP_JS = Path(__file__).resolve().parent.parent / "static" / "app.js"


def test_preview_url_is_never_extended_with_an_ampersand():
    """`config.previewUrl` has no query string of its own, so the first
    parameter appended to it must open one with '?'."""
    offenders = re.findall(r"\$\{config\.previewUrl\}&", APP_JS.read_text())
    assert offenders == [], (
        "previewUrl must be extended with '?' — '&' turns the parameter "
        "into part of the path and the request 404s"
    )


@pytest.fixture
def published(tmp_path: Path, monkeypatch):
    """A published directory holding one image."""
    content = tmp_path / "content"
    (content / "gallery").mkdir(parents=True)
    # A 1x1 PNG is enough — the endpoint only has to find and serve it.
    (content / "gallery" / "shot.png").write_bytes(
        bytes.fromhex(
            "89504e470d0a1a0a0000000d494844520000000100000001080600000"
            "01f15c4890000000a49444154789c63000100000500010d0a2db40000"
            "000049454e44ae426082"
        )
    )

    monkeypatch.setenv("NOTEELI_CONTENT_ROOT", str(content))
    monkeypatch.setenv("NOTEELI_DATA_DIR", str(tmp_path / ".noteeli"))
    monkeypatch.setenv("NOTEELI_SESSION_SECRET", "test-secret")
    monkeypatch.setenv("NOTEELI_GOOGLE_CLIENT_ID", "")
    monkeypatch.setenv("NOTEELI_GOOGLE_CLIENT_SECRET", "")
    get_settings.cache_clear()

    settings = Settings(
        content_root=content,
        data_dir=tmp_path / ".noteeli",
        session_secret="test-secret",
        google_client_id="",
        google_client_secret="",
    )
    service = PublishService(settings, PublishedItemsRepository(settings))
    item = service.publish("directory", "gallery")

    yield item, TestClient(create_app(), base_url="http://app.example.com")

    get_settings.cache_clear()


def test_public_preview_serves_the_file_from_a_query_string(published):
    item, client = published
    response = client.get(
        f"/api/public/{item.id}/file/preview", params={"path": "gallery/shot.png"}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"


def test_public_preview_as_a_path_segment_is_not_a_route(published):
    """The shape the bug produced must stay a 404 — proof the test above
    is actually exercising the query-string form."""
    item, client = published
    response = client.get(f"/api/public/{item.id}/file/preview&path=gallery/shot.png")
    assert response.status_code == 404
