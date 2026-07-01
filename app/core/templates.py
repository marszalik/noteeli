from fastapi.responses import HTMLResponse
from mako.lookup import TemplateLookup

from app.core.config import get_settings


settings = get_settings()
template_lookup = TemplateLookup(
    directories=[str(path) for path in settings.template_dirs],
    input_encoding="utf-8",
    output_encoding=None,
    filesystem_checks=True,
)


def _static_version() -> int:
    """Return the max mtime of the key static files as a cache-busting token.
    Recomputed on every request — cheap (just two stat() calls) and means any
    CSS/JS change is immediately visible without a server restart."""
    static_dir = settings.static_dir
    candidates = [
        static_dir / "app.css",
        static_dir / "app.js",
        static_dir / "icon-192.png",
        static_dir / "icon-512.png",
        static_dir / "apple-touch-icon.png",
        static_dir / "favicon.svg",
    ]
    try:
        return max(int(p.stat().st_mtime) for p in candidates if p.exists())
    except (OSError, ValueError):
        return 0


def render_template(template_name: str, request, **context) -> HTMLResponse:
    template = template_lookup.get_template(template_name)
    body = template.render(
        request=request,
        settings=get_settings(),
        static_version=_static_version(),
        **context,
    )
    # Never let the app-shell HTML go stale. The document carries the
    # cache-busting ?v=<mtime> asset URLs *and* the inline service-worker
    # self-heal script (see base.mako). If a browser or proxy served a
    # cached copy of this HTML, it would pin outdated JS/CSS and the
    # self-heal would never get a chance to run. no-store guarantees every
    # navigation re-fetches a fresh shell — the linchpin for recovering
    # clients (esp. iOS/Safari) stuck on an old service worker.
    return HTMLResponse(body, headers={"Cache-Control": "no-store"})
