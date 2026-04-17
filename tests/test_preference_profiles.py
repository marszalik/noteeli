from pathlib import Path

from app.core.config import Settings
from app.domains.preferences.repository import PreferencesRepository
from app.domains.preferences.service import PreferencesService


def build_service(tmp_path: Path) -> tuple[PreferencesRepository, PreferencesService]:
    settings = Settings(
        content_root=tmp_path / "content",
        data_dir=tmp_path / ".noteeli",
        session_secret="test-secret",
        google_client_id="",
        google_client_secret="",
    )
    repository = PreferencesRepository(settings)
    service = PreferencesService(settings, repository)
    return repository, service


def test_save_list_and_apply_preference_profile(tmp_path: Path):
    repository, service = build_service(tmp_path)

    saved = service.create_profile(
        name="Firmowy SFTP",
        source_type="sftp",
        content_root=str(tmp_path / "ignored-local-root"),
        sftp_host="sftp.example.com",
        sftp_port=2222,
        sftp_username="eli",
        sftp_password="sekret",
        sftp_path="/srv/notatki",
        gdrive_folder_id="root",
        sort_mode="manual",
        theme_mode="obsidian",
        editor_font_size=18,
        image_upload_mode="subdir",
        image_upload_subdir="grafiki",
    )

    profiles = service.list_profiles()

    assert len(profiles) == 1
    assert profiles[0].id == saved.id
    assert profiles[0].name == "Firmowy SFTP"
    assert profiles[0].source_type == "sftp"
    assert profiles[0].sftp_host == "sftp.example.com"
    assert profiles[0].sftp_path == "/srv/notatki"

    applied = service.apply_profile(saved.id)

    assert applied.source_type == "sftp"
    assert applied.sftp_host == "sftp.example.com"
    assert applied.sftp_port == 2222
    assert applied.sftp_username == "eli"
    assert applied.sftp_password == "sekret"
    assert applied.sftp_path == "/srv/notatki"
    assert applied.sort_mode == "manual"
    assert applied.theme_mode == "obsidian"
    assert applied.editor_font_size == 18
    assert applied.image_upload_mode == "subdir"
    assert applied.image_upload_subdir == "grafiki"
    assert repository.get_app_preferences().source_type == "sftp"


def test_update_preference_profile_changes_existing_entry(tmp_path: Path):
    _repository, service = build_service(tmp_path)

    saved = service.create_profile(
        name="Lokalny",
        source_type="local",
        content_root=str(tmp_path / "vault-a"),
        sort_mode="alphabetical",
        theme_mode="light",
        editor_font_size=16,
    )

    updated = service.update_profile(
        saved.id,
        name="Lokalny dom",
        source_type="local",
        content_root=str(tmp_path / "vault-b"),
        sort_mode="manual",
        theme_mode="dark",
        editor_font_size=19,
    )

    profiles = service.list_profiles()

    assert len(profiles) == 1
    assert updated.id == saved.id
    assert profiles[0].name == "Lokalny dom"
    assert profiles[0].content_root == str((tmp_path / "vault-b").resolve())
    assert profiles[0].theme_mode == "dark"


def test_delete_preference_profile_removes_entry(tmp_path: Path):
    _repository, service = build_service(tmp_path)

    saved = service.create_profile(
        name="Do usuniecia",
        source_type="local",
        content_root=str(tmp_path / "vault-a"),
        sort_mode="alphabetical",
        theme_mode="light",
        editor_font_size=16,
    )

    service.delete_profile(saved.id)

    assert service.list_profiles() == []
