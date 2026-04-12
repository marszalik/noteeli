from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import get_settings
from app.domains.auth.router import router as auth_router
from app.domains.workspace.router import router as workspace_router


def create_app() -> FastAPI:
    settings = get_settings()
    settings.ensure_runtime_dirs()

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
    return app


app = create_app()
