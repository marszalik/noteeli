"""E2E (headless Chromium): review comments on a note.

The note carries `<!--comment:c_…:start/end-->` range markers, the
comment bodies live in `<note>_comments.md`. Toast UI's WYSIWYG mode
cannot show (or even survive) an inline HTML comment, so the frontend
maps the markers to `<span data-comment>` marks on the way in and back
on the way out. These tests drive the real UI and assert on the files
on disk — that covers the marker⇄span mapping, the panel, the API and
persistence in one go.

Same caveats as the other e2e modules: the editor stack is CDN-loaded,
so the tests skip without outbound network or a Playwright Chromium.
"""

import re
import time
from pathlib import Path

import pytest

playwright_api = pytest.importorskip("playwright.sync_api")
from playwright.sync_api import expect, sync_playwright  # noqa: E402

from test_e2e_git_badge import _cdn_reachable, _enable_autosave, _running_server  # noqa: E402

ARTICLE_MD = """# Machines

Whether a machine is <!--comment:c_a7f3d2:start-->conscious is a question
without an instrument<!--comment:c_a7f3d2:end-->. Trailing text.

- first item
- second item that nobody commented on

Closing paragraph.
"""

COMMENTS_MD = """---
document: article.md
---
## c_a7f3d2
status: open
created: 2026-09-23T20:41:00+02:00

Is this sentence too absolute?
"""


def _wait_for_file(path: Path, predicate, timeout=15.0) -> str:
    deadline = time.monotonic() + timeout
    text = ""
    while time.monotonic() < deadline:
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        # A plain write_text truncates first — an empty read is a write in
        # progress, never a result.
        if text and predicate(text):
            return text
        time.sleep(0.25)
    return text


def _select_by_drag(page, target, width):
    """Select text with a real mouse drag across `target`, starting at its
    left edge. Headless ProseMirror occasionally swallows the first drag
    (the mousedown lands before focus settles), so verify the browser
    selection and retry a couple of times before giving up."""
    for attempt in range(4):
        box = target.bounding_box()
        assert box
        y = box["y"] + box["height"] / 2
        page.mouse.move(box["x"] + 2, y)
        page.mouse.down()
        page.mouse.move(box["x"] + width, y, steps=8)
        page.mouse.up()
        page.wait_for_timeout(150)
        selected = page.evaluate("window.getSelection().toString()")
        if selected.strip():
            return selected
        page.mouse.click(box["x"] + 2, y)  # collapse and try again
        page.wait_for_timeout(200)
    pytest.fail("mouse drag never produced a selection")


def _launch(p):
    try:
        return p.chromium.launch(headless=True)
    except Exception as exc:  # missing browser build
        pytest.skip(f"Playwright Chromium unavailable: {exc}")


@pytest.fixture
def article_server(tmp_path):
    with _running_server(tmp_path) as (base_url, content):
        (content / "article.md").write_text(ARTICLE_MD, encoding="utf-8")
        (content / "article_comments.md").write_text(COMMENTS_MD, encoding="utf-8")
        _enable_autosave(base_url)
        yield base_url, content


def _open_article(page, base_url):
    page.goto(base_url, wait_until="networkidle")
    # article.md sorts first, so the workspace auto-opens it on load. A
    # second click would start another load that lands mid-test and
    # resets the comment state — only click when it is not open yet.
    link = page.locator(".tree-link-file", has_text="article.md").first
    if "is-active" not in (link.get_attribute("class") or ""):
        link.click()
    editor = page.locator("#editor .toastui-editor-ww-container .ProseMirror")
    expect(editor).to_contain_text("Trailing text", timeout=15_000)
    # The fixture always has an open comment → the panel auto-opens once
    # the comments request lands. Wait for it so the layout is settled.
    expect(page.locator("#comments-panel")).to_be_visible(timeout=15_000)
    return editor


def test_markers_render_as_highlight_and_round_trip_through_a_save(article_server):
    """The range shows as a highlighted span (the markers themselves are
    invisible), the panel lists the comment with its number and quote,
    and an unrelated edit saves the file with exactly the same markers —
    even though the range crosses a soft line break."""
    if not _cdn_reachable():
        pytest.skip("editor CDN unreachable — cannot load the real UI")
    base_url, content = article_server

    with sync_playwright() as p:
        browser = _launch(p)
        try:
            page = browser.new_page()
            editor = _open_article(page, base_url)

            span = editor.locator('span[data-comment="c_a7f3d2"]').first
            expect(span).to_be_visible()
            assert "<!--" not in editor.inner_text()

            # Panel auto-opens for a note with open comments.
            panel = page.locator("#comments-panel")
            expect(panel).to_be_visible()
            card = panel.locator(".comment-card[data-id='c_a7f3d2']")
            expect(card.locator(".comment-number")).to_have_text("1")
            expect(card.locator(".comment-quote")).to_contain_text("conscious is a question")
            expect(card.locator(".comment-text")).to_have_text("Is this sentence too absolute?")
            expect(page.locator("#comments-badge")).to_have_text("1")
            margin_badge = page.locator(".comment-badge[data-id='c_a7f3d2']")
            expect(margin_badge).to_have_text("1")

            # Close the panel, click the margin badge → panel reopens on the card.
            page.locator("#comments-close").click()
            expect(panel).to_be_hidden()
            margin_badge.click()
            expect(panel).to_be_visible()
            expect(card).to_have_class(re.compile(r"\bis-active\b"))

            # Edit outside the range → autosave → markers survive verbatim.
            closing = editor.get_by_text("Closing paragraph.")
            closing.click()
            page.keyboard.press("End")
            page.keyboard.type(" Edited.")
            text = _wait_for_file(content / "article.md", lambda t: "Edited." in t)
            assert text.count("<!--comment:c_a7f3d2:start-->") == 1
            assert text.count("<!--comment:c_a7f3d2:end-->") == 1
            assert "<span" not in text
            assert re.search(
                r"<!--comment:c_a7f3d2:start-->conscious is a question\s+"
                r"without an instrument<!--comment:c_a7f3d2:end-->\.",
                text,
            )
        finally:
            browser.close()


def test_select_text_add_comment_writes_both_files(article_server):
    """Selecting text and using the floating chip creates the range in
    the note and the body in the sidecar; resolve / delete update the
    sidecar and delete strips the markers again."""
    if not _cdn_reachable():
        pytest.skip("editor CDN unreachable — cannot load the real UI")
    base_url, content = article_server

    with sync_playwright() as p:
        browser = _launch(p)
        try:
            page = browser.new_page()
            editor = _open_article(page, base_url)

            # Select "second item" with a real mouse drag → floating chip.
            target = editor.get_by_text("second item that nobody commented on")
            selected = _select_by_drag(page, target, 90)
            assert selected.startswith("second"), selected
            chip = page.locator("#comment-add-floating")
            expect(chip).to_be_visible(timeout=5_000)
            chip.click()

            composer = page.locator("#comments-panel .comment-card.is-composer")
            expect(composer).to_be_visible()
            composer.locator("textarea").fill("Tighten this bullet.")
            composer.locator(".comment-action.is-primary").click()

            sidecar = content / "article_comments.md"
            side_text = _wait_for_file(sidecar, lambda t: "Tighten this bullet." in t)
            ids = re.findall(r"^## (c_[0-9a-f]{6,12})$", side_text, flags=re.M)
            assert ids[0] == "c_a7f3d2" and len(ids) == 2
            new_id = ids[1]
            assert f"## {new_id}\nstatus: open\ncreated: " in side_text

            note = _wait_for_file(
                content / "article.md", lambda t: f"<!--comment:{new_id}:start-->" in t
            )
            assert re.search(
                rf"[-*] <!--comment:{new_id}:start-->second[^\n]*<!--comment:{new_id}:end-->", note
            )
            # The sidecar already existed, so the tree keeps a single row for it.
            expect(page.locator(".tree-link-file", has_text="article_comments.md")).to_have_count(1)

            # Numbering follows document order: the new one comes second.
            new_card = page.locator(f"#comments-panel .comment-card[data-id='{new_id}']")
            expect(new_card.locator(".comment-number")).to_have_text("2")
            expect(page.locator("#comments-badge")).to_have_text("2")

            # Resolve → status flips, card hides until "show resolved".
            new_card.locator(".comment-action.is-primary").click()
            side_text = _wait_for_file(
                sidecar, lambda t: f"## {new_id}\nstatus: resolved" in t
            )
            expect(new_card).to_have_count(0)
            expect(page.locator("#comments-badge")).to_have_text("1")
            page.locator("#comments-show-resolved").check()
            expect(new_card).to_be_visible()
            expect(new_card.locator(".comment-number")).to_have_text("✓")

            # Delete (two clicks) → gone from the sidecar AND the markers vanish.
            new_card.locator(".comment-action.is-danger").click()
            new_card.locator(".comment-action.is-danger").click()
            side_text = _wait_for_file(sidecar, lambda t: new_id not in t)
            assert "## c_a7f3d2" in side_text
            note = _wait_for_file(content / "article.md", lambda t: new_id not in t)
            assert "second item that nobody commented on" in note
            assert "c_a7f3d2:start" in note
        finally:
            browser.close()


def test_cancelled_comment_leaves_no_trace(article_server):
    """Cancelling the composer removes the pending range again."""
    if not _cdn_reachable():
        pytest.skip("editor CDN unreachable — cannot load the real UI")
    base_url, content = article_server

    with sync_playwright() as p:
        browser = _launch(p)
        try:
            page = browser.new_page()
            editor = _open_article(page, base_url)
            target = editor.get_by_text("Closing paragraph.")
            _select_by_drag(page, target, 60)
            page.keyboard.press("Control+Alt+M")
            composer = page.locator("#comments-panel .comment-card.is-composer")
            expect(composer).to_be_visible()
            pending_id = composer.get_attribute("data-id")
            expect(editor.locator(f'span[data-comment="{pending_id}"]')).to_have_count(1)
            composer.locator(".comment-action", has_text="Cancel").or_(
                composer.locator(".comment-action", has_text="Anuluj")
            ).first.click()
            expect(editor.locator(f'span[data-comment="{pending_id}"]')).to_have_count(0)
            expect(page.locator("#comments-panel .comment-card.is-composer")).to_have_count(0)
            # Only the original comment is on disk; the note has no new markers.
            time.sleep(2.0)
            assert pending_id not in (content / "article.md").read_text(encoding="utf-8")
            assert pending_id not in (content / "article_comments.md").read_text(encoding="utf-8")
        finally:
            browser.close()


def test_chip_still_works_when_the_selection_collapses_before_the_click(article_server):
    """Tapping the floating chip on a touch screen collapses the browser
    selection before the click arrives. The chip keeps a snapshot of the
    range it was shown for and comments that range instead of complaining
    "select some text"."""
    if not _cdn_reachable():
        pytest.skip("editor CDN unreachable — cannot load the real UI")
    base_url, content = article_server

    with sync_playwright() as p:
        browser = _launch(p)
        try:
            page = browser.new_page()
            editor = _open_article(page, base_url)
            target = editor.get_by_text("Closing paragraph.")
            _select_by_drag(page, target, 60)
            chip = page.locator("#comment-add-floating")
            expect(chip).to_be_visible(timeout=5_000)
            # Collapse the live selection the way a tap outside does, then
            # fire the chip before its 120 ms hide debounce runs.
            page.evaluate("window.getSelection().collapseToStart()")
            page.evaluate("document.getElementById('comment-add-floating').click()")
            composer = page.locator("#comments-panel .comment-card.is-composer")
            expect(composer).to_be_visible()
            pending_id = composer.get_attribute("data-id")
            expect(editor.locator(f'span[data-comment="{pending_id}"]')).to_have_text("Closing")
            composer.locator("textarea").fill("Snapshot range.")
            composer.locator(".comment-action.is-primary").click()
            note = _wait_for_file(
                content / "article.md", lambda t: f"<!--comment:{pending_id}:start-->" in t
            )
            assert re.search(
                rf"<!--comment:{pending_id}:start-->Closing ?<!--comment:{pending_id}:end--> ?paragraph\.", note
            )
        finally:
            browser.close()


def test_selection_running_into_an_existing_comment_is_trimmed(article_server):
    """A drag that ends inside the neighbouring highlight used to be refused
    with a status-bar message most people never notice. The new comment
    now covers the free text up to the existing comment's boundary."""
    if not _cdn_reachable():
        pytest.skip("editor CDN unreachable — cannot load the real UI")
    base_url, content = article_server

    with sync_playwright() as p:
        browser = _launch(p)
        try:
            page = browser.new_page()
            editor = _open_article(page, base_url)
            # Select from the start of the paragraph well into the existing range.
            page.evaluate("""() => {
              const p = Array.from(document.querySelectorAll('.toastui-editor-ww-container .ProseMirror p'))
                .find(e => e.textContent.startsWith('Whether'));
              const first = p.firstChild;                 // "Whether a machine is "
              const span = p.querySelector('span[data-comment]');
              const range = document.createRange();
              range.setStart(first, 0);
              range.setEnd(span.firstChild, 9);           // "conscious"
              const sel = window.getSelection(); sel.removeAllRanges(); sel.addRange(range);
            }""")
            page.keyboard.press("Control+Alt+M")
            composer = page.locator("#comments-panel .comment-card.is-composer")
            expect(composer).to_be_visible()
            new_id = composer.get_attribute("data-id")
            expect(editor.locator(f'span[data-comment="{new_id}"]')).to_have_text("Whether a machine is")
            # The neighbour kept its whole range.
            expect(editor.locator('span[data-comment="c_a7f3d2"]').first).to_have_text("conscious is a question")
            composer.locator("textarea").fill("Trimmed.")
            composer.locator(".comment-action.is-primary").click()
            note = _wait_for_file(
                content / "article.md", lambda t: f"<!--comment:{new_id}:start-->" in t
            )
            assert re.search(
                rf"<!--comment:{new_id}:start-->Whether a machine is ?<!--comment:{new_id}:end--> ?"
                rf"<!--comment:c_a7f3d2:start-->conscious",
                note,
            )
        finally:
            browser.close()


def test_orphaned_range_markers_never_block_a_new_comment(article_server):
    """Regression: a marker pair with no sidecar entry (left behind when a
    comment's creation failed half-way) has no highlight, yet it used to
    make every selection touching it fail with a status-bar message —
    "clicking the chip does nothing". Unknown ranges are dropped on load
    and never count as occupied."""
    if not _cdn_reachable():
        pytest.skip("editor CDN unreachable — cannot load the real UI")
    base_url, content = article_server
    note = content / "article.md"
    note.write_text(
        note.read_text(encoding="utf-8").replace(
            "Closing paragraph.",
            "<!--comment:c_dead01:start-->Closing paragraph.<!--comment:c_dead01:end-->",
        ),
        encoding="utf-8",
    )

    with sync_playwright() as p:
        browser = _launch(p)
        try:
            page = browser.new_page()
            editor = _open_article(page, base_url)
            # The leftover is gone from the editor and, via autosave, from the file.
            expect(editor.locator('span[data-comment="c_dead01"]')).to_have_count(0)
            cleaned = _wait_for_file(note, lambda t: "c_dead01" not in t)
            assert "c_dead01" not in cleaned
            assert "c_a7f3d2:start" in cleaned

            target = editor.get_by_text("Closing paragraph.")
            _select_by_drag(page, target, 60)
            page.locator("#comment-add-floating").click()
            composer = page.locator("#comments-panel .comment-card.is-composer")
            expect(composer).to_be_visible()
            composer.locator("textarea").fill("Now it works.")
            composer.locator(".comment-action.is-primary").click()
            side = _wait_for_file(content / "article_comments.md", lambda t: "Now it works." in t)
            assert side.count("## c_") == 2
        finally:
            browser.close()


def test_refusal_shows_a_toast_next_to_the_selection(article_server):
    """Pressing the shortcut with nothing selected used to answer only in
    the status bar. Now a toast appears (and fades) next to the caret."""
    if not _cdn_reachable():
        pytest.skip("editor CDN unreachable — cannot load the real UI")
    base_url, _content = article_server

    with sync_playwright() as p:
        browser = _launch(p)
        try:
            page = browser.new_page()
            editor = _open_article(page, base_url)
            editor.get_by_text("Closing paragraph.").click()  # caret only, no range
            page.keyboard.press("Control+Alt+M")
            toast = page.locator("#comment-toast")
            expect(toast).to_be_visible()
            expect(toast).to_have_text(re.compile(r"Zaznacz fragment|Select the text"))
            expect(page.locator("#comments-panel .comment-card.is-composer")).to_have_count(0)
            expect(toast).to_be_hidden(timeout=6_000)
        finally:
            browser.close()
