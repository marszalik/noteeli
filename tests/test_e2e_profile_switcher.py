"""E2E (headless Chromium): settings belong to a profile.

The sidebar header shows the active profile; Settings edit it (no separate
"save profile" step); "+ New profile" creates one with its own source and
switches to it; the dropdown switches back. Same CDN/Chromium skip rules
as the other e2e tests.
"""

import pytest

playwright_api = pytest.importorskip("playwright.sync_api")
from playwright.sync_api import expect, sync_playwright  # noqa: E402

from test_e2e_git_badge import _cdn_reachable, _running_server  # noqa: E402


def test_profiles_own_the_settings_and_switch_from_the_sidebar(tmp_path):
    if not _cdn_reachable():
        pytest.skip("editor CDN unreachable — cannot load the real UI")

    other_root = tmp_path / "drugie-notatki"
    other_root.mkdir()
    (other_root / "inna.md").write_text("# Inna\n", encoding="utf-8")

    with _running_server(tmp_path) as (base_url, _content):
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
            except Exception as exc:
                pytest.skip(f"Playwright Chromium unavailable: {exc}")
            try:
                page = browser.new_page(viewport={"width": 1280, "height": 800})
                page.goto(base_url, wait_until="networkidle")
                switcher = page.locator("#profile-switcher-name")
                name_input = page.locator("#profile-name-input")

                # No profile yet: first save turns the current setup into one.
                expect(switcher).to_have_text("Brak profilu")
                page.locator("#user-menu-toggle").click()
                page.locator("#open-settings").click()
                expect(name_input).to_be_visible()
                assert name_input.input_value() != ""  # suggested from the folder
                name_input.fill("Główny")
                page.locator("#save-settings").click()
                expect(switcher).to_have_text("Główny", timeout=15_000)

                # Settings edit the active profile in place: rename it.
                page.locator("#user-menu-toggle").click()
                page.locator("#open-settings").click()
                name_input.fill("Praca")
                page.locator("#save-settings").click()
                expect(switcher).to_have_text("Praca", timeout=15_000)

                # New profile = its own source, created and activated in one go.
                page.locator("#toggle-preference-profiles").click()
                page.locator("#profile-new").click()
                assert name_input.input_value() == ""
                name_input.fill("Drugie")
                page.locator("#content-root-input").fill(str(other_root))
                page.locator("#save-settings").click()
                expect(switcher).to_have_text("Drugie", timeout=15_000)
                expect(
                    page.locator(".tree-link-file", has_text="inna.md")
                ).to_be_visible(timeout=15_000)

                # Switch back from the sidebar dropdown.
                page.locator("#toggle-preference-profiles").click()
                page.locator(".profiles-dropdown-item", has_text="Praca").click()
                expect(switcher).to_have_text("Praca", timeout=15_000)
                expect(
                    page.locator(".tree-link-file", has_text="inna.md")
                ).to_have_count(0)
                expect(page.locator(".tree-link-file", has_text="note.md")).to_be_visible(
                    timeout=15_000
                )
            finally:
                browser.close()
