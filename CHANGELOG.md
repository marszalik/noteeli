# Changelog

All notable changes to Noteeli are tracked here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and version numbers follow [Semantic Versioning](https://semver.org/).

- **MAJOR** — incompatible changes (storage layout, breaking API).
- **MINOR** — new functionality, backwards compatible.
- **PATCH** — bug fixes only, backwards compatible.

## [Unreleased]

### Added

- **Publish / Unpublish for files and folders.** Right-click any tree
  row → "Publish" mints a public URL of the form `/{id}/{slug}`
  served by the same Noteeli instance (no `node_nr` indirection
  beyond the auto-generated id, slug is derived from the basename
  with diacritics folded). The page renders the regular workspace UI
  in read-only mode — sidebar scoped to the published path, no save,
  no upload, no settings, no profiles, no edit toolbar — and is
  reachable without authentication. Folders expose every descendant
  through scoped `/api/public/{tree,file,preview}` routes; published
  files only expose themselves. Path traversal beyond the published
  scope returns 403. A globe badge marks published rows in the
  authenticated tree, with "Copy public link" and "Unpublish" in the
  context menu. Renaming or deleting a path automatically drops any
  publish entry that pointed at it. Demo mode blocks publish/unpublish.
- **Demo mode** (`--demo` flag, `NOTEELI_DEMO_MODE=1`). The app runs as
  a public read-only showcase: every mutating service method (save,
  create, rename, delete, move, upload, reorder, preference update,
  profile mgmt) raises `DemoReadOnlyError` → 403 with a friendly
  message. Auth is bypassed (auto-login as "Demo guest"), the bundled
  `demo-content/` tree is copied into the configured content root on
  startup so the demo always boots from a clean state, and the
  frontend hides every write-only button (Save, New file/folder,
  Upload, Profiles tab, kebab menu) plus shows a sticky banner
  explaining the situation. Designed for a separate systemd service
  on a dedicated port behind `demo.noteeli.com`.
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
