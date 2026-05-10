"""ASGI middleware that records page-views into the shared analytics DB.

Only active in hosted mode — on a self-host install, no admin reads
this data so writing it is just noise.
"""
from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.config import get_settings
from app.domains.analytics.service import record_pageview


class PageviewMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, default_domain: str = "app.noteeli.com") -> None:
        super().__init__(app)
        self._default_domain = default_domain
        self._enabled = get_settings().hosted_mode

    async def dispatch(self, request, call_next):
        response = await call_next(request)
        if not self._enabled:
            return response
        if request.method != "GET":
            return response
        if response.status_code >= 400:
            return response

        host = (
            request.headers.get("x-forwarded-host")
            or request.headers.get("host")
            or self._default_domain
        ).split(":")[0].lower()

        ip = (
            request.headers.get("x-forwarded-for", "").split(",")[0].strip()
            or (request.client.host if request.client else "")
        )
        ua = request.headers.get("user-agent", "")
        ref = request.headers.get("referer", "")

        user = request.session.get("user") if hasattr(request, "session") else None
        user_id = (user or {}).get("db_id")

        record_pageview(
            domain=host,
            path=request.url.path,
            referrer=ref,
            ip=ip,
            user_agent=ua,
            user_id=user_id,
        )
        return response
