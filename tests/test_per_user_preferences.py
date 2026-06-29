import os
from pathlib import Path

from fastapi.testclient import TestClient


def _client(tmp_path: Path):
    os.environ["NOTEELI_CONTENT_ROOT"] = str(tmp_path / "notes")
    os.environ["NOTEELI_DATA_DIR"] = str(tmp_path / ".noteeli")
    os.environ["NOTEELI_SESSION_SECRET"] = "x"
    from app.core import config as cfg
    cfg.get_settings.cache_clear()
    from app.main import create_app
    app = create_app()
    # The workspace router holds a module-level WorkspaceService bound to
    # whatever settings existed when it was first imported. Rebuild it
    # against this test's fresh settings so the test is order-independent.
    from app.domains.workspace import router as wrouter
    from app.domains.workspace.service import WorkspaceService
    wrouter.settings = cfg.get_settings()
    wrouter.workspace_service = WorkspaceService(cfg.get_settings())
    return TestClient(app, base_url="http://127.0.0.1")


def test_personal_prefs_are_per_user_but_storage_is_shared(tmp_path, monkeypatch):
    client = _client(tmp_path)

    # Drive identity by patching AuthService.get_current_user per call.
    from app.domains.workspace import router as wrouter

    def make_user(email):
        return {"email": email, "name": email.split("@")[0], "is_local": False, "subscription_active": True}

    # Alice sets dark theme
    monkeypatch.setattr(wrouter.auth_service, "get_current_user", lambda req: make_user("alice@x.com"))
    r = client.put("/api/preferences", json={
        "content_root": str(tmp_path / "notes"), "sort_mode": "alphabetical",
        "theme_mode": "dark", "editor_font_size": 20, "source_type": "local",
        "language": "en", "compact_chrome": False,
    })
    assert r.status_code == 200, r.text
    assert r.json()["theme_mode"] == "dark"
    assert r.json()["editor_font_size"] == 20

    # Bob sees the DEFAULT theme, not Alice's dark
    monkeypatch.setattr(wrouter.auth_service, "get_current_user", lambda req: make_user("bob@x.com"))
    bob = client.get("/api/preferences").json()
    assert bob["theme_mode"] != "dark"           # Bob unaffected by Alice
    assert bob["editor_font_size"] != 20

    # Bob sets his own
    client.put("/api/preferences", json={
        "content_root": str(tmp_path / "notes"), "sort_mode": "alphabetical",
        "theme_mode": "obsidian", "editor_font_size": 14, "source_type": "local",
        "language": "pl", "compact_chrome": True,
    })

    # Alice still has dark — isolation holds
    monkeypatch.setattr(wrouter.auth_service, "get_current_user", lambda req: make_user("alice@x.com"))
    alice = client.get("/api/preferences").json()
    assert alice["theme_mode"] == "dark"
    assert alice["editor_font_size"] == 20
    # Storage (content_root) is the same for both — shared
    assert alice["content_root"] == bob["content_root"]


def test_saved_profiles_are_per_user(tmp_path, monkeypatch):
    client = _client(tmp_path)
    from app.domains.workspace import router as wrouter

    def make_user(email):
        return {"email": email, "name": email, "is_local": False, "subscription_active": True}

    base = {
        "content_root": str(tmp_path / "notes"), "sort_mode": "alphabetical",
        "theme_mode": "dark", "editor_font_size": 16, "source_type": "local",
        "language": "en", "compact_chrome": False, "gdrive_credentials": "",
    }

    monkeypatch.setattr(wrouter.auth_service, "get_current_user", lambda req: make_user("alice@x.com"))
    client.post("/api/preferences/profiles", json={**base, "name": "Mine"})
    alice_profiles = client.get("/api/preferences/profiles").json()["profiles"]
    assert [p["name"] for p in alice_profiles] == ["Mine"]

    # Bob sees none of Alice's profiles
    monkeypatch.setattr(wrouter.auth_service, "get_current_user", lambda req: make_user("bob@x.com"))
    bob_profiles = client.get("/api/preferences/profiles").json()["profiles"]
    assert bob_profiles == []

    # Bob can create a profile with the SAME name (per-user uniqueness)
    r = client.post("/api/preferences/profiles", json={**base, "name": "Mine"})
    assert r.status_code == 200, r.text


def test_migration_from_old_global_schema(tmp_path):
    """An existing DB with the old global preference_profiles (name UNIQUE,
    no user_key) migrates cleanly; existing profiles survive as legacy
    (user_key='') and stay visible to everyone."""
    import sqlite3
    from app.core.config import Settings

    data_dir = tmp_path / ".noteeli"
    data_dir.mkdir(parents=True)
    db = data_dir / "noteeli.sqlite3"

    # Hand-build the OLD schema with a profile.
    conn = sqlite3.connect(db)
    conn.executescript(
        """
        CREATE TABLE app_settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE preference_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            payload TEXT NOT NULL,
            sort_index INTEGER NOT NULL DEFAULT 0
        );
        INSERT INTO preference_profiles(name, payload, sort_index)
        VALUES ('Legacy', '{"content_root":"/x","theme_mode":"dark"}', 0);
        """
    )
    conn.commit()
    conn.close()

    settings = Settings(
        content_root=tmp_path / "notes",
        data_dir=data_dir,
        session_secret="x",
        google_client_id="",
        google_client_secret="",
    )
    from app.domains.preferences.repository import PreferencesRepository
    repo = PreferencesRepository(settings)  # runs _initialize → migration

    # Column added, legacy row preserved with user_key=''
    cols = [r[1] for r in sqlite3.connect(db).execute("PRAGMA table_info(preference_profiles)")]
    assert "user_key" in cols

    # Visible to a logged-in user (legacy/shared bucket)
    names = [p.name for p in repo.list_profiles("alice@x.com")]
    assert "Legacy" in names
