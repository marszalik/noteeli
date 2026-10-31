"""E2E (headless Chromium): tree mutations patch the sidebar locally.

Regression test — creating or saving a file used to re-download the whole
/api/tree payload (a full recursive re-scan server-side), which made the
sidebar crawl on big workspaces. The frontend now patches its in-memory
tree instead: after the initial load, creating a file and manually saving
it must not trigger a single further /api/tree request, while the new
file still shows up in the tree and the git badge still updates.

Same operational caveats as test_e2e_git_badge: the app shell loads its
editor stack from CDNs, so the test skips without outbound network or a
Playwright Chromium build.
"""

from urllib.parse import parse_qs, urlparse

import pytest

playwright_api = pytest.importorskip("playwright.sync_api")
from playwright.sync_api import expect, sync_playwright  # noqa: E402

from test_e2e_git_badge import _cdn_reachable, _running_server  # noqa: E402


def test_create_and_save_do_not_reload_the_tree(tmp_path):
    if not _cdn_reachable():
        pytest.skip("editor CDN unreachable — cannot load the real UI")

    with _running_server(tmp_path) as (base_url, _content):
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
            except Exception as exc:  # missing browser build
                pytest.skip(f"Playwright Chromium unavailable: {exc}")
            try:
                page = browser.new_page()
                tree_requests = []
                page.on(
                    "request",
                    lambda request: tree_requests.append(request.url)
                    if urlparse(request.url).path.endswith("/api/tree")
                    else None,
                )
                page.goto(base_url, wait_until="networkidle")
                expect(
                    page.locator(".tree-link-file", has_text="note.md")
                ).to_be_visible()
                assert len(tree_requests) == 1  # the initial load, nothing else

                # Create a file via the sidebar "+" — the row must appear
                # from the local patch, not from a tree re-download.
                page.locator("#new-file").click()
                page.locator("#create-name-input").fill("zzz-nowa")
                page.locator("#confirm-create").click()
                new_row = page.locator(".tree-link-file", has_text="zzz-nowa.md")
                expect(new_row).to_be_visible(timeout=15_000)
                # The untracked file lights the git badge via the status
                # refresh that replaced the tree reload.
                expect(page.locator("#git-menu-badge")).to_have_text(
                    "1", timeout=15_000
                )

                # A manual save must not reload the tree either.
                editor = page.locator("#editor .ProseMirror >> visible=true")
                editor.wait_for(state="visible", timeout=15_000)
                editor.click()
                page.keyboard.type("Zapis bez przeladowania drzewa.")
                page.locator("#save-button").click()
                expect(new_row).to_be_visible()

                page.wait_for_timeout(1_500)  # let any stray request land
                assert len(tree_requests) == 1
            finally:
                browser.close()


def test_tree_loads_one_level_and_fetches_folders_on_open(tmp_path):
    """Lazy tree: the sidebar asks for depth=1, opens deeper folders on
    demand, keeps them open across a refresh, and searches server-side."""
    if not _cdn_reachable():
        pytest.skip("editor CDN unreachable — cannot load the real UI")

    with _running_server(tmp_path) as (base_url, content):
        deep = content / "proj" / "inner" / "deeper"
        deep.mkdir(parents=True)
        (deep / "needle-doc.md").write_text("# deep\n", encoding="utf-8")
        (content / "proj" / "top.md").write_text("# top\n", encoding="utf-8")

        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
            except Exception as exc:  # missing browser build
                pytest.skip(f"Playwright Chromium unavailable: {exc}")
            try:
                page = browser.new_page()
                tree_requests = []
                page.on(
                    "request",
                    lambda request: tree_requests.append(request.url)
                    if urlparse(request.url).path.endswith("/api/tree")
                    else None,
                )
                # Pin the restored file so auto-open doesn't descend into proj/.
                page.add_init_script(
                    "localStorage.setItem('last-opened-file', 'note.md')"
                )
                page.goto(base_url, wait_until="networkidle")
                proj = page.locator(".tree-link-dir", has_text="proj")
                expect(proj).to_be_visible()
                first = parse_qs(urlparse(tree_requests[0]).query)
                assert first.get("depth") == ["1"]

                # Nothing below the first level has been read yet.
                expect(page.locator(".tree-link", has_text="top.md")).to_have_count(0)

                proj.click()
                expect(page.locator(".tree-link", has_text="top.md")).to_be_visible(
                    timeout=15_000
                )
                lazy = [
                    parse_qs(urlparse(u).query)
                    for u in tree_requests
                    if "path" in parse_qs(urlparse(u).query)
                ]
                assert lazy and lazy[-1]["path"] == ["proj"]
                expect(page.locator(".tree-link", has_text="needle-doc.md")).to_have_count(0)

                page.locator(".tree-link-dir", has_text="inner").click()
                page.locator(".tree-link-dir", has_text="deeper").click()
                expect(
                    page.locator(".tree-link", has_text="needle-doc.md")
                ).to_be_visible(timeout=15_000)

                # Refresh: one request that re-reads every open folder.
                tree_requests.clear()
                page.locator("#refresh-tree").click()
                expect(
                    page.locator(".tree-link", has_text="needle-doc.md")
                ).to_be_visible(timeout=15_000)
                page.wait_for_timeout(500)
                assert len(tree_requests) == 1
                expanded = parse_qs(urlparse(tree_requests[0]).query)["expand"]
                assert {"proj", "proj/inner", "proj/inner/deeper"} <= set(expanded)

                # Search reaches into folders the browser never opened.
                page.locator("#tree-search-toggle").click()
                page.locator("#tree-search-input").fill("top.m")
                expect(page.locator(".tree-link", has_text="top.md")).to_be_visible(
                    timeout=15_000
                )
            finally:
                browser.close()
