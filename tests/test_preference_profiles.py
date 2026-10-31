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


def test_apply_profile_marks_it_active_and_delete_clears(tmp_path: Path):
    """The dropdown highlights which profile is currently active; deleting
    the active profile must clear the marker so the UI doesn't point at
    a row that no longer exists."""
    repository, service = build_service(tmp_path)

    # Fresh DB → nothing is active.
    assert repository.get_active_profile_id() is None
    assert service.get_preferences().active_profile_id is None

    a = service.create_profile(
        name="A",
        content_root=str(tmp_path / "content"),
        sort_mode="alphabetical",
        theme_mode="webnote",
        editor_font_size=14,
    )
    b = service.create_profile(
        name="B",
        content_root=str(tmp_path / "content"),
        sort_mode="manual",
        theme_mode="dark",
        editor_font_size=18,
    )

    applied = service.apply_profile(a.id)
    assert applied.active_profile_id == a.id
    assert service.get_preferences().active_profile_id == a.id

    # Switching to B updates the marker.
    service.apply_profile(b.id)
    assert service.get_preferences().active_profile_id == b.id

    # Deleting the inactive A leaves B as active.
    service.delete_profile(a.id)
    assert service.get_preferences().active_profile_id == b.id

    # Deleting the active B clears the marker.
    service.delete_profile(b.id)
    assert service.get_preferences().active_profile_id is None


def _make_profile(service: PreferencesService, tmp_path: Path, name: str, **over):
    args = dict(
        name=name,
        source_type="local",
        content_root=str(tmp_path / name),
        sort_mode="alphabetical",
        theme_mode="light",
        editor_font_size=16,
    )
    args.update(over)
    return service.create_profile(**args)


def _update(service: PreferencesService, base, **over):
    args = dict(
        content_root=base.content_root,
        sort_mode=base.sort_mode,
        theme_mode=base.theme_mode,
        editor_font_size=base.editor_font_size,
        source_type=base.source_type,
    )
    args.update(over)
    return service.update_preferences(**args)


def test_settings_changes_write_through_to_the_active_profile(tmp_path: Path):
    _repo, service = build_service(tmp_path)
    work = _make_profile(service, tmp_path, "praca")
    other = _make_profile(service, tmp_path, "dom", theme_mode="dark")
    applied = service.apply_profile(work.id)

    _update(service, applied, theme_mode="obsidian", editor_font_size=22)

    profiles = {p.name: p for p in service.list_profiles()}
    assert profiles["praca"].theme_mode == "obsidian"
    assert profiles["praca"].editor_font_size == 22
    assert profiles["dom"].theme_mode == "dark"  # other profiles untouched
    assert service.get_preferences().active_profile_id == work.id
    assert other.id != work.id


def test_applying_sftp_profile_without_password_does_not_inherit_previous_one(tmp_path: Path):
    _repo, service = build_service(tmp_path)
    a = _make_profile(
        service, tmp_path, "a", source_type="sftp", sftp_host="a.example", sftp_password="secret-a"
    )
    b = _make_profile(service, tmp_path, "b", source_type="sftp", sftp_host="b.example")

    service.apply_profile(a.id)
    applied_b = service.apply_profile(b.id)

    assert applied_b.sftp_password == ""
    assert applied_b.has_stored_sftp_password is False
    # ...and A still has its own password.
    assert service.apply_profile(a.id).sftp_password == "secret-a"


def test_stale_active_profile_is_dropped_when_source_no_longer_matches(tmp_path: Path):
    repo, service = build_service(tmp_path)
    work = _make_profile(service, tmp_path, "praca")
    service.apply_profile(work.id)
    # Legacy behaviour: the source was changed without touching the marker.
    repo.update_app_preferences(content_root=str(tmp_path / "somewhere-else"))
    (tmp_path / "somewhere-else").mkdir()

    assert service.get_preferences().active_profile_id is None
    # ...so a later settings save can no longer overwrite "praca".
    before = service.list_profiles()[0].content_root
    _update(service, service.get_preferences(), theme_mode="dark")
    assert service.list_profiles()[0].content_root == before


def test_rename_profile_and_conflicts(tmp_path: Path):
    _repo, service = build_service(tmp_path)
    a = _make_profile(service, tmp_path, "a")
    _make_profile(service, tmp_path, "b")

    renamed = service.rename_profile(a.id, "  alfa ")
    assert renamed.name == "alfa"
    import pytest
    from app.domains.preferences.service import (
        PreferenceProfileConflictError,
        PreferenceProfileNotFoundError,
    )

    with pytest.raises(PreferenceProfileConflictError):
        service.rename_profile(a.id, "b")
    with pytest.raises(PreferenceProfileNotFoundError):
        service.rename_profile(9999, "x")


def test_create_profile_from_current_activates_it(tmp_path: Path):
    _repo, service = build_service(tmp_path)
    current = service.update_preferences(
        content_root=str(tmp_path / "moje"),
        sort_mode="alphabetical",
        theme_mode="dark",
        editor_font_size=19,
    )

    profile = service.create_profile_from_current("Moje")

    assert profile.theme_mode == "dark" and profile.editor_font_size == 19
    assert profile.content_root == current.content_root
    assert service.get_preferences().active_profile_id == profile.id
