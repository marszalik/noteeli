# Changelog

All notable changes to Noteeli are tracked here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and version numbers follow [Semantic Versioning](https://semver.org/).

- **MAJOR** — incompatible changes (storage layout, breaking API).
- **MINOR** — new functionality, backwards compatible.
- **PATCH** — bug fixes only, backwards compatible.

## [Unreleased]

### Added

- Read-only preview for `.docx` (Word) and `.xlsx` / `.xlsm` (Excel) files.
  Word documents are converted to HTML on the server (`mammoth`); Excel
  workbooks render as HTML tables, one per sheet (`openpyxl`, capped at 5000
  rows per sheet for safety). Preview shows in a sandboxed iframe — no edit,
  no script execution. Distinct sidebar icons (blue for docx, green for
  xlsx/csv).

## [1.0.0] - 2026-05-01

### Added

- One-line installer (`install.sh`) for Linux & macOS — clones, sets up a
  virtualenv, generates `.env`, and installs a `noteeli` launcher.
- Tabbed settings modal with sidebar navigation (Source / Appearance /
  Editor / Images / Profiles).
- File-type icons in the sidebar tree (markdown, json, code, image, pdf,
  audio, video, archive, plain text, generic).
- CodeMirror-based editor for code files with on-demand syntax mode loading
  for Python, JavaScript/TypeScript, PHP, Ruby, Go, Rust, Java, C/C++, Shell,
  SQL, CSS, HTML, YAML, and more.
- User-pickable code highlighting theme with auto-fallback to Material
  Darker on dark app themes.
- Webnote.li theme based on the marketing-site mockup (IBM Plex Sans/Serif/Mono,
  single-panel layout with 1 px seam between sidebar and editor).
- Themed scrollbars across all themes (no more system-default white bars).
- Drag-and-drop image from sidebar into editor with copy-to-configured-location
  behaviour (Obsidian-style).
- "Last opened file" persistence — Noteeli remembers your last note across
  reloads.
- WYSIWYG default for Markdown files; plain text and code files routed to
  CodeMirror in source mode (no markdown preview pane for non-markdown).
- JSON files open in form mode, fully expanded.

### Fixed

- Rename via Enter no longer creates a new `.md` file — the keypress now
  dispatches on modal action like the button click.
- Renaming a non-Markdown file (image, code, etc.) preserves its original
  extension when no extension is provided.
- Save button hides in autosave mode.

### Changed

- Top-bar buttons (Save, Logout, mode toggle) shrunk and translated.
- Settings inputs and buttons compacted to reduce visual noise.

[Unreleased]: https://github.com/marszalik/noteeli/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/marszalik/noteeli/releases/tag/v1.0.0
