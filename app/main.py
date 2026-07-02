from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import get_settings
from app.domains.auth.router import router as auth_router
from app.domains.git.router import router as git_router
from app.domains.publish.router import router as publish_router
from app.domains.workspace.router import router as workspace_router
from app.domains.workspace.service import DemoReadOnlyError, StorageNotConfiguredError


def _seed_demo_content_if_needed(settings) -> None:
    """When demo mode is on, copy the bundled `demo-content/` tree into
    the configured content_root if the root looks empty. The whole
    point of the demo is read-only access to a curated set of notes —
    we don't trust whatever was in content_root before."""
    if not settings.demo_mode:
        return
    import shutil
    from pathlib import Path

    bundled = Path(__file__).resolve().parents[1] / "demo-content"
    if not bundled.is_dir():
        return
    target = settings.content_root
    target.mkdir(parents=True, exist_ok=True)
    # Refresh on every startup so an admin can update the bundled
    # demo content and just restart the service.
    for entry in target.iterdir():
        if entry.is_dir():
            shutil.rmtree(entry, ignore_errors=True)
        else:
            try:
                entry.unlink()
            except OSError:
                pass
    for entry in bundled.iterdir():
        dst = target / entry.name
        if entry.is_dir():
            shutil.copytree(entry, dst)
        else:
            shutil.copy2(entry, dst)


def _seed_demo_preferences_if_needed(settings) -> None:
    """Demo's initial UI: English + Webnote theme. Writes straight to
    the preferences SQLite (which lives in /tmp on the demo box and is
    wiped on every service restart), so visitors always land on the
    same first-impression view regardless of what previous visitors
    might have clicked."""
    if not settings.demo_mode:
        return
    from app.domains.preferences.repository import PreferencesRepository

    repo = PreferencesRepository(settings)
    # We bypass the WorkspaceService write guard on purpose — this
    # runs as part of process startup, not a user request.
    repo.update_app_preferences(
        language="en",
        theme_mode="webnote",
        content_root=str(settings.content_root),
    )


def create_app() -> FastAPI:
    settings = get_settings()
    settings.ensure_runtime_dirs()
    # File logs first, so everything from startup onward is captured.
    from app.core.logging import setup_file_logging
    setup_file_logging(settings)
    _seed_demo_content_if_needed(settings)
    _seed_demo_preferences_if_needed(settings)

    app = FastAPI(title=settings.app_name)

    # In hosted mode, the session cookie is set by noteeli.com and shared
    # across .noteeli.com (cookie domain). Both apps MUST use the same
    # session_secret and cookie name.
    _session_kwargs: dict = {
        "secret_key": settings.session_secret,
        "same_site": "lax",
        "https_only": True if settings.hosted_mode else False,
        "session_cookie": "noteeli_session" if settings.hosted_mode else "session",
    }
    if settings.hosted_mode and settings.session_cookie_domain:
        _session_kwargs["domain"] = settings.session_cookie_domain
    app.add_middleware(SessionMiddleware, **_session_kwargs)

    app.mount("/static", StaticFiles(directory=str(settings.static_dir)), name="static")

    app.include_router(auth_router)
    app.include_router(workspace_router)
    app.include_router(git_router)
    # Publish routes are registered last so that more-specific paths
    # like /login and /api/* always win over the catch-all /{id}/{slug}
    # public viewer route.
    app.include_router(publish_router)

    # Demo mode: any service-layer write raises DemoReadOnlyError. Catch
    # it here so every endpoint that calls a guarded method automatically
    # responds with 403 + a friendly Polish/English message — no need to
    # add a try/except clause to every route.
    @app.exception_handler(DemoReadOnlyError)
    async def _demo_readonly_handler(request: Request, exc: DemoReadOnlyError):
        return JSONResponse(status_code=403, content={"detail": str(exc), "demo": True})

    @app.exception_handler(StorageNotConfiguredError)
    async def _storage_not_configured_handler(request: Request, exc: StorageNotConfiguredError):
        return JSONResponse(
            status_code=412,
            content={"detail": str(exc), "needs_storage_setup": True},
        )

    # The PWA is gone, but we keep serving service-worker.js as a
    # kill-switch (see static/service-worker.js): browsers still running
    # the old Noteeli SW re-fetch this script, which unregisters itself and
    # purges caches. no-store so the kill-switch is never itself cached.
    @app.get("/service-worker.js", include_in_schema=False)
    async def service_worker():
        return FileResponse(
            settings.static_dir / "service-worker.js",
            media_type="application/javascript",
            headers={
                "Service-Worker-Allowed": "/",
                "Cache-Control": "no-store, max-age=0",
            },
        )

    return app


app = create_app()
