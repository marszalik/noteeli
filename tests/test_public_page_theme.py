"""A published page renders with the publisher's own look.

Theme, font size and language are *personal* keys: the Settings UI writes
them to `user_settings` under the caller's key, never to the global
`app_settings` row. The public page used to read preferences with no user
key, so it always rendered the factory defaults — on a single-user
instance the shared page still didn't match what the owner saw, and no
setting the owner could change had any effect on it.

`published_items.user_key` records who published an item so the public
render can ask for that person's preferences.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.domains.preferences.repository import PreferencesRepository
from app.domains.publish.repository import PublishedItemsRepository
from app.domains.publish.service import PublishService
from app.main import create_app


OWNER = "owner@example.com"


@pytest.fixture
def env(tmp_path: Path, monkeypatch):
    content = tmp_path / "content"
    (content / "shared").mkdir(parents=True)
    (content / "shared" / "note.md").write_text("# hello\n")

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
    # The owner picked a non-default theme — this lands in user_settings.
    PreferencesRepository(settings).update_app_preferences(
        user_key=OWNER, theme_mode="obsidian"
    )
    publish = PublishService(settings, PublishedItemsRepository(settings))

    yield settings, publish, TestClient(create_app(), base_url="http://app.example.com")

    get_settings.cache_clear()


def test_publishing_records_the_publisher(env):
    _settings, publish, _client = env
    item = publish.publish("directory", "shared", user_key=OWNER)
    assert item.user_key == OWNER
    assert publish.find_by_id(item.id).user_key == OWNER


def test_public_page_uses_the_publishers_personal_theme(env):
    _settings, publish, client = env
    item = publish.publish("directory", "shared", user_key=OWNER)

    response = client.get(item.public_url)
    assert response.status_code == 200
    assert 'data-theme-mode="obsidian"' in response.text


def test_legacy_rows_without_a_publisher_fall_back_to_the_global_row(env):
    """Rows predating the column keep the old behaviour rather than
    guessing an owner."""
    settings, publish, client = env
    item = publish.publish("directory", "shared", user_key="")

    response = client.get(item.public_url)
    assert response.status_code == 200
    # The factory default, i.e. what app_settings holds untouched.
    assert 'data-theme-mode="webnote"' in response.text


def test_migration_adds_user_key_to_an_existing_table(tmp_path: Path):
    """An older DB gets the column added in place, with existing rows
    landing in the legacy bucket."""
    import sqlite3

    settings = Settings(
        content_root=tmp_path / "content",
        data_dir=tmp_path / ".noteeli",
        session_secret="test-secret",
    )
    settings.ensure_runtime_dirs()
    with sqlite3.connect(settings.database_path) as conn:
        conn.execute(
            """
            CREATE TABLE published_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kind TEXT NOT NULL CHECK (kind IN ('file', 'directory')),
                path TEXT NOT NULL UNIQUE,
                slug TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        conn.execute(
            "INSERT INTO published_items(kind, path, slug) VALUES('file', 'a.md', 'a')"
        )

    repo = PublishedItemsRepository(settings)  # runs the migration
    row = repo.find_by_path("a.md")
    assert row["user_key"] == ""
