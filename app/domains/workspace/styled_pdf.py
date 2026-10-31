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
RENDER_TIMEOUT_SECONDS = 60
MAX_HTML_BYTES = 8 * 1024 * 1024

_CSP = "default-src 'none'; img-src data:; style-src 'unsafe-inline'; font-src data:"

_BASE_CSS = """
@page { size: A4; margin: 16mm 15mm; }
* { box-sizing: border-box; }
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { margin: 0; font: 11pt/1.6 "Segoe UI", -apple-system, "Helvetica Neue", Roboto, Arial, sans-serif; overflow-wrap: anywhere; }
h1, h2, h3, h4 { line-height: 1.25; break-after: avoid; margin: 1.4em 0 .5em; }
h1 { font-size: 22pt; margin-top: 0; }
h2 { font-size: 16pt; }
h3 { font-size: 13pt; }
p, ul, ol, blockquote, pre, table { margin: 0 0 .9em; }
img { max-width: 100%; height: auto; break-inside: avoid; }
a { color: var(--accent); text-decoration: none; }
code { font: 9.5pt ui-monospace, "DejaVu Sans Mono", Menlo, Consolas, monospace; padding: .1em .35em; border-radius: 4px; background: var(--code-bg); color: var(--code-fg); }
pre { padding: .8em 1em; border-radius: 8px; background: var(--code-bg); color: var(--code-fg); white-space: pre-wrap; break-inside: avoid; }
pre code { padding: 0; background: none; font-size: 9pt; }
blockquote { padding: .2em 1em; border-left: 4px solid var(--accent); color: var(--muted); }
table { border-collapse: collapse; width: 100%; break-inside: auto; }
th, td { border: 1px solid var(--line); padding: 5px 9px; text-align: left; vertical-align: top; }
th { background: var(--th-bg); color: var(--th-fg); }
tr { break-inside: avoid; }
hr { border: 0; border-top: 1px solid var(--line); margin: 1.4em 0; }
li > input[type=checkbox] { margin-right: .4em; }
.doc-footer { margin-top: 2.4em; padding-top: .6em; border-top: 1px solid var(--line); font-size: 8.5pt; color: var(--muted); }
"""

_THEMES = {
    "light": """
:root { --bg:#fff; --fg:#1f2937; --muted:#6b7280; --line:#d6dbe3; --accent:#0e7490;
        --code-bg:#f1f5f9; --code-fg:#0f172a; --th-bg:#eef2f7; --th-fg:#0f172a; }
html, body { background: var(--bg); color: var(--fg); }
h1, h2, h3 { color: #0f172a; }
h1 { padding-bottom: .25em; border-bottom: 3px solid var(--accent); }
""",
    # Dark title band and code blocks on a light page — the "Noteeli" look.
    "mixed": """
:root { --bg:#fff; --fg:#1f2937; --muted:#64748b; --line:#d6dbe3; --accent:#0891b2;
        --code-bg:#0f172a; --code-fg:#e2e8f0; --th-bg:#0f172a; --th-fg:#f8fafc; }
html, body { background: var(--bg); color: var(--fg); }
h1 { background: #0f172a; color: #f8fafc; padding: .55em .8em; border-radius: 10px; border-left: 8px solid var(--accent); }
h2 { color: #0f172a; border-bottom: 2px solid var(--accent); padding-bottom: .15em; }
h3 { color: #155e75; }
code { background: #e2e8f0; color: #0f172a; }
pre code { background: none; color: inherit; }
""",
}


class StyledPdfError(Exception):
    """The browser is missing or failed to produce a PDF."""


_HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")


def build_document_html(
    title: str, body_html: str | None, text: str | None, style: str, accent: str | None = None
) -> str:
    if style not in STYLES:
        style = "light"
    # The active theme's accent colour (validated: it lands inside <style>).
    accent_css = f":root {{ --accent: {accent}; }}" if accent and _HEX_COLOR.match(accent) else ""
    if body_html is not None:
        body = re.sub(r"<script\b.*?</script\s*>", "", body_html, flags=re.I | re.S)
    else:
        body = f"<pre><code>{html_lib.escape(text or '')}</code></pre>"
    safe_title = html_lib.escape(title)
    return (
        "<!DOCTYPE html><html><head><meta charset=\"utf-8\">"
        f"<meta http-equiv=\"Content-Security-Policy\" content=\"{_CSP}\">"
        f"<title>{safe_title}</title><style>{_BASE_CSS}{_THEMES[style]}{accent_css}</style></head>"
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
        self, title: str, body_html: str | None, text: str | None, style: str, accent: str | None = None
    ) -> bytes:
        exe = self.executable()
        if exe is None:
            raise StyledPdfError("No Chromium/Chrome found for PDF rendering.")
        document = build_document_html(title, body_html, text, style, accent)
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
