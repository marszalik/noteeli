from pathlib import Path

import pytest

from app.domains.workspace.service import DemoReadOnlyError
from app.domains.workspace.styled_pdf import StyledPdfError, build_document_html
from test_workspace_service import build_service


def test_document_html_is_locked_down_and_themed():
    html = build_document_html(
        "T<x>", "<h1>Hi</h1><script>alert(1)</script>", None, "mixed", accent="#112233"
    )
    assert "<script" not in html
    assert "default-src 'none'" in html  # no scripts, no network
    assert "<title>T&lt;x&gt;</title>" in html
    assert "--accent:#112233" in html


def test_accent_is_validated_because_it_lands_in_css():
    html = build_document_html("t", "<p>x</p>", None, "light", accent="red;}</style><script>")
    assert "red;}" not in html


def test_plain_text_is_escaped_into_a_code_block_and_unknown_style_falls_back():
    html = build_document_html("t", None, "a <b> & c", "neon")
    assert "<pre><code>a &lt;b&gt; &amp; c</code></pre>" in html
    assert "--band:" in html and "--th-bg:color-mix" in html  # light scheme


def test_pdf_is_saved_next_to_the_note_under_its_own_name(tmp_path: Path, monkeypatch):
    root = tmp_path / "vault"
    (root / "sub").mkdir(parents=True)
    (root / "sub" / "note.md").write_text("# x", encoding="utf-8")
    (root / "sub" / "note.pdf").write_bytes(b"hand-made")
    service = build_service(root)
    monkeypatch.setattr(service.styled_pdf, "render", lambda *a, **k: b"%PDF-fake")

    saved = service.create_styled_pdf("sub/note.md", "<h1>x</h1>", None, "mixed")

    assert saved == "sub/note-noteeli.pdf"
    assert (root / saved).read_bytes() == b"%PDF-fake"
    assert (root / "sub" / "note.pdf").read_bytes() == b"hand-made"  # untouched


def test_pdf_creation_is_blocked_in_demo_mode(tmp_path: Path):
    root = tmp_path / "vault"
    root.mkdir()
    (root / "a.md").write_text("x", encoding="utf-8")
    with pytest.raises(DemoReadOnlyError):
        build_service(root, demo_mode=True).create_styled_pdf("a.md", "<p>x</p>", None, "light")


def test_missing_browser_is_reported(tmp_path: Path):
    root = tmp_path / "vault"
    root.mkdir()
    service = build_service(root)
    service.styled_pdf._executable = None
    assert service.styled_pdf.status()["available"] is False
    with pytest.raises(StyledPdfError):
        service.styled_pdf.render("t", "<p>x</p>", None, "light")


def test_real_browser_renders_a_pdf(tmp_path: Path):
    service = build_service(tmp_path / "vault")
    if not service.styled_pdf.available():
        pytest.skip("no Chromium/Chrome on this machine")
    pdf = service.styled_pdf.render("t", "<h1>Zażółć</h1><p>tekst</p>", None, "mixed")
    assert pdf.startswith(b"%PDF")


NOTEELI = {"bg": "#08111a", "text": "#edf3f8", "muted": "#9db0c2", "accent": "#f2b01d", "panel": "#14273b"}
CREAM = {"bg": "#f4efe4", "text": "#2f261c", "muted": "#756652", "accent": "#0f766e", "panel": "#fffaf1"}


def test_theme_palette_drives_the_colours_and_page_stays_light():
    dark_theme = build_document_html("t", "<p>x</p>", None, "mixed", palette=NOTEELI)
    light_theme = build_document_html("t", "<p>x</p>", None, "mixed", palette=CREAM)
    # dark theme: its dark surface becomes the band, the page is white-ish
    assert "--band:#08111a" in dark_theme and "--paper:#fffdf8" in dark_theme
    # light theme: its cream paper and brown ink are used
    assert "--paper:#f4efe4" in light_theme and "--ink:#2f261c" in light_theme
    assert dark_theme != light_theme


def test_each_markdown_layout_has_its_own_typography():
    docs = {
        name: build_document_html("t", "<p>x</p>", None, "light", layout=name)
        for name in ("default", "clean", "magazine", "compact", "manuscript")
    }
    assert len(set(docs.values())) == 5
    assert "first-letter" in docs["magazine"]
    assert "text-indent" in docs["manuscript"] and 'lang="pl"' in docs["manuscript"]


def test_bad_palette_values_never_reach_the_css():
    html = build_document_html(
        "t", "<p>x</p>", None, "light",
        palette={"accent": "red;}</style><script>", "bg": "#zzzzzz"}, layout="evil", lang="x\">",
    )
    assert "<script>" not in html.split("</style>")[0] and "red;}" not in html
    assert 'lang="pl"' in html
