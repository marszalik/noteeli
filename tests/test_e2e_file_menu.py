"""E2E (headless Chromium, phone viewport): the topbar file menu offers
Download, Save as PDF and Read aloud for the open document, so the sidebar
is not needed just to export what you are looking at."""

import pytest

playwright_api = pytest.importorskip("playwright.sync_api")
from playwright.sync_api import expect, sync_playwright  # noqa: E402

from test_e2e_git_badge import _cdn_reachable, _running_server  # noqa: E402

IPHONE = {
    "viewport": {"width": 393, "height": 852},
    "device_scale_factor": 3,
    "is_mobile": True,
    "has_touch": True,
}

SPEECH_STUB = """
window.__spoken = [];
window.__cancelled = 0;
window.SpeechSynthesisUtterance = function (text) { this.text = text; };
Object.defineProperty(window, 'speechSynthesis', { configurable: true, value: {
  speak(u) { window.__spoken.push(u.text); setTimeout(() => u.onend && u.onend(), 5); },
  cancel() { window.__cancelled++; },
  getVoices() { return []; },
}});
window.__printed = 0;
window.print = () => {
  const root = document.getElementById('print-root');
  window.__printed++;
  window.__printHtml = root ? root.innerHTML : '';
};
"""


def test_file_menu_download_pdf_and_read_aloud(tmp_path):
    if not _cdn_reachable():
        pytest.skip("editor CDN unreachable — cannot load the real UI")

    with _running_server(tmp_path) as (base_url, content):
        (content / "note.md").write_text(
            "# Tytul\n\nPierwsze zdanie. Drugie zdanie.\n", encoding="utf-8"
        )
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
            except Exception as exc:
                pytest.skip(f"Playwright Chromium unavailable: {exc}")
            try:
                page = browser.new_context(**IPHONE, accept_downloads=True).new_page()
                page.add_init_script(SPEECH_STUB)
                page.add_init_script("localStorage.setItem('last-opened-file','note.md')")
                page.goto(base_url, wait_until="networkidle")
                expect(page.locator("#current-file-label")).to_have_text("note.md", timeout=15_000)

                # Visible on the phone topbar without opening the drawer.
                toggle = page.locator("#file-menu-toggle")
                expect(toggle).to_be_visible()

                # Read aloud
                toggle.tap()
                page.locator("#file-read-aloud").tap()
                page.wait_for_function("() => window.__spoken.length >= 1")
                spoken = " ".join(page.evaluate("() => window.__spoken"))
                assert "Pierwsze zdanie." in spoken and "Tytul" in spoken

                # Save as PDF prints only the rendered document.
                toggle.tap()
                page.locator("#file-pdf").tap()
                page.wait_for_function("() => window.__printed === 1")
                assert "Tytul" in page.evaluate("() => window.__printHtml")

                # Download
                toggle.tap()
                with page.expect_download() as info:
                    page.locator("#file-download").tap()
                assert info.value.suggested_filename == "note.md"
            finally:
                browser.close()


def test_noteeli_pdf_dialog_saves_pdf_next_to_the_note(tmp_path):
    if not _cdn_reachable():
        pytest.skip("editor CDN unreachable — cannot load the real UI")

    with _running_server(tmp_path) as (base_url, content):
        (content / "note.md").write_text("# Tytul\n\nTekst.\n", encoding="utf-8")
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
            except Exception as exc:
                pytest.skip(f"Playwright Chromium unavailable: {exc}")
            try:
                page = browser.new_context(**IPHONE).new_page()
                page.add_init_script("localStorage.setItem('last-opened-file','note.md')")
                page.goto(base_url, wait_until="networkidle")
                expect(page.locator("#current-file-label")).to_have_text("note.md", timeout=15_000)

                page.locator("#file-menu-toggle").tap()
                page.locator("#file-noteeli-pdf").tap()
                dialog = page.locator(".modal-card", has_text="Noteeli PDF")
                expect(dialog).to_be_visible()
                # Dark/light is decided by the profile's theme; both styles offered.
                expect(dialog.locator('input[name="npdf-style"]')).to_have_count(2)
                create = dialog.locator("footer button.button-primary")
                if create.is_disabled():
                    pytest.skip("no Chromium/Chrome for the server-side PDF")
                create.tap()
                expect(dialog.locator(".npdf-result")).to_contain_text(
                    "note-noteeli.pdf", timeout=60_000
                )
                assert (content / "note-noteeli.pdf").read_bytes().startswith(b"%PDF")
            finally:
                browser.close()
