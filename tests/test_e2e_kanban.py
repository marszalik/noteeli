"""E2E (headless Chromium): markdown-backed kanban board.

A board is a plain .md file with `kanban-plugin:` in its frontmatter
(Obsidian Kanban compatible): `## ` headings are columns, list items are
cards, nested list items are subtask cards rendered indented under their
parent. The board serializes every mutation back to markdown through the
regular save/autosave path, so these tests assert against the file on
disk — that covers parser, serializer and persistence in one go.

Same operational caveats as test_e2e_git_badge: the app shell loads its
editor stack from CDNs, so the tests skip without outbound network or a
Playwright Chromium build.
"""

import re
import time
from pathlib import Path

import pytest

playwright_api = pytest.importorskip("playwright.sync_api")
from playwright.sync_api import expect, sync_playwright  # noqa: E402

from test_e2e_git_badge import _cdn_reachable, _enable_autosave, _running_server  # noqa: E402

BOARD_MD = """---

kanban-plugin: board

---

## Todo

- [ ] Parent task
    - [ ] Child one
    - [ ] Child two
- [ ] Loner card

## Doing

## Done

- [x] Shipped thing
"""


def _write_board(content_dir: Path) -> None:
    (content_dir / "board.md").write_text(BOARD_MD, encoding="utf-8")


def _wait_for_file_text(path: Path, predicate, timeout=15.0) -> str:
    deadline = time.monotonic() + timeout
    text = ""
    while time.monotonic() < deadline:
        text = path.read_text(encoding="utf-8")
        if predicate(text):
            return text
        time.sleep(0.3)
    return text


def _column_section(text: str, title: str) -> str:
    """The slice of the markdown belonging to column `title`."""
    start = text.index(f"## {title}")
    rest = text[start + 1 :]
    next_heading = rest.find("\n## ")
    end = len(text) if next_heading == -1 else start + 1 + next_heading
    return text[start:end]


@pytest.fixture
def board_server(tmp_path):
    with _running_server(tmp_path) as (base_url, content):
        _write_board(content)
        _enable_autosave(base_url)
        yield base_url, content


def _open_board(page, base_url):
    page.goto(base_url, wait_until="networkidle")
    page.locator(".tree-link-file", has_text="board.md").click()
    expect(page.locator(".kanban-column")).to_have_count(3, timeout=15_000)


def _launch(p):
    try:
        return p.chromium.launch(headless=True)
    except Exception as exc:  # missing browser build
        pytest.skip(f"Playwright Chromium unavailable: {exc}")


def test_board_renders_columns_cards_and_subtask_thread(board_server):
    """The Obsidian-format file opens straight into a board: three columns,
    subtasks as separate indented cards under the parent, a progress chip
    on the parent, and the topbar toggle flips to the raw markdown editor."""
    if not _cdn_reachable():
        pytest.skip("editor CDN unreachable — cannot load the real UI")
    base_url, _content = board_server

    with sync_playwright() as p:
        browser = _launch(p)
        try:
            page = browser.new_page()
            _open_board(page, base_url)

            titles = page.locator(".kanban-column-title")
            expect(titles.nth(0)).to_have_text("Todo")
            expect(titles.nth(1)).to_have_text("Doing")
            expect(titles.nth(2)).to_have_text("Done")

            # Subtasks live inside the parent card's thread container.
            parent = page.locator(".kanban-card", has=page.locator(
                ".kanban-card-main", has_text="Parent task"))
            thread = parent.locator(".kanban-children .kanban-card")
            expect(thread).to_have_count(2)
            expect(parent.locator(".kanban-card-progress")).to_have_text("0/2")

            # Done column: checked card renders as done.
            expect(
                page.locator(".kanban-card.is-done", has_text="Shipped thing")
            ).to_be_visible()

            # The mode button opens a dropdown with all four views; pick
            # them directly: Text (CodeMirror raw), WYSIWYG, back to Kanban.
            toggle = page.locator("#editor-mode-toggle")
            expect(toggle).to_have_text("Kanban")

            def pick_mode(label):
                toggle.click()
                page.locator(".editor-mode-menu-item", has_text=label).click()

            pick_mode("Kod")
            expect(page.locator("#code-editor")).to_be_visible()
            expect(page.locator("#code-editor")).to_contain_text("kanban-plugin")
            pick_mode("WYSIWYG")
            editor = page.locator("#editor .ProseMirror >> visible=true")
            editor.wait_for(state="visible", timeout=15_000)
            expect(editor).to_contain_text("Parent task")
            pick_mode("Kanban")
            expect(page.locator(".kanban-column")).to_have_count(3)
        finally:
            browser.close()


def test_drag_card_between_columns_persists_markdown(board_server):
    """Dragging a card to another column rewrites the markdown file: the
    card line moves under the target `## ` heading via autosave."""
    if not _cdn_reachable():
        pytest.skip("editor CDN unreachable — cannot load the real UI")
    base_url, content = board_server

    with sync_playwright() as p:
        browser = _launch(p)
        try:
            page = browser.new_page()
            _open_board(page, base_url)

            loner = page.locator(".kanban-card", has_text="Loner card")
            doing = page.locator(".kanban-column").nth(1).locator(".kanban-cards")
            loner.drag_to(doing)

            text = _wait_for_file_text(
                content / "board.md",
                lambda t: "Loner card" in _column_section(t, "Doing"),
            )
            assert "- [ ] Loner card" in _column_section(text, "Doing")
            assert "Loner card" not in _column_section(text, "Todo")
        finally:
            browser.close()


def test_subtask_checkbox_toggle_persists_nested_line(board_server):
    """Ticking a subtask card's checkbox flips exactly its nested `[ ]`
    to `[x]` in the file — parent and sibling lines stay untouched."""
    if not _cdn_reachable():
        pytest.skip("editor CDN unreachable — cannot load the real UI")
    base_url, content = board_server

    with sync_playwright() as p:
        browser = _launch(p)
        try:
            page = browser.new_page()
            _open_board(page, base_url)

            page.locator(
                ".kanban-card-main", has_text="Child one"
            ).locator("input.kanban-card-checkbox").check()

            text = _wait_for_file_text(
                content / "board.md", lambda t: "- [x] Child one" in t
            )
            assert "    - [x] Child one" in text
            assert "    - [ ] Child two" in text
            assert "- [ ] Parent task" in text
        finally:
            browser.close()


def test_parent_locked_until_subtasks_moved(board_server):
    """A card with subtasks cannot leave its column. Once both subtask
    cards are dragged away (each becoming standalone), the parent unlocks
    and can be moved."""
    if not _cdn_reachable():
        pytest.skip("editor CDN unreachable — cannot load the real UI")
    base_url, content = board_server
    board_path = content / "board.md"

    with sync_playwright() as p:
        browser = _launch(p)
        try:
            page = browser.new_page()
            _open_board(page, base_url)

            doing = page.locator(".kanban-column").nth(1).locator(".kanban-cards")
            parent = page.locator(".kanban-card", has=page.locator(
                ".kanban-card-main", has_text="Parent task"))

            # Locked: the drop is rejected, the file keeps the parent in Todo.
            parent.drag_to(doing)
            page.wait_for_timeout(2_500)  # would-be autosave window
            assert "Parent task" in _column_section(
                board_path.read_text(encoding="utf-8"), "Todo"
            )

            # Move both subtasks away — they detach and become standalone.
            # Drag by the card's own main row: .kanban-card would also match
            # the parent (subtask DOM nests inside it), .kanban-card-main
            # holds only its own text.
            for child in ("Child one", "Child two"):
                page.locator(".kanban-card-main", has_text=child).drag_to(doing)
            text = _wait_for_file_text(
                board_path,
                lambda t: "Child one" in _column_section(t, "Doing")
                and "Child two" in _column_section(t, "Doing"),
            )
            assert "- [ ] Child one" in _column_section(text, "Doing")

            # Unlocked now: the parent can follow.
            page.locator(".kanban-card-main", has_text="Parent task").drag_to(doing)
            text = _wait_for_file_text(
                board_path,
                lambda t: "Parent task" in _column_section(t, "Doing"),
            )
            assert "- [ ] Parent task" in _column_section(text, "Doing")
            assert "Parent task" not in _column_section(text, "Todo")
        finally:
            browser.close()


def test_mode_toggle_converts_plain_note_to_board(board_server):
    """Cycling the mode button to Kanban on a regular note (no frontmatter)
    shows its `## ` headings as columns. Just switching views writes
    nothing; the first real board edit saves the note with the
    `kanban-plugin` frontmatter added, and from then on the file opens as
    a board. A note with no headings gets three default columns."""
    if not _cdn_reachable():
        pytest.skip("editor CDN unreachable — cannot load the real UI")
    base_url, content = board_server
    note = content / "notatka.md"
    note.write_text(
        "# Projekt\n\n## Pomysły\n\n- [ ] Istniejące zadanie\n", encoding="utf-8"
    )
    (content / "pusta.md").write_text("tylko tekst\n", encoding="utf-8")

    with sync_playwright() as p:
        browser = _launch(p)
        try:
            page = browser.new_page()
            page.goto(base_url, wait_until="networkidle")
            page.locator(".tree-link-file", has_text="notatka.md").click()
            editor = page.locator("#editor .ProseMirror >> visible=true")
            editor.wait_for(state="visible", timeout=15_000)

            toggle = page.locator("#editor-mode-toggle")
            toggle.click()
            page.locator(".editor-mode-menu-item", has_text="Kanban").click()
            expect(page.locator(".kanban-column-title")).to_have_text(["Pomysły"])
            expect(
                page.locator(".kanban-card", has_text="Istniejące zadanie")
            ).to_be_visible()

            # Merely switching views must not touch the file.
            page.wait_for_timeout(2_500)
            assert "kanban-plugin" not in note.read_text(encoding="utf-8")

            # First real edit → the save carries the added frontmatter.
            page.locator(".kanban-add-card").click()
            entry = page.locator(".kanban-inline-input")
            entry.fill("Nowa karta")
            entry.press("Enter")
            text = _wait_for_file_text(
                note, lambda t: "kanban-plugin" in t and "Nowa karta" in t
            )
            assert "## Pomysły" in text
            assert "# Projekt" in text  # prelude content preserved

            # Reopening the note now lands straight on the board.
            page.locator(".tree-link-file", has_text="board.md").click()
            expect(page.locator(".kanban-column")).to_have_count(3, timeout=15_000)
            page.locator(".tree-link-file", has_text="notatka.md").click()
            expect(
                page.locator(".kanban-card", has_text="Nowa karta")
            ).to_be_visible(timeout=15_000)

            # No headings at all → three default (localized) columns.
            page.locator(".tree-link-file", has_text="pusta.md").click()
            editor = page.locator("#editor .ProseMirror >> visible=true")
            editor.wait_for(state="visible", timeout=15_000)
            toggle.click()
            page.locator(".editor-mode-menu-item", has_text="Kanban").click()
            expect(page.locator(".kanban-column")).to_have_count(3)
        finally:
            browser.close()


def test_detached_subtask_keeps_parent_link(board_server):
    """Jira-style: a subtask dragged to another column stays a subtask.
    The file gets a block id on the parent (`^abc12`, native Obsidian
    syntax) and a `[[#^abc12]]` ref on the moved card; on the board the
    moved card shows a parent chip, and the parent's progress counts it —
    ticking the moved subtask updates the parent's counter."""
    if not _cdn_reachable():
        pytest.skip("editor CDN unreachable — cannot load the real UI")
    base_url, content = board_server
    board_path = content / "board.md"

    with sync_playwright() as p:
        browser = _launch(p)
        try:
            page = browser.new_page()
            _open_board(page, base_url)

            doing = page.locator(".kanban-column").nth(1).locator(".kanban-cards")
            page.locator(".kanban-card-main", has_text="Child one").drag_to(doing)

            text = _wait_for_file_text(
                board_path, lambda t: "Child one" in _column_section(t, "Doing")
            )
            id_match = re.search(r"- \[ \] Parent task \^([a-z0-9]+)", text)
            assert id_match, f"parent got no block id:\n{text}"
            parent_id = id_match.group(1)
            assert f"- [ ] Child one [[#^{parent_id}]]" in _column_section(text, "Doing")

            # The moved card shows where it belongs…
            moved = page.locator(".kanban-column").nth(1).locator(
                ".kanban-card", has_text="Child one")
            expect(moved.locator(".kanban-card-parent")).to_have_text("↳ Parent task")

            # …and the parent still counts it: 0/2, then 1/2 once ticked.
            parent_main = page.locator(".kanban-card-main", has_text="Parent task")
            expect(parent_main.locator(".kanban-card-progress")).to_have_text("0/2")
            moved.locator("input.kanban-card-checkbox").check()
            expect(parent_main.locator(".kanban-card-progress")).to_have_text("1/2")
        finally:
            browser.close()


def test_parser_roundtrip_preserves_foreign_content(board_server):
    """parse → serialize is byte-identical for a board holding content the
    UI doesn't model: frontmatter, prose under a heading, deep nesting,
    card descriptions and an Obsidian `%% kanban:settings` block."""
    if not _cdn_reachable():
        pytest.skip("editor CDN unreachable — cannot load the real UI")
    base_url, _content = board_server

    tricky = (
        "---\n\nkanban-plugin: board\n\n---\n\n"
        "## Kolumna A\n\n"
        "Opis kolumny, nie karta.\n\n"
        "- [ ] Karta z **pogrubieniem** i [linkiem](inna.md)\n"
        "    - [ ] dziecko\n"
        "        - [x] wnuk\n"
        "    dopisek pod kartą\n"
        "- Zwykła pozycja bez checkboxa\n\n"
        "## Kolumna B\n\n"
        "- [x] Zrobione\n\n"
        "%% kanban:settings\n```\n{\"kanban-plugin\":\"board\"}\n```\n%%\n"
    )

    with sync_playwright() as p:
        browser = _launch(p)
        try:
            page = browser.new_page()
            page.goto(base_url, wait_until="networkidle")
            result = page.evaluate(
                """(md) => {
                    const k = window.__noteeliKanban;
                    return {
                        detected: k.isKanban(md),
                        identical: k.serialize(k.parse(md)) === md,
                        columns: k.parse(md).columns.map(c => c.title),
                    };
                }""",
                tricky,
            )
            assert result["detected"] is True
            assert result["columns"] == ["Kolumna A", "Kolumna B"]
            assert result["identical"] is True
        finally:
            browser.close()
