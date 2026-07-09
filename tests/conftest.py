"""Global test isolation.

The suite must be hermetic: it runs on developer machines (including the
production box) where a real `.env` with NOTEELI_HOSTED_MODE=1 etc. sits in
the repo root, and NOTEELI_* vars may be exported in the shell. Without this
scrub, `get_settings()` picks those up and e.g. every workspace test dies
with "Local filesystem is not available in hosted mode." (402/paywall).

The scrub happens at *import* time, not in a fixture: conftest.py is imported
before any test module, and several routers snapshot `get_settings()` at
module level (`app/domains/workspace/router.py`, `app/domains/auth/router.py`),
so the environment must already be clean when those imports run.
"""

import os
import tempfile

# 1. Strip NOTEELI_* vars inherited from the developer's shell. Tests that
#    need specific values set them explicitly via monkeypatch/os.environ.
for _key in [k for k in os.environ if k.startswith("NOTEELI_")]:
    del os.environ[_key]

# 2. Point content/data at a throwaway sandbox. The defaults live inside the
#    repo checkout (content/, .noteeli/) — on a real deployment that .noteeli
#    holds the production preferences DB (e.g. source_type='sftp'), and the
#    module-level router singletons would happily open SFTP connections from
#    inside the test suite.
_sandbox = tempfile.mkdtemp(prefix="noteeli-tests-")
os.environ["NOTEELI_CONTENT_ROOT"] = os.path.join(_sandbox, "content")
os.environ["NOTEELI_DATA_DIR"] = os.path.join(_sandbox, "data")

from app.core.config import Settings, get_settings  # noqa: E402

# 3. Never read the repo-root .env during tests.
Settings.model_config["env_file"] = None

import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def _fresh_settings_cache():
    # Tests that tweak NOTEELI_* env vars rely on a cleared cache to see them.
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
