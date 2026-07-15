"""Server-side rendering helpers for the public-publish view.

The authenticated editor uses Toast UI, JSONEditor, CodeMirror, etc.
For the public read-only viewer we render markdown / code / json /
plain text straight into HTML on the server and let the frontend drop
it into a `<div>` — no need to ship a 600 KB editor bundle to a
visitor who only wants to read.
"""
from __future__ import annotations

import html as _html
import json
import re
from pathlib import Path
from urllib.parse import quote

import markdown
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from pygments.util import ClassNotFound


# ── Markdown ────────────────────────────────────────────────────


_MD_EXTENSIONS = [
    "extra",          # tables, fenced code, def_list, attr_list, footnotes…
    "sane_lists",     # don't merge adjacent lists of different types
    "smarty",         # smart quotes / dashes
    "codehilite",     # syntax highlighting via Pygments
    "toc",            # table of contents anchors
    "nl2br",          # newline → <br> (matches WYSIWYG behaviour)
]


def render_markdown_html(content: str, *, source_path: str = "", asset_url: str = "") -> str:
    """Convert markdown text to HTML.

    Image and link references whose target is a relative path inside
    the published item get rewritten to go through ``asset_url`` —
    typically the public preview endpoint scoped to the publish item
    — so embedded images load through the auth-free public proxy
    instead of leaking to a 404.

    Mermaid / PlantUML code blocks are preserved as ``<pre><code class
    ="language-mermaid">`` so the existing client-side mermaid CDN
    in the public viewer can render them.
    """
    md = markdown.Markdown(
        extensions=_MD_EXTENSIONS,
        extension_configs={
            "codehilite": {
                "css_class": "codehilite",
                "guess_lang": False,
                "linenums": False,
            },
        },
        output_format="html5",
    )
    html = md.convert(content or "")

    if asset_url and source_path:
        html = _rewrite_relative_assets(html, source_path, asset_url)

    return html


def render_code_html(content: str, filename: str) -> str:
    """Render a code file as a Pygments-highlighted HTML block.
    Falls back to a plain ``<pre>`` if the language can't be detected."""
    suffix = Path(filename).suffix.lstrip(".").lower()
    lexer = None
    if suffix:
        try:
            lexer = get_lexer_by_name(suffix, stripall=False)
        except ClassNotFound:
            lexer = None
    if lexer is None:
        # Plain `<pre>` for unknown extensions — preserves whitespace,
        # no highlighting.
        return f'<pre class="code-block">{_html.escape(content or "")}</pre>'
    formatter = HtmlFormatter(cssclass="codehilite", linenos=False)
    return highlight(content or "", lexer, formatter)


def render_json_html(content: str) -> str:
    """Pretty-print JSON with key/value highlighting."""
    try:
        parsed = json.loads(content) if content else None
        pretty = json.dumps(parsed, indent=2, ensure_ascii=False)
    except (ValueError, TypeError):
        pretty = content or ""
    lexer = get_lexer_by_name("json", stripall=False)
    formatter = HtmlFormatter(cssclass="codehilite", linenos=False)
    return highlight(pretty, lexer, formatter)


def render_text_html(content: str) -> str:
    """Plain-text fallback — preserves whitespace, no highlighting."""
    return f'<pre class="code-block">{_html.escape(content or "")}</pre>'


# ── CSS ─────────────────────────────────────────────────────────


def pygments_css() -> str:
    """Return the Pygments stylesheet (`.codehilite ...`) used by the
    syntax-highlighted blocks. Inlined into the public viewer template."""
    return HtmlFormatter(cssclass="codehilite").get_style_defs(".codehilite")


# ── Asset rewriting ─────────────────────────────────────────────


_RELATIVE_URL_RE = re.compile(
    r'(<(?:img|a)\b[^>]*?\b(?:src|href)=)'
    r'(["\'])'
    r'((?!https?:|mailto:|tel:|#|/|data:)[^"\']+)'
    r'\2',
    re.IGNORECASE,
)


def _rewrite_relative_assets(html: str, source_path: str, asset_url: str) -> str:
    """Rewrite ``<img src="rel/path">`` and ``<a href="rel/path">`` to
    point at the public preview endpoint.

    Skips absolute URLs (``http://…``, ``//…``, ``/…``), data URIs,
    fragments, mailto/tel. Anything else we treat as relative to the
    published source file's directory."""

    def _replace(match: re.Match) -> str:
        attr_prefix, quote_ch, target = match.group(1), match.group(2), match.group(3)
        # Links to other NOTES stay relative — the public viewer's click
        # handler resolves them and swaps the rendered note in place.
        # Only binary/asset targets go through the preview endpoint.
        if attr_prefix.lstrip("<").startswith("a") and re.search(
            r"\.(md|markdown)(?:[#?]|$)", target, re.IGNORECASE
        ):
            return match.group(0)
        # The publish preview endpoint understands ?source_path=…&target=…
        # — exactly the shape used by the regular embedded-asset route,
        # so the same backend code path resolves it.
        new_url = (
            f"{asset_url}"
            f"{'&' if '?' in asset_url else '?'}"
            f"source_path={quote(source_path, safe='')}&target={quote(target, safe='')}"
        )
        return f"{attr_prefix}{quote_ch}{new_url}{quote_ch}"

    return _RELATIVE_URL_RE.sub(_replace, html)
