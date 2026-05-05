from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import get_settings
from app.domains.auth.router import router as auth_router
from app.domains.workspace.router import router as workspace_router
from app.domains.workspace.service import DemoReadOnlyError


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


def create_app() -> FastAPI:
    settings = get_settings()
    settings.ensure_runtime_dirs()
    _seed_demo_content_if_needed(settings)

    app = FastAPI(title=settings.app_name)
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.session_secret,
        same_site="lax",
        https_only=False,
    )
    app.mount("/static", StaticFiles(directory=str(settings.static_dir)), name="static")

    app.include_router(auth_router)
    app.include_router(workspace_router)

    # Demo mode: any service-layer write raises DemoReadOnlyError. Catch
    # it here so every endpoint that calls a guarded method automatically
    # responds with 403 + a friendly Polish/English message — no need to
    # add a try/except clause to every route.
    @app.exception_handler(DemoReadOnlyError)
    async def _demo_readonly_handler(request: Request, exc: DemoReadOnlyError):
        return JSONResponse(status_code=403, content={"detail": str(exc), "demo": True})

    # PWA: service worker must be served from the root scope so it can
    # intercept all same-origin requests (scope = /).
    @app.get("/service-worker.js", include_in_schema=False)
    async def service_worker():
        return FileResponse(
            settings.static_dir / "service-worker.js",
            media_type="application/javascript",
            headers={"Service-Worker-Allowed": "/"},
        )

    # PWA: web app manifest
    @app.get("/manifest.webmanifest", include_in_schema=False)
    async def web_manifest():
        return FileResponse(
            settings.static_dir / "manifest.webmanifest",
            media_type="application/manifest+json",
        )

    return app


app = create_app()
