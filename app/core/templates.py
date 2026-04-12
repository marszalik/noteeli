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


def render_template(template_name: str, request, **context) -> HTMLResponse:
    template = template_lookup.get_template(template_name)
    body = template.render(request=request, settings=get_settings(), **context)
    return HTMLResponse(body)
