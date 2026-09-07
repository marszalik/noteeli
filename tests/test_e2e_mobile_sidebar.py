"""E2E (headless Chromium, iPhone-16-sized viewport): mobile drawer UX.

Regression tests for three phone-breaking bugs:

1. Expanding a folder in the overlay drawer used to CLOSE the drawer —
   the tap re-rendered the tree, detaching the tapped row before the
   click bubbled to the backdrop-close handler, whose `contains(target)`
   check then mistook it for an outside tap. Fixed with composedPath().
2. Picking a file did NOT close the drawer, so the note opened invisibly
   behind it.
3. The full-height drawer covered the topbar, making the hamburger
   untappable — no way to close the drawer from the toolbar. The drawer
   now starts below the topbar (--topbar-h).

Same operational caveats as test_e2e_git_badge: the editor stack is
CDN-loaded, so the tests skip without outbound network or a Playwright
Chromium build.
"""

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


def _shell_mode(page) -> str:
    return page.evaluate("() => document.querySelector('.app-shell').className")


def test_mobile_drawer_survives_folder_tap_and_closes_on_file_tap(tmp_path):
    if not _cdn_reachable():
        pytest.skip("editor CDN unreachable — cannot load the real UI")

    with _running_server(tmp_path) as (base_url, content):
        sub = content / "projekty"
        sub.mkdir()
        (sub / "plan.md").write_text("# Plan\n", encoding="utf-8")

        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
            except Exception as exc:
                pytest.skip(f"Playwright Chromium unavailable: {exc}")
            try:
                page = browser.new_context(**IPHONE).new_page()
                page.goto(base_url, wait_until="networkidle")

                # First mobile visit: the last-opened file auto-loads and
                # the drawer closes itself so the note is actually visible
                # (it used to stay open, covering the editor).
                editor = page.locator("#editor .ProseMirror >> visible=true")
                editor.wait_for(state="visible", timeout=15_000)
                page.wait_for_function(
                    "() => document.querySelector('.app-shell').classList.contains('sidebar-collapsed')",
                    timeout=15_000,
                )

                # Hamburger opens the overlay drawer.
                page.locator("#sidebar-toggle").tap()
                assert "sidebar-overlay" in _shell_mode(page)

                # Collapsing and re-expanding a folder must NOT close the
                # drawer (each tap re-renders the tree, which used to
                # detach the tapped row and fool the backdrop-close
                # handler into treating it as an outside tap).
                folder = page.locator(".tree-link-dir", has_text="projekty").first
                folder.tap()  # collapse (auto-select expanded it)
                expect(page.locator(".tree-link-file", has_text="plan.md")).to_be_hidden()
                assert "sidebar-overlay" in _shell_mode(page)
                folder.tap()  # expand again
                expect(page.locator(".tree-link-file", has_text="plan.md")).to_be_visible()
                assert "sidebar-overlay" in _shell_mode(page)

                # The hamburger stays tappable while the drawer is open
                # (the drawer sits below the topbar now) — and closes it.
                page.locator("#sidebar-toggle").tap()
                assert "sidebar-collapsed" in _shell_mode(page)
                page.locator("#sidebar-toggle").tap()
                assert "sidebar-overlay" in _shell_mode(page)

                # Picking a file loads it AND closes the drawer.
                page.locator(".tree-link-file", has_text="plan.md").first.tap()
                expect(page.locator("#current-file-label")).to_have_text(
                    "plan.md", timeout=15_000
                )
                # The drawer closes at the END of loadFile (the label above
                # updates mid-load), so poll rather than assert instantly.
                page.wait_for_function(
                    "() => document.querySelector('.app-shell').classList.contains('sidebar-collapsed')",
                    timeout=15_000,
                )

                # No horizontal overflow: the page must not be wider than
                # the phone.
                inner_w, doc_w = page.evaluate(
                    "() => [window.innerWidth, document.documentElement.scrollWidth]"
                )
                assert doc_w <= inner_w, f"page overflows: {doc_w}px > {inner_w}px"
            finally:
                browser.close()


def test_update_bar_appears_when_server_version_changes(tmp_path):
    """The voiceeli-style update hook: when /api/version starts reporting
    a different version than the one baked into the page, an update bar
    with a Refresh button appears; tapping it reloads with a cache-buster."""
    if not _cdn_reachable():
        pytest.skip("editor CDN unreachable — cannot load the real UI")

    with _running_server(tmp_path) as (base_url, _content):
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
            except Exception as exc:
                pytest.skip(f"Playwright Chromium unavailable: {exc}")
            try:
                page = browser.new_context(**IPHONE).new_page()
                page.goto(base_url, wait_until="networkidle")
                expect(page.locator("#update-bar")).to_have_count(0)

                # A deploy happens under the open tab:
                page.route(
                    "**/api/version",
                    lambda route: route.fulfill(json={"version": "99.0.0"}),
                )
                # The check fires when the tab regains focus.
                page.evaluate("window.dispatchEvent(new Event('focus'))")
                bar = page.locator("#update-bar")
                expect(bar).to_be_visible(timeout=10_000)

                bar.locator("button").tap()
                page.wait_for_url("**r=**", timeout=10_000)  # cache-busted reload
            finally:
                browser.close()
