"""The public demo must never reveal or reach anything outside its own
content root: no directory browsing of the host, no server-side SFTP
connection attempts on a caller's behalf."""
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app.domains.auth.router as arouter
import app.domains.workspace.router as wrouter
from app.core.config import get_settings
from app.domains.auth.service import AuthService
from app.domains.workspace.service import WorkspaceService
from app.main import create_app


@pytest.fixture
def demo_client(tmp_path: Path, monkeypatch):
    root = tmp_path / "demo-content"
    root.mkdir()
    (root / "sub").mkdir()
    (tmp_path / "secret-dir").mkdir()  # a sibling of the content root
    monkeypatch.setenv("NOTEELI_CONTENT_ROOT", str(root))
    monkeypatch.setenv("NOTEELI_DATA_DIR", str(tmp_path / ".noteeli"))
    monkeypatch.setenv("NOTEELI_SESSION_SECRET", "test-secret")
    monkeypatch.setenv("NOTEELI_GOOGLE_CLIENT_ID", "")
    monkeypatch.setenv("NOTEELI_GOOGLE_CLIENT_SECRET", "")
    monkeypatch.setenv("NOTEELI_HOSTED_MODE", "0")
    monkeypatch.setenv("NOTEELI_REDIRECT_ALL_TO", "")
    monkeypatch.setenv("NOTEELI_DEMO_MODE", "1")
    get_settings.cache_clear()
    app = create_app()
    fresh = get_settings()
    monkeypatch.setattr(wrouter, "settings", fresh)
    monkeypatch.setattr(wrouter, "auth_service", AuthService(fresh))
    monkeypatch.setattr(wrouter, "workspace_service", WorkspaceService(fresh))
    monkeypatch.setattr(arouter, "_settings", fresh)
    monkeypatch.setattr(arouter, "auth_service", AuthService(fresh))
    yield TestClient(app, base_url="http://127.0.0.1"), tmp_path
    get_settings.cache_clear()


def test_demo_directory_browser_cannot_leave_the_content_root(demo_client):
    client, tmp_path = demo_client
    for probe in (str(tmp_path), "/", "/home", str(tmp_path / "secret-dir"), "/etc"):
        data = client.get("/api/directories", params={"path": probe}).json()
        assert data["current_path"] == str((tmp_path / "demo-content").resolve()), probe
        assert data["parent_path"] is None
        names = [d["name"] for d in data["directories"]]
        assert names and "secret-dir" not in names, probe
        assert all(d["path"].startswith(data["current_path"]) for d in data["directories"])


def test_demo_refuses_the_sftp_connection_test(demo_client):
    client, _ = demo_client
    response = client.post(
        "/api/sftp/test",
        json={"host": "127.0.0.1", "port": 22, "username": "x", "password": "y", "path": "/"},
    )
    assert response.status_code == 403
