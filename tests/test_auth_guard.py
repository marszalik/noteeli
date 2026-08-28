"""Tests for the auth guard on workspace API endpoints.

The guard lives in `AuthService.require_api_access`: requests from
"local" hosts (127.0.0.1, localhost) bypass auth (intentional for
dev), everyone else gets 401 unless they have a session cookie.

These tests use FastAPI's TestClient with a non-local host header so
the guard fires.
"""
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.main import create_app


@pytest.fixture
def client(tmp_path: Path, monkeypatch) -> TestClient:
    """Build a fresh app with isolated content/data dirs and a non-local
    host so the auth guard activates."""
    monkeypatch.setenv("NOTEELI_CONTENT_ROOT", str(tmp_path / "content"))
    monkeypatch.setenv("NOTEELI_DATA_DIR", str(tmp_path / ".noteeli"))
    monkeypatch.setenv("NOTEELI_SESSION_SECRET", "test-secret")
    monkeypatch.setenv("NOTEELI_GOOGLE_CLIENT_ID", "")
    monkeypatch.setenv("NOTEELI_GOOGLE_CLIENT_SECRET", "")
    monkeypatch.setenv("NOTEELI_LOCAL_USERNAME", "")
    monkeypatch.setenv("NOTEELI_LOCAL_PASSWORD", "")

    # Drop the cached Settings so env changes are picked up.
    get_settings.cache_clear()

    app = create_app()
    test_client = TestClient(app, base_url="http://app.example.com")
    yield test_client

    get_settings.cache_clear()


def test_tree_api_requires_auth(client: TestClient):
    """An unauthenticated request to /api/tree from a non-local host
    is rejected."""
    response = client.get("/api/tree")
    assert response.status_code == 401


def test_file_api_requires_auth(client: TestClient):
    response = client.get("/api/file", params={"path": "anything.md"})
    assert response.status_code == 401


def test_save_api_requires_auth(client: TestClient):
    response = client.put("/api/file", json={"path": "x.md", "content": ""})
    assert response.status_code == 401


def test_create_item_requires_auth(client: TestClient):
    response = client.post("/api/items", json={"parent_path": "", "name": "foo", "kind": "file"})
    assert response.status_code == 401


def test_delete_item_requires_auth(client: TestClient):
    response = client.delete("/api/items", params={"path": "anything"})
    assert response.status_code == 401


def test_rename_item_requires_auth(client: TestClient):
    response = client.post("/api/items/rename", json={"path": "x.md", "new_name": "y"})
    assert response.status_code == 401


def test_upload_requires_auth(client: TestClient):
    response = client.post(
        "/api/items/upload",
        files=[("files", ("x.png", b"png-bytes", "image/png"))],
        data={"parent_path": ""},
    )
    assert response.status_code == 401


def test_preferences_api_requires_auth(client: TestClient):
    response = client.get("/api/preferences")
    assert response.status_code == 401


def test_preference_profiles_api_requires_auth(client: TestClient):
    response = client.get("/api/preferences/profiles")
    assert response.status_code == 401


def test_workspace_root_redirects_to_login(client: TestClient):
    """The HTML page guards differently — it redirects to the login
    page rather than returning 401."""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 303
    assert "/login" in response.headers["location"]


def test_local_host_bypass_allows_unauthenticated_access(tmp_path: Path, monkeypatch):
    """Sanity check the auth model: a request whose host is on the
    LOCAL_HOSTS list (e.g. someone accessing http://localhost:8000) is
    treated as an authenticated local user without needing a session."""
    monkeypatch.setenv("NOTEELI_CONTENT_ROOT", str(tmp_path / "content"))
    monkeypatch.setenv("NOTEELI_DATA_DIR", str(tmp_path / ".noteeli"))
    monkeypatch.setenv("NOTEELI_SESSION_SECRET", "test-secret")
    monkeypatch.setenv("NOTEELI_GOOGLE_CLIENT_ID", "")
    monkeypatch.setenv("NOTEELI_GOOGLE_CLIENT_SECRET", "")
    get_settings.cache_clear()
    app = create_app()
    local_client = TestClient(app, base_url="http://127.0.0.1:8000")

    response = local_client.get("/api/tree")
    assert response.status_code == 200
    body = response.json()
    assert body["kind"] == "directory"

    get_settings.cache_clear()


def test_gmail_dots_are_ignored_in_allowlist(tmp_path):
    """Google OAuth returns the canonical (dotless) gmail address while the
    operator typed the dotted variant into .env — both must match. Regression
    for a real lockout: allowlist had 'marek.spyrzewski@', Google sent
    'marekspyrzewski@'."""
    from app.core.config import Settings
    from app.domains.auth.service import AuthService

    settings = Settings(
        content_root=tmp_path / "n",
        data_dir=tmp_path / ".noteeli",
        session_secret="x",
        google_client_id="",
        google_client_secret="",
        allowed_google_emails="marek.spyrzewski@gmail.com, Alice@Example.com",
        admin_emails="ad.min@googlemail.com",
    )
    auth = AuthService(settings)

    # gmail: dots ignored, googlemail == gmail, case-insensitive
    assert auth.google_email_is_allowed("marekspyrzewski@gmail.com")
    assert auth.google_email_is_allowed("marek.spyrzewski@gmail.com")
    assert auth.google_email_is_allowed("Marek.Spyrzewski@GoogleMail.com")
    assert auth.is_admin("admin@gmail.com")

    # non-gmail domains: dots stay significant
    assert auth.google_email_is_allowed("alice@example.com")
    assert not auth.google_email_is_allowed("a.lice@example.com")
    # and unknown addresses are still rejected
    assert not auth.google_email_is_allowed("intruder@gmail.com")


def test_admin_emails_accept_space_separation(tmp_path):
    """Operators write NOTEELI_ADMIN_EMAILS both comma- and space-separated.
    Regression for a production redirect loop: prod .env used
    'a@gmail.com b@gmail.com' (spaces), the parser split on ',' only, so the
    whole string became one bogus entry — is_admin() returned False for a real
    admin, who (in hosted mode, no subscription) was then bounced to /subscribe
    and back to / forever."""
    from app.core.config import Settings
    from app.domains.auth.service import AuthService

    for raw in (
        "elizadie@gmail.com marszalik@gmail.com",       # spaces
        "elizadie@gmail.com,marszalik@gmail.com",       # commas
        "elizadie@gmail.com, marszalik@gmail.com",      # comma + space
        "  elizadie@gmail.com   marszalik@gmail.com  ",  # ragged whitespace
    ):
        settings = Settings(
            content_root=tmp_path / "n",
            data_dir=tmp_path / ".noteeli",
            session_secret="x",
            google_client_id="",
            google_client_secret="",
            admin_emails=raw,
        )
        auth = AuthService(settings)
        assert auth.is_admin("elizadie@gmail.com"), raw
        assert auth.is_admin("marszalik@gmail.com"), raw
        # dotted variant still canonicalises to the same gmail account
        assert auth.is_admin("eli.zadie@gmail.com"), raw
        # non-admins stay out
        assert not auth.is_admin("intruder@gmail.com"), raw


def test_forwarded_host_does_not_grant_local_access(client: TestClient):
    """X-Forwarded-Host must NOT be trusted by default.

    Regression: `_request_host` read the header unconditionally, so any
    client on the network could send `X-Forwarded-Host: localhost` and
    take the local-access auto-login path — full workspace, no password.
    Trusting it is only safe behind a proxy that overwrites the header,
    so it is now gated behind NOTEELI_TRUST_FORWARDED_HOST."""
    response = client.get("/api/tree", headers={"X-Forwarded-Host": "localhost"})
    assert response.status_code == 401


def test_forwarded_host_honoured_when_explicitly_trusted():
    """With the opt-in set, the header is honoured again — this is the
    reverse-proxy deployment (nginx in front of app.noteeli.com).

    Asserted at the service level: `auth.router` builds its AuthService at
    import time, so a TestClient in the same process can't be given
    different settings."""
    from starlette.requests import Request

    from app.domains.auth.service import AuthService

    def _request(headers: dict[str, str]) -> Request:
        return Request({
            "type": "http",
            "http_version": "1.1",
            "method": "GET",
            "scheme": "http",
            "path": "/",
            "raw_path": b"/",
            "query_string": b"",
            "root_path": "",
            "server": ("192.168.1.10", 8000),
            "headers": [(k.lower().encode(), v.encode()) for k, v in headers.items()],
        })

    spoofed = {"host": "192.168.1.10:8000", "x-forwarded-host": "localhost"}

    untrusting = AuthService(Settings(trust_forwarded_host=False))
    assert untrusting.is_local_request(_request(spoofed)) is False

    trusting = AuthService(Settings(trust_forwarded_host=True))
    assert trusting.is_local_request(_request(spoofed)) is True
