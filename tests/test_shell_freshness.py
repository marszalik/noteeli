"""The app-shell HTML must never be cacheable and must carry the inline
service-worker self-heal script.

Both guard against the "stale deploy" failure mode: a browser (notably
iOS/Safari) stuck on an old service worker or a cached HTML would keep
running outdated JS and silently break saves. The shell is served
`no-store` and boots a small unregister-every-SW + purge-caches script
straight from the HTML, so returning clients recover with no manual
DevTools cache wipe.
"""
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
def client(tmp_path: Path, monkeypatch) -> TestClient:
    monkeypatch.setenv("NOTEELI_CONTENT_ROOT", str(tmp_path / "content"))
    monkeypatch.setenv("NOTEELI_DATA_DIR", str(tmp_path / ".noteeli"))
    monkeypatch.setenv("NOTEELI_SESSION_SECRET", "test-secret")
    monkeypatch.setenv("NOTEELI_GOOGLE_CLIENT_ID", "")
    monkeypatch.setenv("NOTEELI_GOOGLE_CLIENT_SECRET", "")
    monkeypatch.setenv("NOTEELI_HOSTED_MODE", "0")
    get_settings.cache_clear()
    app = create_app()

    # Routers capture Settings at import time — and the repo's .env sets
    # HOSTED_MODE=1, which would bounce these routes to the external portal.
    # Rebind the module-level singletons to the freshly-loaded (non-hosted)
    # settings, mirroring tests/test_per_user_preferences.py.
    fresh = get_settings()
    wrouter.settings = fresh
    wrouter.auth_service = AuthService(fresh)
    wrouter.workspace_service = WorkspaceService(fresh)
    arouter._settings = fresh
    arouter.auth_service = AuthService(fresh)

    # Local host so the workspace page renders (auth bypass) instead of
    # redirecting to /login.
    yield TestClient(app, base_url="http://127.0.0.1")
    get_settings.cache_clear()


def test_login_shell_is_no_store(client: TestClient):
    response = client.get("/login")
    assert response.status_code == 200
    assert response.headers.get("cache-control") == "no-store"


def test_workspace_shell_is_no_store(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers.get("cache-control") == "no-store"


def test_shell_carries_sw_self_heal(client: TestClient):
    body = client.get("/login").text
    # The self-heal runs from the HTML head (not app.js) so it reaches
    # clients even when app.js itself is served stale.
    assert "serviceWorker" in body
    assert "getRegistrations" in body
    assert "unregister" in body


def test_assets_are_cache_busted(client: TestClient):
    body = client.get("/").text
    assert "app.js?v=" in body
    assert "app.css?v=" in body
