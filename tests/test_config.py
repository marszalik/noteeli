from app.core.config import Settings


def _settings(**kw):
    # .env / NOTEELI_* isolation is handled globally in conftest.py.
    kw.setdefault("session_secret", "test")
    return Settings(**kw)


def test_demo_mode_forces_hosted_off():
    # The public demo runs from the hosted app's working dir and would
    # otherwise inherit NOTEELI_HOSTED_MODE=1 from a shared .env, which
    # makes the hosted guard reject the demo's local content root.
    s = _settings(demo_mode=True, hosted_mode=True)
    assert s.demo_mode is True
    assert s.hosted_mode is False


def test_hosted_mode_without_demo_is_preserved():
    s = _settings(hosted_mode=True)
    assert s.hosted_mode is True


def test_plain_local_defaults():
    s = _settings()
    assert s.demo_mode is False
    assert s.hosted_mode is False


def test_blank_bool_env_values_are_disabled():
    # A bare `NOTEELI_LOCK_WORKSPACE=` line in .env arrives as "" and used
    # to crash pydantic ("could not parse as bool"). Treat blank as unset.
    s = _settings(lock_workspace="", hosted_mode="  ", demo_mode="")
    assert s.lock_workspace is False
    assert s.hosted_mode is False
    assert s.demo_mode is False


def test_redirect_all_to_turns_the_app_into_a_301(tmp_path, monkeypatch):
    """A retired instance serves nothing but permanent redirects."""
    from fastapi.testclient import TestClient

    monkeypatch.setenv("NOTEELI_CONTENT_ROOT", str(tmp_path / "content"))
    monkeypatch.setenv("NOTEELI_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("NOTEELI_REDIRECT_ALL_TO", "https://noteeli.com")
    from app.core.config import get_settings
    get_settings.cache_clear()
    from app.main import create_app

    client = TestClient(create_app(), base_url="http://app.example.com")
    for path in ("/", "/login", "/api/tree", "/42/anything"):
        response = client.get(path, follow_redirects=False)
        assert response.status_code == 301, path
        assert response.headers["location"] == "https://noteeli.com"
    get_settings.cache_clear()
