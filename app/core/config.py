from functools import lru_cache
from pathlib import Path

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "Noteeli"
    session_secret: str = "change-me-in-production"
    google_client_id: str = ""
    google_client_secret: str = ""
    # Comma-separated list of Google account e-mails allowed to log in.
    # Leave empty to allow any Google account that completes OAuth.
    allowed_google_emails: str = ""
    # Credentials for the built-in password login (optional).
    local_username: str = ""
    local_password: str = ""
    content_root: Path = PROJECT_ROOT / "content"
    data_dir: Path = PROJECT_ROOT / ".noteeli"
    allowed_markdown_extensions: tuple[str, ...] = (".md", ".markdown")
    # Demo mode — when on, the app refuses every mutation at the service
    # layer, skips authentication entirely, and points at a baked
    # read-only content root. Toggle via NOTEELI_DEMO_MODE=1 or the
    # `--demo` CLI flag. Used for the public demo at demo.noteeli.com.
    demo_mode: bool = False

    # ── Instance retirement ─────────────────────────────────────────────
    # When set to a URL, the app serves nothing but a 301 to it — for
    # decommissioned instances whose domain should live on (e.g. a retired
    # hosted app pointing visitors at the project site) without touching
    # the reverse proxy.
    redirect_all_to: str = ""

    # ── Silent checkpoint commits ───────────────────────────────────────
    # When on, every saved file is queued and — once it has been idle for
    # git_autocommit_idle_seconds — committed automatically, signed by
    # whoever saved it last. "End of an editing session" is not an
    # observable event, so this idle debounce approximates it. Gives
    # shared workspaces a truthful `git blame` even when nobody commits
    # by hand. Toggle via NOTEELI_GIT_AUTOCOMMIT=1.
    git_autocommit: bool = False
    git_autocommit_idle_seconds: int = 300
    # After a successful checkpoint, push to the configured remote. If the
    # remote moved ahead, clean divergence is replayed via pull --rebase;
    # a content conflict parks the sync (nothing lost, ahead/behind shows
    # in the git menu) for a human to resolve. Needs git_autocommit.
    git_autocommit_push: bool = False

    # Rotating file logs: <data_dir>/logs/noteeli.log, rotated daily,
    # keeping this many days. Covers app + uvicorn access/error logs so
    # incidents are diagnosable after the journal rotates away.
    log_retention_days: int = 14

    # ── Locked workspace ────────────────────────────────────────────────
    # When True, the storage source and root are pinned: users can't change
    # source_type / content_root / SFTP settings from Settings, the source
    # tab is hidden, and the directory picker is confined to the workspace
    # root (no walking up the disk). Use this to safely share a single
    # directory with a group — combine with an email allowlist (self-hosted)
    # or the Free-access panel (hosted). Toggle via NOTEELI_LOCK_WORKSPACE=1.
    lock_workspace: bool = False

    # ── Hosted / SaaS mode ──────────────────────────────────────────────
    # When True:
    #   - any Google account may log in (no allowed_google_emails check)
    #   - subscription is required to access the workspace
    #   - local-filesystem storage backend is hidden
    # Toggle via NOTEELI_HOSTED_MODE=1.
    hosted_mode: bool = False
    # Comma-separated admin emails — bypass subscription check, can access /admin.
    admin_emails: str = ""
    # Canonical public URL of the app (used to build OAuth redirect URIs).
    # Must be set when running behind a reverse proxy.
    # Example: https://app.noteeli.com
    app_url: str = ""

    # Paddle Billing (https://developer.paddle.com)
    paddle_api_key: str = ""
    paddle_webhook_secret: str = ""
    paddle_price_id: str = ""          # e.g. pri_01kr271nvqa591dbrehd141g79
    paddle_client_token: str = ""      # client-side token for Paddle.js
    # "sandbox" → sandbox-api.paddle.com  |  "live" → api.paddle.com
    paddle_environment: str = "sandbox"
    # Cookie domain for shared session with noteeli.com — set to ".noteeli.com"
    # in production so both apps see the same login state.
    session_cookie_domain: str = ""
    # Public URL of the portal (noteeli.com) — used for redirect-to-login.
    portal_url: str = "https://noteeli.com"

    model_config = SettingsConfigDict(
        env_prefix="NOTEELI_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode="after")
    def _demo_is_never_hosted(self) -> "Settings":
        # Demo and hosted are mutually exclusive: the public demo is a
        # local, read-only, no-auth instance. It commonly runs from the
        # same working directory as the hosted app, so it would otherwise
        # inherit NOTEELI_HOSTED_MODE=1 from a shared .env and then refuse
        # local storage ("Hosted mode requires SFTP or Google Drive").
        # Demo always wins.
        if self.demo_mode and self.hosted_mode:
            object.__setattr__(self, "hosted_mode", False)
        return self

    @field_validator(
        "demo_mode", "hosted_mode", "lock_workspace", "git_autocommit",
        "git_autocommit_push", mode="before"
    )
    @classmethod
    def _blank_bool_is_false(cls, value: object) -> object:
        # An empty (or whitespace-only) value in .env — e.g. a bare
        # `NOTEELI_LOCK_WORKSPACE=` line — means "not set", but pydantic
        # can't parse "" as a bool and would refuse to start. Treat it as
        # the disabled default instead of forcing the user to write `0`.
        if isinstance(value, str) and not value.strip():
            return False
        return value

    @field_validator("content_root", mode="before")
    @classmethod
    def _normalize_content_root(cls, value: str | Path) -> Path:
        return Path(value).expanduser().resolve()

    @field_validator("data_dir", mode="before")
    @classmethod
    def _normalize_data_dir(cls, value: str | Path) -> Path:
        return Path(value).expanduser().resolve()

    @property
    def template_dirs(self) -> list[Path]:
        return [
            PROJECT_ROOT / "app",
        ]

    @property
    def static_dir(self) -> Path:
        return PROJECT_ROOT / "static"

    @property
    def database_path(self) -> Path:
        return self.data_dir / "noteeli.sqlite3"

    def ensure_runtime_dirs(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def ensure_content_root(self) -> None:
        self.content_root.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    return Settings()
