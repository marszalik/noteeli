from functools import lru_cache

from authlib.integrations.starlette_client import OAuth
from fastapi import HTTPException, Request

from app.core.config import Settings, get_settings


LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}


@lru_cache
def get_oauth() -> OAuth:
    settings = get_settings()
    oauth = OAuth()
    if settings.google_client_id and settings.google_client_secret:
        oauth.register(
            name="google",
            client_id=settings.google_client_id,
            client_secret=settings.google_client_secret,
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            client_kwargs={"scope": "openid email profile"},
        )
    return oauth


class AuthService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def _request_host(self, request: Request) -> str:
        forwarded_host = request.headers.get("x-forwarded-host")
        if forwarded_host:
            return forwarded_host.split(",")[0].strip().split(":")[0]
        return request.url.hostname or ""

    def is_local_request(self, request: Request) -> bool:
        return self._request_host(request) in LOCAL_HOSTS

    def get_current_user(self, request: Request) -> dict | None:
        if self.is_local_request(request):
            return {
                "email": "local@noteeli",
                "name": "Lokalny dostep",
                "is_local": True,
            }
        return request.session.get("user")

    def require_api_access(self, request: Request) -> dict:
        user = self.get_current_user(request)
        if user is None:
            raise HTTPException(status_code=401, detail="Authentication required.")
        return user

    def google_is_configured(self) -> bool:
        return bool(self.settings.google_client_id and self.settings.google_client_secret)

    def google_emails_configured(self) -> bool:
        """Return True if at least one allowed email is set in .env."""
        return bool(self.settings.allowed_google_emails.strip())

    def google_email_is_allowed(self, email: str) -> bool:
        """Return True only if the email is on the explicit allowlist.

        If NOTEELI_ALLOWED_GOOGLE_EMAILS is empty, nobody is allowed —
        the login page shows a hint to edit .env.
        """
        raw = self.settings.allowed_google_emails.strip()
        if not raw:
            return False
        allowed = {e.strip().lower() for e in raw.split(",") if e.strip()}
        return email.strip().lower() in allowed

    def password_login_configured(self) -> bool:
        return bool(self.settings.local_username and self.settings.local_password)

    def check_password(self, username: str, password: str) -> bool:
        if not self.password_login_configured():
            return False
        return (
            username == self.settings.local_username
            and password == self.settings.local_password
        )

    def get_google_client(self):
        return get_oauth().create_client("google")
