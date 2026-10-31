"""E2E (headless Chromium): "Download" must never navigate the app window.

Update (1.15.1): in the iOS home-screen app ``window.open`` on an
attachment response produced a BLANK sheet that never offered to save.
Standalone iOS (``navigator.standalone``) now fetches the bytes and hands
a File to the share sheet (``navigator.share``); if the tap's user
activation has lapsed, or sharing files is unsupported, a "file ready"
dialog with explicit buttons appears instead.

Regression test for a phone-breaking bug. The tree context menu's
"Download" entry used `window.location.href = /api/download?...`. In a
browser tab that is harmless (an attachment response never replaces the
page), but in an installed PWA (home-screen icon, no browser chrome) iOS
rendered the PDF / markdown full-screen inside the app's webview with no
back button — the user was stuck.

Now:

* in a normal tab the download goes through a hidden ``<a download>``
  click — the page URL stays put and a download event fires;
* in standalone display mode the URL is opened in a NEW window
  (``window.open``) — iOS shows an in-app browser sheet with a "Done"
  button, Android just downloads. The app window itself never moves.

Same operational caveats as test_e2e_git_badge: the editor stack is
CDN-loaded, so the tests skip without outbound network or a Playwright
Chromium build.
"""

import re

import pytest

playwright_api = pytest.importorskip("playwright.sync_api")
from playwright.sync_api import sync_playwright  # noqa: E402

from test_e2e_git_badge import _cdn_reachable, _running_server  # noqa: E402

# Pretend to be an installed PWA: iOS exposes navigator.standalone, other
# browsers match the display-mode media query. We stub both, and record
# window.open calls instead of letting Chromium spawn a popup.
STANDALONE_INIT = """
  Object.defineProperty(navigator, 'standalone', { value: true, configurable: true });
  const realMatchMedia = window.matchMedia.bind(window);
  window.matchMedia = (q) => q.includes('display-mode: standalone')
    ? { matches: true, media: q, addEventListener() {}, removeEventListener() {} }
    : realMatchMedia(q);
"""
# iOS standalone: record share-sheet calls instead of opening the real one.
SHARE_STUB = """
  window.__shared = [];
  navigator.canShare = () => true;
  navigator.share = async (data) => {
    window.__shared.push((data.files || []).map((f) => ({ name: f.name, size: f.size })));
  };
"""
NO_SHARE_STUB = """
  navigator.canShare = () => false;
"""
RECORD_WINDOW_OPEN = """
  window.__openedWindows = [];
  window.open = (url, target, features) => {
    window.__openedWindows.push({ url: String(url), target, features });
    return null;
  };
"""


# The label is localised (UI language follows the browser); match any of
# the five dictionaries so the test doesn't depend on locale detection.
DOWNLOAD_LABEL = re.compile(r"^(Download|Pobierz|Descargar|Herunterladen|Скачать)$")


def _download_button(page):
    return page.locator("#tree-context-menu .context-menu-item", has_text=DOWNLOAD_LABEL).first


def _open_download_entry(page, filename: str) -> None:
    row = page.locator(".tree-link-file", has_text=filename).first
    row.wait_for(state="visible", timeout=15_000)
    row.click(button="right")
    _download_button(page).wait_for(state="visible", timeout=5_000)


def _launch(p):
    try:
        return p.chromium.launch(headless=True)
    except Exception as exc:  # pragma: no cover - environment dependent
        pytest.skip(f"Playwright Chromium unavailable: {exc}")


def _seed(content):
    (content / "raport.pdf").write_bytes(b"%PDF-1.4\n%fake\n")
    (content / "notatka.md").write_text("# Notatka\n", encoding="utf-8")


def test_download_in_browser_tab_keeps_page_and_fires_download(tmp_path):
    if not _cdn_reachable():
        pytest.skip("editor CDN unreachable — cannot load the real UI")

    with _running_server(tmp_path) as (base_url, content):
        _seed(content)
        with sync_playwright() as p:
            browser = _launch(p)
            try:
                context = browser.new_context(accept_downloads=True)
                page = context.new_page()
                page.goto(base_url, wait_until="networkidle")
                url_before = page.url

                _open_download_entry(page, "raport.pdf")
                with page.expect_download(timeout=10_000) as dl_info:
                    _download_button(page).click()
                download = dl_info.value

                assert download.suggested_filename == "raport.pdf"
                # The app window must not have navigated to the attachment.
                assert page.url == url_before
                assert page.locator("#tree-context-menu").count() == 1
            finally:
                browser.close()


def _standalone_context(browser, init_script):
    context = browser.new_context(
        viewport={"width": 393, "height": 852},
        device_scale_factor=3,
        is_mobile=True,
        has_touch=True,
    )
    context.add_init_script(STANDALONE_INIT + RECORD_WINDOW_OPEN + init_script)
    return context


def _start_mobile_download(page, filename):
    page.wait_for_function(
        "() => document.querySelector('.app-shell').classList.contains('sidebar-collapsed')",
        timeout=15_000,
    )
    page.locator("#sidebar-toggle").tap()
    _open_download_entry(page, filename)
    _download_button(page).click()


def test_download_in_ios_standalone_hands_file_to_share_sheet(tmp_path):
    if not _cdn_reachable():
        pytest.skip("editor CDN unreachable — cannot load the real UI")

    with _running_server(tmp_path) as (base_url, content):
        _seed(content)
        with sync_playwright() as p:
            browser = _launch(p)
            try:
                page = _standalone_context(browser, SHARE_STUB).new_page()
                page.goto(base_url, wait_until="networkidle")
                url_before = page.url

                _start_mobile_download(page, "notatka.md")
                page.wait_for_function("() => window.__shared.length === 1", timeout=10_000)

                shared = page.evaluate("() => window.__shared")
                assert shared[0][0]["name"] == "notatka.md"
                assert shared[0][0]["size"] > 0
                # No blank window: nothing is opened, the app stays put.
                assert page.evaluate("() => window.__openedWindows") == []
                assert page.url == url_before
            finally:
                browser.close()


def test_download_in_ios_standalone_without_file_share_shows_ready_dialog(tmp_path):
    if not _cdn_reachable():
        pytest.skip("editor CDN unreachable — cannot load the real UI")

    with _running_server(tmp_path) as (base_url, content):
        _seed(content)
        with sync_playwright() as p:
            browser = _launch(p)
            try:
                page = _standalone_context(browser, NO_SHARE_STUB).new_page()
                page.goto(base_url, wait_until="networkidle")

                _start_mobile_download(page, "notatka.md")
                dialog = page.locator(".modal-backdrop .modal-card h3", has_text="notatka.md")
                dialog.wait_for(state="visible", timeout=10_000)
                assert page.evaluate("() => window.__openedWindows") == []
            finally:
                browser.close()
