# Changelog

All notable changes to Noteeli are tracked here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and version numbers follow [Semantic Versioning](https://semver.org/).

- **MAJOR** — incompatible changes (storage layout, breaking API).
- **MINOR** — new functionality, backwards compatible.
- **PATCH** — bug fixes only, backwards compatible.

## [Unreleased]

### Fixed

- **Onboarding: Settings modal now auto-opens after Google login** when
  storage isn't configured yet. Previously users only saw a "Welcome"
  banner with a Settings link and had to click it to start setup.
- **SFTP authentication failed after picking a folder** when the user
  opted out of "Remember password". The verified password was kept in
  the server session for the folder-picker hop, but `build_backend()`
  read `prefs.sftp_password` (empty) and returned an unauthenticated
  connection, freezing the workspace on tree load. A request middleware
  now propagates `request.session["sftp_session_password"]` into a
  ContextVar that `build_backend()` falls back to when the DB column is
  empty — so "Remember = no" means "don't persist across sessions",
  not "fail within this session".
- **Misleading "Błąd usuwania pliku" (Delete error) on any API failure.**
  The generic fallback in `requestJson`/`requestMultipart` reused the
  delete-specific i18n key. Replaced with a dedicated `st_request_failed`
  key across all five languages.

## [1.1.0] - 2026-05-07

### Added

- **Publish / Unpublish for files and folders.** Right-click any tree
  row → "Publish" mints a public URL of the form `/{id}/{slug}`
  served by the same Noteeli instance. The page renders a read-only
  workspace scoped to the published path — sidebar, navigation, and
  server-rendered content, but no editor, no save, no upload, no
  settings, no authentication required. Folders expose every descendant
  through scoped `/api/public/{tree,file,preview}` routes; published
  files only expose themselves. Path traversal beyond the published
  scope returns 403. A globe badge marks published rows in the
  authenticated tree, with "Copy public link" and "Unpublish" in the
  context menu. Renaming or deleting a path automatically drops any
  publish entry that pointed at it. Demo mode blocks publish/unpublish.
- **Server-side rendering for public pages.** Published markdown is
  rendered to HTML by `python-markdown` + Pygments (tables, fenced
  code, syntax highlighting). JSON is pretty-printed and highlighted.
  Code files are highlighted by extension. The public viewer loads only
  Mermaid — no Toast UI, CodeMirror, or JSONEditor — so pages are
  significantly lighter.
- **Demo mode** (`--demo` flag / `NOTEELI_DEMO_MODE=1`). Every mutating
  operation returns 403 with a friendly message. Auth is bypassed
  (auto-login as "Demo guest"), the bundled `demo-content/` tree is
  seeded on startup, and the frontend hides all write-only controls
  behind a sticky banner. Designed for a separate systemd service on a
  dedicated port.
- **Read-only preview for Office formats.** `.docx` (Word) converted
  to HTML via `mammoth`; `.xlsx`/`.xlsm` (Excel) rendered as HTML
  tables via `openpyxl` (max 5 000 rows/sheet); `.pptx` (PowerPoint)
  converted slide-by-slide. All previews run in a sandboxed iframe.
  Distinct sidebar icons per format.
- **SFTP storage backend.** Connect Noteeli to a remote server via
  SFTP; full read/write/rename/delete/move support, same interface as
  the local backend.
- **Markdown rendering style presets.** Five orthogonal looks — Default,
  Minimal, Academic, Warm, Typewriter — switchable in settings without
  touching the theme.
- **Profile management in the topbar.** Save / load / delete named
  preference profiles directly from the header dropdown; the Settings
  → Profiles tab has been removed.
- **Optimistic image drag-and-drop.** Dragging an image from the
  sidebar to the editor now shows the image instantly; copying to the
  configured assets folder happens in the background. The markdown
  reference is silently updated to the final path at save time —
  no re-render, no flash.
- **Themed checkboxes and task-list items.** Native checkboxes and
  Toast UI WYSIWYG task-list checkboxes follow the active colour
  scheme instead of the system default.
- Context menu items now carry icons; labels shortened and translated
  into all five supported languages.

### Fixed

- Drag-from-sidebar to editor broken in Chrome 124+ (`effectAllowed =
  "move"` conflicting with `dropEffect = "link"`). Fixed by setting
  `effectAllowed = "all"` on `dragstart`.
- Context menu on iPad / touch devices now uses a tap button (three-dot
  kebab) instead of long-press, which was unreliable.
- Toolbar Task / List buttons silently no-oped after opening a file
  in WYSIWYG mode.

### Changed

- English is now the project's primary development language (UI strings
  still available in Polish, Spanish, German, Russian).
- PWA manifest served dynamically with versioned icon URLs so CDN /
  Cloudflare caches are invalidated automatically on icon updates.
  `Cache-Control: no-store` prevents proxy caching of the manifest.

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

[Unreleased]: https://github.com/marszalik/noteeli/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/marszalik/noteeli/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/marszalik/noteeli/releases/tag/v1.0.0
