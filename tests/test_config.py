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
