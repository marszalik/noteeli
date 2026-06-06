# Changelog

All notable changes to Noteeli are tracked here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and version numbers follow [Semantic Versioning](https://semver.org/).

- **MAJOR** — incompatible changes (storage layout, breaking API).
- **MINOR** — new functionality, backwards compatible.
- **PATCH** — bug fixes only, backwards compatible.

## [Unreleased]

### Added

- **Reload file button** in the topbar — re-fetches the open file from
  disk (it may have changed in the background via SFTP, another device,
  or an external editor). Confirms before discarding unsaved local edits.

### Changed

- **Topbar tidy-up: Settings and Logout now live under an account menu.**
  A user icon on the right opens a dropdown with the signed-in email (or
  "Local mode"), Settings, and Logout — replacing the loose settings cog,
  email chip, and logout button. Font zoom stays in the topbar.

### Fixed

- **Pin button now toggles** — a second tap on the pin un-pins and
  closes the sidebar. Previously pinning was one-way, which on mobile
  meant the docked drawer covered the whole viewport with no way out
  (the pin button is the only stable touch target inside it).
  The button's `aria-label` / tooltip now also flip between "Pin
  sidebar" and "Unpin sidebar" to match the current state.
- **Pinned sidebar still collapsed on refresh on mobile** (1.2.1 only
  fixed the init path). The `resize` handler also force-collapsed a
  docked sidebar on mobile and persisted the collapse — and mobile
  browsers fire spurious `resize` events on load (URL-bar show/hide,
  keyboard, orientation). The width-shortage auto-collapse is now a
  desktop-only concern; mobile is excluded, so an explicit pin survives.

## [1.2.1] - 2026-05-28

### Added

- **Active profile indicator** — the workspace tracks which saved
  preference profile was last applied and highlights its row in the
  dropdown (subtle accent background + 3px inset border) so it's clear
  which set is currently in effect. Deleting the active profile clears
  the marker automatically.

### Fixed

- **Demo (`demo.noteeli.com`) showed an empty tree and a "configure
  storage" banner.** The demo service runs uvicorn from the hosted app's
  working directory, so pydantic-settings inherited
  `NOTEELI_HOSTED_MODE=1` from a shared `.env`. Hosted mode then forbade
  the demo's local content root. A `Settings` validator now forces
  `hosted_mode=False` whenever `demo_mode=True` — demo and hosted are
  mutually exclusive by design.
- **Saved-profiles button hidden on mobile.** The `@media (max-width: 768px)`
  rule that strips non-essential topbar items was also hiding the
  profiles menu, leaving no way to switch sets on a phone. Restored;
  the dropdown was already viewport-clamped.
- **Pinned sidebar reverted to collapsed after refresh on mobile.**
  `initSidebar` force-collapsed any persisted `docked` mode on mobile.
  Now the user's explicit pin choice is respected across refreshes;
  only an actual width shortage on desktop falls back to collapsed.

## [1.2.0] - 2026-05-28

### Added

- **Duplicate (file context menu)** — copies any file into the same folder
  under `<name>_1.<ext>`, incrementing the suffix (`_2`, `_3`, …) when a
  copy already exists. Binary-safe; the new file is selected/opened.
  Backend: `WorkspaceService.duplicate_item` + `POST /api/items/duplicate`.

- **File search in the sidebar** — a magnifier button next to the refresh
  icon reveals a search box that filters the tree by name fragment
  (case-insensitive). Matching folders auto-expand so deep matches are
  visible; Escape or toggling the button clears it. Labels in all 5
  locales.

- **Settings → Appearance → "Compact layout (no frames)"** — toggle that
  removes the rounded panel borders, drop shadows, and the outer
  padding/gap around the sidebar and workspace. Live preview while the
  Settings modal is open; persisted as `compact_chrome` per user.
  Labels and hint translated to pl/en/es/de/ru.

### Changed

- **New default look:** fresh installs/users now start with the Webnote.li
  theme, the compact (frameless) layout enabled, and the Magazine markdown
  rendering style. Existing instances keep whatever they already had.

- **SFTP password is now always persisted (encrypted at rest).** The
  "Remember password" checkbox is gone — it added no real security (the
  password is encrypted with Fernet using a key derived from
  `NOTEELI_SESSION_SECRET`, so a stolen `noteeli.sqlite3` is useless
  without the env file) and the transient session-only mode was fragile
  on hosted instances. `/api/sftp/test` now persists the verified
  credentials directly (`WorkspaceService.save_sftp_credentials`); the
  `sftp_remember_password` field and the per-request session-password
  plumbing were removed.

- **First-load UX when SFTP is configured but no password is on file:**
  the Settings modal opens on the Source tab with the password input
  focused and a clear "Enter your SFTP password to connect" hint, so
  users no longer see a generic error in the status bar.

- **Tree sidebar readability:** tighter chevron→folder spacing and file
  icons aligned directly under sibling folders at every depth and theme.

### Fixed

- **SFTP authentication failed after picking a folder.** The workspace
  could freeze on tree load with an auth error after configuring SFTP;
  credentials are now persisted on connect, so the tree loads reliably.

- **Context menu hidden under the sidebar in mobile/RWD mode** — bumped
  its z-index above the floating sidebar drawer.

- **PWA served stale CSS/JS after deploys.** Same-origin static assets
  are now fetched network-first (cached copy kept only as an offline
  fallback), so updates appear on the next reload.

- **Onboarding: Settings modal now auto-opens after Google login** when
  storage isn't configured yet, instead of only showing a banner.

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
