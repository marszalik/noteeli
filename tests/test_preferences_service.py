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
