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
    try:
        return max(
            int((static_dir / "app.css").stat().st_mtime),
            int((static_dir / "app.js").stat().st_mtime),
        )
    except OSError:
        return 0


def render_template(template_name: str, request, **context) -> HTMLResponse:
    template = template_lookup.get_template(template_name)
    body = template.render(
        request=request,
        settings=get_settings(),
        static_version=_static_version(),
        **context,
    )
    return HTMLResponse(body)
