import errno
from pathlib import Path

from app.core.config import Settings
from app.domains.preferences.repository import PreferencesRepository
from app.domains.preferences.service import PreferencesService


def build_service(tmp_path: Path) -> tuple[Settings, PreferencesRepository, PreferencesService]:
    settings = Settings(
        content_root=tmp_path / "content",
        data_dir=tmp_path / ".noteeli",
        session_secret="test-secret",
        google_client_id="",
        google_client_secret="",
    )
    repository = PreferencesRepository(settings)
    service = PreferencesService(settings, repository)
    return settings, repository, service


def test_get_preferences_falls_back_to_default_content_root_when_saved_path_is_invalid(
    tmp_path: Path,
    monkeypatch,
):
    settings, repository, service = build_service(tmp_path)
    broken_root = "/home/eli/dev/noteeli/content"
    repository.update_app_preferences(content_root=broken_root)

    original = service._ensure_local_content_root

    def fake_ensure_local_content_root(value: str | Path) -> Path:
        if str(value) == broken_root:
            raise OSError(errno.ENOTSUP, "Operation not supported")
        return original(value)

    monkeypatch.setattr(service, "_ensure_local_content_root", fake_ensure_local_content_root)

    preferences = service.get_preferences()

    assert preferences.content_root == str(settings.content_root.resolve())
    assert repository.get_app_preferences().content_root == str(settings.content_root.resolve())
    assert settings.content_root.resolve().is_dir()


def test_update_preferences_persists_basic_fields(tmp_path: Path):
    settings, repository, service = build_service(tmp_path)
    notes = tmp_path / "my-notes"
    notes.mkdir()

    updated = service.update_preferences(
        content_root=str(notes),
        sort_mode="manual",
        theme_mode="dark",
        editor_font_size=18,
        autosave_enabled=True,
        language="en",
    )

    assert updated.content_root == str(notes.resolve())
    assert updated.sort_mode == "manual"
    assert updated.theme_mode == "dark"
    assert updated.editor_font_size == 18
    assert updated.autosave_enabled is True
    assert updated.language == "en"

    # Round-trip through the repository — values are persisted, not just returned.
    persisted = repository.get_app_preferences()
    assert persisted.theme_mode == "dark"
    assert persisted.autosave_enabled is True


def test_update_preferences_switches_to_sftp_source_type(tmp_path: Path):
    settings, repository, service = build_service(tmp_path)

    updated = service.update_preferences(
        content_root="/home/eli",  # ignored when source_type != local
        sort_mode="alphabetical",
        theme_mode="noteeli",
        editor_font_size=14,
        source_type="sftp",
        sftp_host="example.com",
        sftp_port=2222,
        sftp_username="eli",
        sftp_password="secret",
        sftp_path="/notes",
    )

    assert updated.source_type == "sftp"
    assert updated.sftp_host == "example.com"
    assert updated.sftp_port == 2222
    assert updated.sftp_username == "eli"
    assert updated.sftp_path == "/notes"
    # Local content_root remains as-passed when source_type isn't local.
    persisted = repository.get_app_preferences()
    assert persisted.source_type == "sftp"
    assert persisted.sftp_password == "secret"


def test_update_preferences_normalises_local_content_root(tmp_path: Path):
    """Local source_type triggers a real path resolve — relative paths are
    normalised, missing dirs are created."""
    settings, repository, service = build_service(tmp_path)
    new_root = tmp_path / "fresh-vault"
    # Note: directory does not yet exist. Service should create it.

    updated = service.update_preferences(
        content_root=str(new_root),
        sort_mode="alphabetical",
        theme_mode="light",
        editor_font_size=14,
    )

    assert updated.content_root == str(new_root.resolve())
    assert new_root.is_dir()


def test_compact_chrome_round_trips(tmp_path):
    """The Appearance → Compact layout toggle persists and reads back."""
    from app.core.config import Settings
    from app.domains.preferences.repository import PreferencesRepository
    from app.domains.preferences.service import PreferencesService

    settings = Settings(
        content_root=tmp_path / "notes",
        data_dir=tmp_path / ".noteeli",
        session_secret="test",
        google_client_id="",
        google_client_secret="",
    )
    repo = PreferencesRepository(settings)
    service = PreferencesService(settings, repo)

    # Default is on (frameless layout ships as the default look).
    assert service.get_preferences().compact_chrome is True

    # Toggle off, persist
    updated = service.update_preferences(
        content_root=str(tmp_path / "notes"),
        sort_mode="alphabetical",
        theme_mode="webnote",
        editor_font_size=14,
        compact_chrome=False,
    )
    assert updated.compact_chrome is False

    # Survives a fresh repo (i.e. it's in SQLite, not just memory)
    reloaded = PreferencesService(settings, PreferencesRepository(settings)).get_preferences()
    assert reloaded.compact_chrome is False


def test_content_root_display_is_relative_to_env_root(tmp_path):
    """The sidebar label must not leak the server's filesystem layout:
    equal to NOTEELI_CONTENT_ROOT → "/", subdir → "/sub", outside → the
    real (deliberately chosen) path."""
    from app.core.config import Settings
    from app.domains.workspace.service import WorkspaceService

    root = tmp_path / "notes"
    (root / "kurs" / "sylabus").mkdir(parents=True)
    settings = Settings(
        content_root=root, data_dir=tmp_path / ".noteeli", session_secret="t"
    )
    service = WorkspaceService(settings)

    assert service.relativize_local_root(str(root)) == "/"
    assert service.relativize_local_root(str(root / "kurs" / "sylabus")) == "/kurs/sylabus"
    outside = tmp_path / "elsewhere"
    outside.mkdir()
    assert service.relativize_local_root(str(outside)) == str(outside)

    # And the preferences API carries the computed display field.
    prefs = service.get_preferences()
    assert prefs.content_root_display == "/"
