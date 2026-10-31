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
    assert "--accent: #112233" in html


def test_accent_is_validated_because_it_lands_in_css():
    html = build_document_html("t", "<p>x</p>", None, "light", accent="red;}</style><script>")
    assert "red;}" not in html


def test_plain_text_is_escaped_into_a_code_block_and_unknown_style_falls_back():
    html = build_document_html("t", None, "a <b> & c", "neon")
    assert "<pre><code>a &lt;b&gt; &amp; c</code></pre>" in html
    assert "--bg:#fff" in html  # light


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
