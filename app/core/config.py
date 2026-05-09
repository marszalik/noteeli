from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
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

    # ── Hosted / SaaS mode ──────────────────────────────────────────────
    # When True:
    #   - any Google account may log in (no allowed_google_emails check)
    #   - subscription is required to access the workspace
    #   - local-filesystem storage backend is hidden
    # Toggle via NOTEELI_HOSTED_MODE=1.
    hosted_mode: bool = False
    # Comma-separated admin emails — bypass subscription check, can access /admin.
    admin_emails: str = ""

    # Paddle Billing (https://developer.paddle.com)
    paddle_api_key: str = ""
    paddle_webhook_secret: str = ""
    paddle_price_id: str = ""          # e.g. pri_01kr271nvqa591dbrehd141g79
    paddle_client_token: str = ""      # client-side token for Paddle.js
    # "sandbox" → sandbox-api.paddle.com  |  "live" → api.paddle.com
    paddle_environment: str = "sandbox"

    model_config = SettingsConfigDict(
        env_prefix="NOTEELI_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

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
