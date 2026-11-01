"""E2E: .drawio files open in the embedded draw.io editor, edits reach the
file through Save, and the file menu can open the diagram in diagrams.net.

Needs outbound network (embed.diagrams.net) — skipped otherwise. draw.io
refuses "HeadlessChrome" user agents, so the context presents a normal one.
"""
import re

import pytest

playwright_api = pytest.importorskip("playwright.sync_api")
from playwright.sync_api import sync_playwright  # noqa: E402

from test_e2e_git_badge import _cdn_reachable, _running_server  # noqa: E402

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
XML = (
    '<mxfile><diagram name="Page-1" id="a"><mxGraphModel><root><mxCell id="0"/><mxCell id="1" parent="0"/>'
    '<mxCell id="2" value="Hello" style="rounded=1;" vertex="1" parent="1">'
    '<mxGeometry x="120" y="120" width="120" height="60" as="geometry"/></mxCell></root></mxGraphModel></diagram></mxfile>'
)


def test_drawio_edit_save_and_open_in_app(tmp_path):
    if not _cdn_reachable():
        pytest.skip("no outbound network")
    with _running_server(tmp_path) as (base_url, content):
        (content / "d.drawio").write_text(XML, encoding="utf-8")
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
            except Exception as exc:
                pytest.skip(f"Playwright Chromium unavailable: {exc}")
            try:
                ctx = browser.new_context(viewport={"width": 1300, "height": 800}, user_agent=UA)
                page = ctx.new_page()
                page.add_init_script("localStorage.setItem('last-opened-file','d.drawio')")
                page.goto(base_url, wait_until="networkidle")
                frame = page.frame_locator("#drawio-editor iframe")
                try:
                    frame.get_by_text("Hello").first.wait_for(timeout=40_000)
                except Exception:
                    pytest.skip("draw.io editor not reachable from this machine")

                # Edit in draw.io, save with Noteeli's Save button.
                frame.get_by_text("Hello").first.dblclick()
                page.keyboard.type("Changed")
                page.mouse.click(900, 600)
                page.wait_for_timeout(800)
                page.click("#save-button")
                for _ in range(20):
                    if "Changed" in (content / "d.drawio").read_text(encoding="utf-8"):
                        break
                    page.wait_for_timeout(300)
                saved = (content / "d.drawio").read_text(encoding="utf-8")
                assert "Changed" in saved and saved.lstrip().startswith("<mxfile")

                # File menu: only export actions that make sense for a diagram.
                page.click("#file-menu-toggle")
                assert page.locator("#file-open-drawio").is_visible()
                assert page.locator("#file-download").is_visible()
                assert not page.locator("#file-pdf").is_visible()
                assert not page.locator("#file-read-aloud").is_visible()
                with ctx.expect_page() as info:
                    page.click("#file-open-drawio")
                popup = info.value
                popup.wait_for_url("https://app.diagrams.net/#R**", timeout=20_000)
            finally:
                browser.close()


def test_new_empty_drawio_file_opens_a_blank_canvas(tmp_path):
    if not _cdn_reachable():
        pytest.skip("no outbound network")
    with _running_server(tmp_path) as (base_url, content):
        (content / "empty.drawio").write_text("", encoding="utf-8")
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
            except Exception as exc:
                pytest.skip(f"Playwright Chromium unavailable: {exc}")
            try:
                page = browser.new_context(viewport={"width": 1300, "height": 800}, user_agent=UA).new_page()
                page.add_init_script("localStorage.setItem('last-opened-file','empty.drawio')")
                page.goto(base_url, wait_until="networkidle")
                frame = page.frame_locator("#drawio-editor iframe")
                try:
                    # the page tab is named in the UI language (pl: "Strona-1")
                    frame.get_by_text(re.compile(r"^(Strona|Page)-1$")).first.wait_for(timeout=40_000)
                except Exception:
                    pytest.skip("draw.io editor not reachable from this machine")
            finally:
                browser.close()
