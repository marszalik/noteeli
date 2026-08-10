"""/api/file/raw — verbatim file serving for "open in new tab".

The endpoint hands the browser the untouched file with an inline
content disposition: PDFs render in the native viewer, office files
download for the user's native application. Unlike /api/file/preview it
never rewrites anything (no office→HTML rendering) and serves any file
type.

Note: the workspace router snapshots its service at import time against
the conftest sandbox, so test files are written into the sandbox content
root (os.environ["NOTEELI_CONTENT_ROOT"]) rather than a per-test tmp_path.
"""
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client() -> TestClient:
    content = Path(os.environ["NOTEELI_CONTENT_ROOT"])
    content.mkdir(parents=True, exist_ok=True)
    (content / "raw-raport.pdf").write_bytes(b"%PDF-1.4 fake pdf body")
    (content / "raw-slajdy.pptx").write_bytes(b"PK fake pptx body")
    (content / "raw-notatka.md").write_text("# hej\n", encoding="utf-8")

    # Localhost base URL → the local-host auth bypass applies.
    yield TestClient(create_app(), base_url="http://127.0.0.1")

    for name in ("raw-raport.pdf", "raw-slajdy.pptx", "raw-notatka.md"):
        (content / name).unlink(missing_ok=True)


def test_raw_serves_pdf_inline_with_media_type(client: TestClient):
    response = client.get("/api/file/raw", params={"path": "raw-raport.pdf"})
    assert response.status_code == 200
    assert response.content == b"%PDF-1.4 fake pdf body"
    assert response.headers["content-type"].startswith("application/pdf")
    assert response.headers["content-disposition"].startswith("inline")
    assert "raw-raport.pdf" in response.headers["content-disposition"]


def test_raw_serves_office_files_verbatim_not_html(client: TestClient):
    """Unlike /api/file/preview, no server-side HTML rendering — the
    browser gets the real .pptx bytes (and will download them)."""
    response = client.get("/api/file/raw", params={"path": "raw-slajdy.pptx"})
    assert response.status_code == 200
    assert response.content == b"PK fake pptx body"
    assert "html" not in response.headers["content-type"]
    assert response.headers["content-disposition"].startswith("inline")


def test_raw_serves_any_type_including_markdown(client: TestClient):
    response = client.get("/api/file/raw", params={"path": "raw-notatka.md"})
    assert response.status_code == 200
    assert response.text == "# hej\n"


def test_raw_missing_file_is_404(client: TestClient):
    response = client.get("/api/file/raw", params={"path": "raw-brak.pdf"})
    assert response.status_code == 404


def test_raw_rejects_path_escape(client: TestClient):
    response = client.get("/api/file/raw", params={"path": "../../etc/passwd"})
    assert response.status_code in (400, 404)


def test_raw_requires_auth_for_non_local_hosts(client: TestClient):
    remote = TestClient(create_app(), base_url="http://app.example.com")
    response = remote.get("/api/file/raw", params={"path": "raw-raport.pdf"})
    assert response.status_code == 401
