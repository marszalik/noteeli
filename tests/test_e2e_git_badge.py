"""E2E (headless Chromium): the git badge updates after an autosave.

Regression test — autosaving a document used to leave the sidebar git
counter stale until a full page reload. A manual save reloads the whole
tree (which refreshes git status as a side effect); autosave deliberately
skips the tree reload, so it must call refreshGitStatus() itself.

The test boots a real uvicorn server against a throwaway git repo and
drives the real UI. The editor stack (Toast UI) is CDN-loaded, so the
test needs outbound network; it skips itself when the CDN or a Playwright
Chromium build is unavailable rather than failing the hermetic suite.
"""

import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from contextlib import contextmanager
from pathlib import Path

import pytest

playwright_api = pytest.importorskip("playwright.sync_api")
from playwright.sync_api import expect, sync_playwright  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]


def _cdn_reachable() -> bool:
    try:
        socket.create_connection(("uicdn.toast.com", 443), timeout=5).close()
        return True
    except OSError:
        return False


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        env={**os.environ, "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_SYSTEM": "/dev/null"},
    )


@contextmanager
def _running_server(tmp_path, extra_env=None):
    """A real uvicorn instance over a clean single-commit git workspace."""
    content = tmp_path / "content"
    content.mkdir()
    (content / "note.md").write_text("# Hello\n", encoding="utf-8")
    (content / "second.md").write_text("# Second\n", encoding="utf-8")
    _git(content, "init")
    _git(content, "config", "user.email", "test@noteeli")
    _git(content, "config", "user.name", "Noteeli Test")
    _git(content, "add", ".")
    _git(content, "commit", "-m", "initial")

    env = {k: v for k, v in os.environ.items() if not k.startswith("NOTEELI_")}
    env["NOTEELI_CONTENT_ROOT"] = str(content)
    env["NOTEELI_DATA_DIR"] = str(tmp_path / "data")
    env["PYTHONPATH"] = str(REPO_ROOT)
    env.update(extra_env or {})

    port = _free_port()
    base_url = f"http://127.0.0.1:{port}"
    # cwd is the tmp dir on purpose: pydantic-settings reads `.env` relative
    # to the working directory, and the repo root holds a production .env
    # (hosted mode, OAuth) that would break the localhost auto-login.
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--log-level",
            "warning",
        ],
        cwd=tmp_path,
        env=env,
    )
    try:
        deadline = time.monotonic() + 30
        while True:
            try:
                urllib.request.urlopen(base_url, timeout=2).read()
                break
            except (urllib.error.URLError, ConnectionError):
                if proc.poll() is not None:
                    pytest.fail("uvicorn exited before becoming ready")
                if time.monotonic() > deadline:
                    pytest.fail("uvicorn did not become ready within 30s")
                time.sleep(0.2)
        yield base_url, content
    finally:
        proc.terminate()
        proc.wait(timeout=10)


@pytest.fixture
def server(tmp_path):
    with _running_server(tmp_path) as (base_url, _content):
        yield base_url


def _enable_autosave(base_url: str) -> None:
    # Localhost requests share the synthetic "local@noteeli" identity, so
    # preferences set here are the ones the browser session sees.
    prefs = json.loads(urllib.request.urlopen(f"{base_url}/api/preferences").read())
    request = urllib.request.Request(
        f"{base_url}/api/preferences",
        data=json.dumps({**prefs, "autosave_enabled": True}).encode(),
        method="PUT",
        headers={"Content-Type": "application/json"},
    )
    urllib.request.urlopen(request).read()


def test_autosave_refreshes_git_badge_without_reload(server):
    if not _cdn_reachable():
        pytest.skip("editor CDN unreachable — cannot load the real UI")
    _enable_autosave(server)

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True)
        except Exception as exc:  # missing browser build
            pytest.skip(f"Playwright Chromium unavailable: {exc}")
        try:
            page = browser.new_page()
            page.goto(server, wait_until="networkidle")

            # Clean repo → no badge on first paint.
            badge = page.locator("#git-menu-badge")
            expect(badge).to_be_hidden()

            page.locator(".tree-link-file", has_text="note.md").click()
            # Toast UI keeps two ProseMirror roots (markdown + WYSIWYG);
            # only the active mode's root is visible.
            editor = page.locator("#editor .ProseMirror >> visible=true")
            editor.wait_for(state="visible", timeout=15_000)
            editor.click()
            page.keyboard.type("Autosave should light up the git badge.")

            # No reload happens here: the badge must appear on its own once
            # the debounced autosave (1.2s) lands and git status refreshes.
            expect(badge).to_have_text("1", timeout=15_000)
            expect(badge).to_be_visible()

            # The tree row should pick up the "modified" marker too, since
            # refreshGitStatus() re-renders the tree.
            expect(
                page.locator(".tree-link-file.is-git-changed", has_text="note.md")
            ).to_be_visible(timeout=15_000)
        finally:
            browser.close()


def test_autocommit_checkpoints_after_idle(tmp_path):
    """Full silent-checkpoint loop: type → autosave → git badge shows the
    dirty file → the idle-debounced background commit lands → badge clears
    on the next status refresh, and the repo has a Checkpoint commit."""
    if not _cdn_reachable():
        pytest.skip("editor CDN unreachable — cannot load the real UI")

    extra_env = {
        "NOTEELI_GIT_AUTOCOMMIT": "1",
        "NOTEELI_GIT_AUTOCOMMIT_IDLE_SECONDS": "2",
    }
    with _running_server(tmp_path, extra_env) as (base_url, content):
        _enable_autosave(base_url)
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
            except Exception as exc:
                pytest.skip(f"Playwright Chromium unavailable: {exc}")
            try:
                page = browser.new_page()
                page.goto(base_url, wait_until="networkidle")
                badge = page.locator("#git-menu-badge")

                page.locator(".tree-link-file", has_text="note.md").click()
                editor = page.locator("#editor .ProseMirror >> visible=true")
                editor.wait_for(state="visible", timeout=15_000)
                editor.click()
                page.keyboard.type("Idle checkpoint incoming.")

                # Autosave lands → badge appears.
                expect(badge).to_have_text("1", timeout=15_000)

                # Wait out the idle window, then let the checkpoint loop
                # commit. The UI refreshes git status when the git menu
                # opens — use that as the "no reload" refresh trigger.
                deadline = time.monotonic() + 20
                while time.monotonic() < deadline:
                    log = subprocess.run(
                        ["git", "-C", str(content), "log", "-1", "--format=%s"],
                        capture_output=True,
                        text=True,
                    ).stdout.strip()
                    if log.startswith("Checkpoint:"):
                        break
                    time.sleep(0.5)
                assert log == "Checkpoint: note.md"

                page.locator("#git-menu-toggle").click()  # triggers refreshGitStatus()
                expect(badge).to_be_hidden(timeout=10_000)
            finally:
                browser.close()


def _publish(base_url: str, path: str) -> str:
    """Publish a path via the localhost-bypassed API; returns the public URL."""
    request = urllib.request.Request(
        f"{base_url}/api/publish",
        data=json.dumps({"path": path}).encode(),
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    item = json.loads(urllib.request.urlopen(request).read())
    return base_url + item["public_url"]


def test_public_view_hides_editor_chrome(tmp_path):
    """A published FILE reads like an article: no sidebar, no status line
    ('File ready for editing' on a read-only page), title names the note.
    A published FOLDER keeps the sidebar for navigation but still drops
    the status line and the dotfiles toggle."""
    if not _cdn_reachable():
        pytest.skip("editor CDN unreachable — cannot load the real UI")

    with _running_server(tmp_path) as (base_url, content):
        project = content / "projekt"
        project.mkdir()
        (project / "plan.md").write_text("# Plan\n\ntresc planu\n", encoding="utf-8")
        file_url = _publish(base_url, "note.md")
        folder_url = _publish(base_url, "projekt")

        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
            except Exception as exc:
                pytest.skip(f"Playwright Chromium unavailable: {exc}")
            try:
                page = browser.new_page()

                page.goto(file_url, wait_until="networkidle")
                expect(page.locator("#public-content")).to_contain_text("Hello")
                expect(page.locator(".statusbar")).to_be_hidden()
                expect(page.locator("#sidebar")).to_be_hidden()
                assert "note — Noteeli" in page.title()

                page.goto(folder_url, wait_until="networkidle")
                expect(page.locator("#public-content")).to_contain_text("tresc planu")
                expect(page.locator("#sidebar")).to_be_visible()
                expect(page.locator(".statusbar")).to_be_hidden()
                expect(page.locator("#toggle-hidden-files")).to_be_hidden()
            finally:
                browser.close()


def _mint_session_cookie(secret: str, user: dict) -> str:
    """Forge a valid starlette session cookie. Works because the test
    controls NOTEELI_SESSION_SECRET — same signing scheme as
    SessionMiddleware (TimestampSigner over base64 JSON)."""
    import base64

    from itsdangerous import TimestampSigner

    payload = base64.b64encode(json.dumps({"user": user}).encode("utf-8"))
    return TimestampSigner(secret).sign(payload).decode("utf-8")


def _login_context(browser, base_url: str, secret: str, email: str, name: str):
    """A browser context authenticated as a real (non-local) user.
    X-Forwarded-Host makes the request non-local, so the auth layer reads
    the session instead of handing out the localhost synthetic identity."""
    context = browser.new_context(extra_http_headers={"X-Forwarded-Host": "app.test"})
    context.add_cookies(
        [
            {
                "name": "session",
                "value": _mint_session_cookie(secret, {"email": email, "name": name}),
                "url": base_url,
            }
        ]
    )
    # Autosave preference is per-user — enable it for this identity.
    prefs = context.request.get(f"{base_url}/api/preferences").json()
    response = context.request.put(
        f"{base_url}/api/preferences",
        data=json.dumps({**prefs, "autosave_enabled": True}),
        headers={"Content-Type": "application/json"},
    )
    assert response.ok, response.text()
    return context


def test_two_users_editing_simultaneously_get_own_signed_checkpoints(tmp_path):
    """Two logged-in users type at the same time (interleaved keystrokes in
    two browser contexts). Each must end up with their own checkpoint
    commit, authored by them, containing only their file."""
    if not _cdn_reachable():
        pytest.skip("editor CDN unreachable — cannot load the real UI")

    secret = "e2e-session-secret"
    extra_env = {
        "NOTEELI_GIT_AUTOCOMMIT": "1",
        "NOTEELI_GIT_AUTOCOMMIT_IDLE_SECONDS": "2",
        "NOTEELI_SESSION_SECRET": secret,
    }
    users = [
        ("anna@example.com", "Anna", "note.md"),
        ("bartek@example.com", "Bartek", "second.md"),
    ]
    with _running_server(tmp_path, extra_env) as (base_url, content):
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
            except Exception as exc:
                pytest.skip(f"Playwright Chromium unavailable: {exc}")
            try:
                sessions = []
                for email, name, filename in users:
                    context = _login_context(browser, base_url, secret, email, name)
                    page = context.new_page()
                    page.goto(base_url, wait_until="networkidle")
                    page.locator(".tree-link-file", has_text=filename).click()
                    editor = page.locator("#editor .ProseMirror >> visible=true")
                    editor.wait_for(state="visible", timeout=15_000)
                    editor.click()
                    sessions.append((page, email))

                # Interleave keystrokes so both editing sessions are live
                # at the same time (each page keeps its own focus).
                for round_no in range(3):
                    for page, email in sessions:
                        page.keyboard.type(f" edit {round_no} by {email.split('@')[0]}.")

                # Both files go idle together → the background loop should
                # produce one commit per author.
                deadline = time.monotonic() + 25
                checkpoints: list[str] = []
                while time.monotonic() < deadline:
                    log = subprocess.run(
                        ["git", "-C", str(content), "log", "-5", "--format=%ae|%s"],
                        capture_output=True,
                        text=True,
                    ).stdout.splitlines()
                    checkpoints = [line for line in log if "|Checkpoint:" in line]
                    if len(checkpoints) >= 2:
                        break
                    time.sleep(0.5)

                assert sorted(checkpoints) == [
                    "anna@example.com|Checkpoint: note.md",
                    "bartek@example.com|Checkpoint: second.md",
                ]
            finally:
                browser.close()


def test_history_modal_shows_commits_diff_and_blame(tmp_path):
    """The blame/history UI end-to-end: a signed-in user's edit gets
    checkpointed, then the History modal lists the commit with the author,
    clicking it reveals a word-level diff of the added text, and the
    Line-authors tab attributes the new line to that user."""
    if not _cdn_reachable():
        pytest.skip("editor CDN unreachable — cannot load the real UI")

    secret = "e2e-session-secret"
    marker = "sygnatura42"
    extra_env = {
        "NOTEELI_GIT_AUTOCOMMIT": "1",
        "NOTEELI_GIT_AUTOCOMMIT_IDLE_SECONDS": "2",
        "NOTEELI_SESSION_SECRET": secret,
    }
    with _running_server(tmp_path, extra_env) as (base_url, content):
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
            except Exception as exc:
                pytest.skip(f"Playwright Chromium unavailable: {exc}")
            try:
                context = _login_context(browser, base_url, secret, "anna@example.com", "Anna")
                page = context.new_page()
                page.goto(base_url, wait_until="networkidle")
                page.locator(".tree-link-file", has_text="note.md").click()
                editor = page.locator("#editor .ProseMirror >> visible=true")
                editor.wait_for(state="visible", timeout=15_000)
                editor.click()
                page.keyboard.type(f"Nowy wiersz {marker} od Anny.")

                # Wait for the idle checkpoint so history has Anna's commit.
                deadline = time.monotonic() + 20
                while time.monotonic() < deadline:
                    log = subprocess.run(
                        ["git", "-C", str(content), "log", "-1", "--format=%s"],
                        capture_output=True,
                        text=True,
                    ).stdout.strip()
                    if log.startswith("Checkpoint:"):
                        break
                    time.sleep(0.5)
                assert log == "Checkpoint: note.md"

                # History modal opens from the git dropdown ("History &
                # authors" entry, labeled with the open file's name).
                page.locator("#git-menu-toggle").click()
                history_entry = page.locator("#git-file-history")
                expect(history_entry).to_be_visible()
                expect(history_entry).to_contain_text("note.md")
                history_entry.click()
                expect(page.locator("#history-modal")).to_be_visible()
                checkpoint_row = page.locator(
                    ".history-commit-row", has_text="Checkpoint: note.md"
                )
                expect(checkpoint_row).to_be_visible(timeout=10_000)
                expect(checkpoint_row).to_contain_text("Anna")
                expect(
                    page.locator(".history-commit-row", has_text="initial")
                ).to_be_visible()

                # Clicking the commit reveals the word-level diff with the
                # typed text marked as added.
                checkpoint_row.click()
                added = page.locator(".history-diff .diff-added", has_text=marker)
                expect(added.first).to_be_visible(timeout=10_000)

                # Blame tab: the new line is attributed to Anna.
                page.locator("#history-tab-blame").click()
                blame_line = page.locator(".blame-line", has_text=marker)
                expect(blame_line.first).to_be_visible(timeout=10_000)
                expect(blame_line.first.locator(".blame-gutter")).to_contain_text("Anna")
            finally:
                browser.close()
