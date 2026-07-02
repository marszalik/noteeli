import logging
from pathlib import Path

from app.core.config import Settings
from app.core.logging import setup_file_logging


def _settings(tmp_path: Path, **kw) -> Settings:
    return Settings(
        content_root=tmp_path / "notes",
        data_dir=tmp_path / ".noteeli",
        session_secret="x",
        google_client_id="",
        google_client_secret="",
        **kw,
    )


def test_log_file_receives_app_and_uvicorn_records(tmp_path: Path):
    settings = _settings(tmp_path)
    settings.ensure_runtime_dirs()
    log_path = setup_file_logging(settings)
    assert log_path == tmp_path / ".noteeli" / "logs" / "noteeli.log"

    logging.getLogger("app.domains.auth.router").warning("Google login DENIED for 'x@y.com'")
    logging.getLogger("uvicorn.access").info('1.2.3.4 - "GET /api/tree HTTP/1.1" 200')
    for h in logging.getLogger().handlers:
        h.flush()

    text = log_path.read_text(encoding="utf-8")
    assert "DENIED for 'x@y.com'" in text
    assert "GET /api/tree" in text
    assert "WARNING" in text and "INFO" in text


def test_repeated_setup_does_not_duplicate_lines(tmp_path: Path):
    settings = _settings(tmp_path)
    settings.ensure_runtime_dirs()
    setup_file_logging(settings)
    log_path = setup_file_logging(settings)  # second call must replace, not stack

    logging.getLogger("app.test").warning("once-only")
    for h in logging.getLogger().handlers:
        h.flush()

    text = log_path.read_text(encoding="utf-8")
    assert text.count("once-only") == 1


def test_unwritable_log_dir_is_not_fatal(tmp_path: Path):
    blocker = tmp_path / ".noteeli"
    blocker.parent.mkdir(parents=True, exist_ok=True)
    blocker.write_text("file, not dir")  # data_dir/logs mkdir will fail
    settings = _settings(tmp_path)
    assert setup_file_logging(settings) is None  # no exception
