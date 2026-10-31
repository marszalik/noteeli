"""Noteeli-styled PDFs: the rendered note wrapped in Noteeli's own look
and printed by a headless Chromium/Chrome.

No Python dependency: any Chromium-family binary that understands
`--headless --print-to-pdf` will do (system chromium / google-chrome, a
Playwright download, or `NOTEELI_PDF_BROWSER`). The browser is used as a
renderer only: the page carries a CSP that forbids scripts and network
access, so the HTML a client sends (which is its own note, already
sanitised by the editor) cannot run code or reach other hosts. Images
must be inlined as data: URIs by the caller.
"""
from __future__ import annotations

import html as html_lib
import logging
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from app.core.config import Settings

logger = logging.getLogger(__name__)

STYLES = ("light", "mixed")
LAYOUTS = ("default", "clean", "magazine", "compact", "manuscript")
LANGS = ("pl", "en", "es", "de", "ru")
RENDER_TIMEOUT_SECONDS = 60
MAX_HTML_BYTES = 8 * 1024 * 1024

_CSP = "default-src 'none'; img-src data:; style-src 'unsafe-inline'; font-src data:"
_HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")

SANS = '"Lato", "Segoe UI", "Liberation Sans", "DejaVu Sans", Arial, sans-serif'
SERIF = '"IBM Plex Serif", Georgia, "Liberation Serif", "Nimbus Roman", "DejaVu Serif", serif'
MONO = 'ui-monospace, "DejaVu Sans Mono", "Liberation Mono", Menlo, Consolas, monospace'

# Used when the client sends no (or a broken) palette.
DEFAULT_PALETTE = {
    "bg": "#ffffff", "text": "#1f2937", "muted": "#6b7280",
    "accent": "#0e7490", "panel": "#f1f5f9",
}

_BASE_CSS = """
@page { size: A4; margin: 16mm 15mm; }
* { box-sizing: border-box; }
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { margin: 0; font: 11pt/1.6 var(--sans); overflow-wrap: anywhere; }
h1, h2, h3, h4 { line-height: 1.25; break-after: avoid; margin: 1.4em 0 .5em; }
h1 { font-size: 22pt; margin-top: 0; }
h2 { font-size: 16pt; }
h3 { font-size: 13pt; }
p, ul, ol, blockquote, pre, table { margin: 0 0 .9em; }
img { max-width: 100%; height: auto; break-inside: avoid; }
a { color: var(--accent-ink); text-decoration: none; }
code { font: 9.5pt var(--mono); padding: .1em .35em; border-radius: 4px; background: var(--inline-bg); color: var(--inline-fg); }
pre { padding: .8em 1em; border-radius: 8px; background: var(--code-bg); color: var(--code-fg); white-space: pre-wrap; break-inside: avoid; }
pre code { padding: 0; background: none; color: inherit; font-size: 9pt; }
blockquote { padding: .2em 1em; border-left: 4px solid var(--accent); color: var(--muted); }
table { border-collapse: collapse; width: 100%; break-inside: auto; }
th, td { border: 1px solid var(--line); padding: 5px 9px; text-align: left; vertical-align: top; }
th { background: var(--th-bg); color: var(--th-fg); }
tr { break-inside: avoid; }
hr { border: 0; border-top: 1px solid var(--line); margin: 1.4em 0; }
li > input[type=checkbox] { margin-right: .4em; }
html, body { background: var(--paper); color: var(--ink); }
h2, h3 { color: var(--head); }
"""

# Typography presets — the same five the editor offers as "Markdown
# rendering style", ported to print units.
_LAYOUTS = {
    "default": """
h1 { color: var(--head); padding-bottom: .25em; border-bottom: 3px double var(--accent); }
h2 { padding-bottom: .15em; border-bottom: 1px solid var(--line); }
""",
    "clean": """
h1 { font-size: 20pt; font-weight: 600; color: var(--head); margin-bottom: .5em; }
h2 { font-size: 15pt; font-weight: 600; }
h3 { font-size: 12.5pt; font-weight: 600; }
""",
    "magazine": """
body { font-family: var(--serif); line-height: 1.72; }
h1, h2, h3 { font-family: var(--serif); }
h1 { font-size: 27pt; font-weight: 600; letter-spacing: -.02em; line-height: 1.1; color: var(--head); }
h2 { font-size: 17pt; font-style: italic; font-weight: 500; }
h3 { font-size: 11.5pt; font-weight: 600; letter-spacing: .06em; text-transform: uppercase; color: var(--accent-ink); }
h1 + p::first-letter { float: left; font-size: 3.2em; font-weight: 700; line-height: .85; margin: .04em .08em 0 0; color: var(--accent-ink); }
""",
    "compact": """
body { font-size: 10pt; line-height: 1.42; }
h1 { font-size: 16pt; margin-bottom: .3em; padding-bottom: .2em; border-bottom: 1px solid var(--line); color: var(--head); }
h2 { font-size: 13pt; margin: .9em 0 .25em; }
h3 { font-size: 11pt; margin: .7em 0 .2em; }
p { margin: 0 0 .45em; } li { margin: .1em 0; }
pre, table, blockquote, ul, ol { margin-bottom: .6em; }
""",
    "manuscript": """
@page { margin: 20mm 22mm; }
body { font-family: var(--serif); line-height: 1.78; text-align: justify; hyphens: auto; }
h1, h2, h3 { font-family: var(--serif); }
h1 { font-size: 21pt; font-weight: 500; font-variant: small-caps; letter-spacing: .06em; text-align: center;
     margin: 1.4em 0 1em; color: var(--head); padding: .5em 0; border-top: 1px solid var(--accent); border-bottom: 1px solid var(--accent); }
h2 { font-size: 15pt; font-style: italic; font-weight: 500; text-align: center; margin: 1.4em 0 .6em; }
h3 { font-size: 12.5pt; font-style: italic; font-weight: 500; }
p + p { text-indent: 1.8em; margin-top: 0; }
""",
}

# Extras only the "mixed" colour scheme adds: dark band under the title
# (not for the book-like manuscript layout, which has its own rules).
_MIXED_EXTRA = """
h1 { background: var(--band); color: var(--band-fg); padding: .55em .8em; border-radius: 10px;
     border-left: 8px solid var(--accent); border-bottom: 0; }
h2 { border-bottom: 2px solid var(--accent); padding-bottom: .15em; }
"""
_MIXED_EXTRA_MANUSCRIPT = """
h1 { background: var(--band); color: var(--band-fg); border: 0; border-radius: 6px; padding: .6em 0; }
h2 { color: var(--accent-ink); }
"""


def _rgb(hex_color: str) -> tuple[int, int, int]:
    return tuple(int(hex_color[i:i + 2], 16) for i in (1, 3, 5))  # type: ignore[return-value]


def _luminance(hex_color: str) -> float:
    r, g, b = (c / 255 for c in _rgb(hex_color))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _shade(hex_color: str, factor: float) -> str:
    return "#" + "".join(f"{round(c * factor):02x}" for c in _rgb(hex_color))


def _clean_palette(palette: dict | None, accent: str | None) -> dict:
    result = dict(DEFAULT_PALETTE)
    for key, value in (palette or {}).items():
        if key in result and isinstance(value, str) and _HEX_COLOR.match(value):
            result[key] = value.lower()
    if accent and _HEX_COLOR.match(accent):
        result["accent"] = accent.lower()
    return result


def _colour_variables(style: str, pal: dict) -> str:
    """The page is always light (readable, printable). The theme supplies
    the character: its accent, its dark surface for bands and code, and —
    for light themes — its paper and ink."""
    dark_theme = _luminance(pal["bg"]) < 0.4
    accent = pal["accent"]
    accent_ink = _shade(accent, 0.6) if _luminance(accent) > 0.4 else accent
    if dark_theme:
        paper, ink, muted, head = "#fffdf8", "#1f2430", "#667085", "#111827"
        band, band_fg = pal["bg"], pal["text"]
        code_bg, code_fg = pal["panel"], pal["text"]
    else:
        paper, ink, muted, head = pal["bg"], pal["text"], pal["muted"], pal["text"]
        band, band_fg = pal["text"], pal["bg"]
        code_bg, code_fg = pal["text"], pal["bg"]
    if style == "mixed":
        th_bg, th_fg = band, band_fg
        inline_bg, inline_fg = f"color-mix(in srgb, {ink} 10%, {paper})", ink
    else:  # light: every surface is a faint tint of the page
        code_bg, code_fg = f"color-mix(in srgb, {ink} 6%, {paper})", ink
        th_bg, th_fg = f"color-mix(in srgb, {accent} 14%, {paper})", head
        inline_bg, inline_fg = code_bg, ink
    return (
        ":root {"
        f" --paper:{paper}; --ink:{ink}; --muted:{muted}; --head:{head};"
        f" --accent:{accent}; --accent-ink:{accent_ink};"
        f" --line:color-mix(in srgb, {ink} 18%, {paper});"
        f" --band:{band}; --band-fg:{band_fg};"
        f" --code-bg:{code_bg}; --code-fg:{code_fg}; --inline-bg:{inline_bg}; --inline-fg:{inline_fg};"
        f" --th-bg:{th_bg}; --th-fg:{th_fg};"
        f" --sans:{SANS}; --serif:{SERIF}; --mono:{MONO}; }}"
    )


class StyledPdfError(Exception):
    """The browser is missing or failed to produce a PDF."""


_HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")


def build_document_html(
    title: str,
    body_html: str | None,
    text: str | None,
    style: str,
    accent: str | None = None,
    layout: str = "default",
    palette: dict | None = None,
    lang: str = "pl",
) -> str:
    if style not in STYLES:
        style = "light"
    if layout not in LAYOUTS:
        layout = "default"
    if lang not in LANGS:
        lang = "pl"
    pal = _clean_palette(palette, accent)
    if body_html is not None:
        body = re.sub(r"<script\b.*?</script\s*>", "", body_html, flags=re.I | re.S)
    else:
        body = f"<pre><code>{html_lib.escape(text or '')}</code></pre>"
    css = _BASE_CSS + _colour_variables(style, pal) + _LAYOUTS[layout]
    if style == "mixed":
        css += _MIXED_EXTRA_MANUSCRIPT if layout == "manuscript" else _MIXED_EXTRA
    safe_title = html_lib.escape(title)
    return (
        f"<!DOCTYPE html><html lang=\"{lang}\"><head><meta charset=\"utf-8\">"
        f"<meta http-equiv=\"Content-Security-Policy\" content=\"{_CSP}\">"
        f"<title>{safe_title}</title><style>{css}</style></head>"
        f"<body>{body}</body></html>"
    )


class StyledPdfRenderer:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._executable: str | None | bool = False

    def executable(self) -> str | None:
        if self._executable is False:
            self._executable = self._find_executable()
        return self._executable  # type: ignore[return-value]

    def available(self) -> bool:
        return self.executable() is not None

    def status(self) -> dict:
        return {"available": self.available(), "styles": list(STYLES)}

    def _find_executable(self) -> str | None:
        configured = (self.settings.pdf_browser or "").strip()
        if configured.lower() in ("off", "none", "0", "false"):
            return None
        if configured:
            path = Path(configured).expanduser()
            if path.is_file():
                return str(path)
            return shutil.which(configured)
        for candidate in ("chromium", "chromium-browser", "google-chrome", "google-chrome-stable", "chrome"):
            found = shutil.which(candidate)
            if found:
                return found
        # Playwright's download cache (headless shell or full chromium).
        cache = Path.home() / ".cache" / "ms-playwright"
        for pattern in ("chromium_headless_shell-*/*/chrome-headless-shell", "chromium-*/chrome-linux*/chrome"):
            for found in sorted(cache.glob(pattern), reverse=True):
                if found.is_file():
                    return str(found)
        return None

    def render(
        self,
        title: str,
        body_html: str | None,
        text: str | None,
        style: str,
        accent: str | None = None,
        layout: str = "default",
        palette: dict | None = None,
        lang: str = "pl",
    ) -> bytes:
        exe = self.executable()
        if exe is None:
            raise StyledPdfError("No Chromium/Chrome found for PDF rendering.")
        document = build_document_html(title, body_html, text, style, accent, layout, palette, lang)
        if len(document.encode("utf-8")) > MAX_HTML_BYTES:
            raise StyledPdfError("The document is too large to render.")
        with tempfile.TemporaryDirectory(prefix="noteeli-pdf-") as tmp:
            tmp_dir = Path(tmp)
            source = tmp_dir / "doc.html"
            target = tmp_dir / "doc.pdf"
            source.write_text(document, encoding="utf-8")
            command = [
                exe, "--headless", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
                "--disable-dev-shm-usage", f"--user-data-dir={tmp_dir / 'profile'}",
                "--no-pdf-header-footer", "--print-to-pdf-no-header",
                f"--print-to-pdf={target}", source.as_uri(),
            ]
            try:
                subprocess.run(command, capture_output=True, timeout=RENDER_TIMEOUT_SECONDS, check=False)
            except subprocess.TimeoutExpired as exc:
                raise StyledPdfError("PDF rendering timed out.") from exc
            except OSError as exc:
                raise StyledPdfError(f"Could not start the browser: {exc}") from exc
            if not target.is_file() or target.stat().st_size == 0:
                raise StyledPdfError("The browser did not produce a PDF.")
            return target.read_bytes()
