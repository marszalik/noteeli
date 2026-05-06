"""Showcase of syntax highlighting in Noteeli.

Code files (.py, .js, .ts, .php, .rb, .go, .rs, .c, .cpp, .sh, .css,
.html, .yaml, .toml…) open in CodeMirror with the language mode loaded
on demand and the colour theme you picked
(Settings → Editor → Code highlighting theme).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Note:
    path: Path
    title: str
    body: str

    def slug(self) -> str:
        s = re.sub(r"[^\w\s-]", "", self.title.lower())
        return re.sub(r"\s+", "-", s).strip("-")


def find_markdown_files(root: Path) -> list[Path]:
    """Yield every .md file under `root`, alphabetical."""
    return sorted(root.rglob("*.md"))


def read_note(path: Path) -> Note:
    text = path.read_text(encoding="utf-8")
    first_line = text.splitlines()[0] if text else ""
    title = first_line.lstrip("#").strip() or path.stem
    return Note(path=path, title=title, body=text)


if __name__ == "__main__":
    for md_file in find_markdown_files(Path("notes")):
        note = read_note(md_file)
        print(f"{note.slug()}: {note.title}")
