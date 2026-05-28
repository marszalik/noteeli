from app.core.config import Settings


def _settings(**kw):
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
