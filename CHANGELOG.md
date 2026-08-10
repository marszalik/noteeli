# Changelog

All notable changes to Noteeli are tracked here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and version numbers follow [Semantic Versioning](https://semver.org/).

- **MAJOR** — incompatible changes (storage layout, breaking API).
- **MINOR** — new functionality, backwards compatible.
- **PATCH** — bug fixes only, backwards compatible.

## [Unreleased]

### Added

- **Markdown-backed kanban boards** (Obsidian Kanban compatible). Any `.md`
  file with `kanban-plugin:` in its frontmatter opens as a drag & drop
  board: `## ` headings are columns, list items are cards. Nested list
  items render as separate subtask cards (arbitrary depth) indented under
  their parent with a progress chip; a parent card cannot leave its column
  until its subtasks are moved away, and a subtask dragged to another
  column becomes a standalone card. Cards, subtasks and columns can be
  added, edited and deleted on the board. Unrecognised file content
  (frontmatter, prose, card descriptions, `%% kanban:settings`)
  round-trips untouched. Detection is purely content-based — there is no
  separate board file type.
- **Four-way editor mode button.** The topbar toggle now cycles
  WYSIWYG → Markdown → Kanban → Text (plain-text CodeMirror view) for
  markdown files. Picking Kanban on a regular note converts it in place:
  `## ` headings become columns (an empty note gets three default ones)
  and the `kanban-plugin` frontmatter is written together with the first
  real board edit — merely switching views never touches the file.

### Fixed

- **Editor links no longer hijack plain clicks.** 1.5.10 made a plain
  click in the WYSIWYG follow internal links, so clicking into a note's
  text near a link teleported you to another note mid-edit. Standard
  editor behavior now: **Ctrl/Cmd+click** follows links in the editor,
  a plain click just places the cursor. Published (read-only) pages
  keep plain-click navigation.

## [1.5.10] - 2026-07-15

### Added

- **Internal note links now work.** Clicking a relative Markdown link
  ([harmonogram](harmonogram/zjazdy.md)) opens the target note inside
  Noteeli — in the WYSIWYG editor (unsaved edits are autosave-flushed
  first) and in the public read-only view, where the rendered note
  swaps in place instead of the browser navigating away. `../` paths
  resolve, escapes above the workspace root are ignored, and external
  links open in a new tab. The public renderer no longer rewrites
  note-to-note links through the asset-preview endpoint (images and
  other assets still are).

## [1.5.9] - 2026-07-15

### Added

- **Instance retirement redirect** (`NOTEELI_REDIRECT_ALL_TO=<url>`).
  When set, the app serves nothing but a permanent 301 to the given URL
  — for decommissioned instances whose domain should keep forwarding
  visitors somewhere alive, without touching the reverse proxy.

## [1.5.8] - 2026-07-15

### Changed

- **The sidebar no longer shows the server's full filesystem path.**
  The workspace root is displayed relative to the instance's
  `NOTEELI_CONTENT_ROOT`: "/" when they're the same, "/sub/dir" for a
  subdirectory — so users of a shared instance see a clean label
  instead of the server's directory layout. A workspace deliberately
  pointed outside the content root still shows its real path, and the
  Settings input keeps the full path (it's an input, not a label).
  SFTP/GDrive labels unchanged.

## [1.5.7] - 2026-07-15

### Added

- **Auto-push after checkpoints** (`NOTEELI_GIT_AUTOCOMMIT_PUSH=1`, needs
  `NOTEELI_GIT_AUTOCOMMIT`). Each successful silent checkpoint is pushed
  to the repo's remote, making an external git remote (e.g. a private
  GitHub repo) the durable source of truth for a workspace. Never
  destructive: if the remote moved ahead, clean divergence is replayed
  with `pull --rebase` (checkpoint authorship preserved); a content
  conflict aborts the rebase and *parks* the sync — local commits stay
  intact, nothing is overwritten, and the git menu's ↑/↓ counters show
  the stalled state for a human to resolve once. No remote configured →
  silent no-op.

## [1.5.6] - 2026-07-15

### Added

- **Shared pages can navigate between published notes.** The public
  sidebar is back (also for single-file publishes) and now carries a
  "Published notes" section listing every published item of the
  instance — display names only, never filesystem paths — with the
  current page highlighted. Visitors with one link can reach the other
  things you've shared. The section hides itself when only one item is
  published. New public endpoint `/api/public/published` returns
  name + kind + public URL and deliberately nothing else.

## [1.5.5] - 2026-07-15

### Changed

- **The public-view banner stopped being an ad.** The loud green
  gradient bar on shared pages is now a slim near-black strip with
  small gray text (and slightly less height), so the published note —
  not the banner — is what the page is about.

## [1.5.4] - 2026-07-15

### Fixed

- **Public view no longer looks like a crippled editor.** A published
  single file now reads like an article: the sidebar (which only
  repeated the file's own name) is gone, the content takes the full
  page in a readable centered column, and the browser tab is titled
  after the note instead of just "Noteeli". The editor status line
  ("File ready for editing…" — on a read-only page!) and the dotfiles
  toggle are hidden in every public view. Folder publishes keep the
  sidebar for navigation. Also fixed the content area collapsing into
  the wrong (zero-height/width) grid track when the topbar/sidebar are
  hidden.

## [1.5.3] - 2026-07-15

### Fixed

- **Dead public links now show a human page instead of raw JSON.**
  When a published note is unpublished — or its source file is renamed
  or deleted, which auto-drops the publish entry — visiting the old
  public link used to dump `{"detail": "Published item #1 does not
  exist."}` into the browser. It now renders a proper "this page is no
  longer published" notice (PL + EN, light/dark aware) with a 404
  status.

## [1.5.2] - 2026-07-15

### Changed

- **History & blame moved into the git menu.** The standalone topbar
  clock icon read as "undo/revert changes"; the entry now lives in the
  git dropdown as "History & authors" with the open file's name under
  it, next to the other git actions where it belongs.

## [1.5.1] - 2026-07-15

### Added

- **File history & blame view.** A clock icon in the topbar (visible when
  the workspace is a git repo and a file is open) opens a modal with two
  tabs: **History** lists every commit that touched the file (author,
  relative date, subject — renames followed); clicking a commit unfolds a
  **word-level diff** of what it changed, which for prose is readable
  where a line diff is not. **Line authors** is a blame view: each line
  carries an author gutter (color-coded per person) and a freshness tint,
  so "who wrote this and how recently" is visible at a glance; lines not
  yet committed are marked as such. Read-only endpoints
  (`/api/git/log|blame|diff`) with the same auth gate as the rest of the
  git API and strict revision/path validation. Pairs with silent
  checkpoints from 1.5.0 — history now has per-person, per-session
  granularity worth looking at.

## [1.5.0] - 2026-07-15

### Added

- **User manual** (`manual.md`) — a complete user-facing guide to every
  feature: workspace tour, files & folders, editors, saving/autosave,
  images, diagrams, publishing, git (including the new silent
  checkpoints), personalisation, storage backends, accounts, and an
  admin env-var reference. Linked from the README.

- **Silent checkpoint commits** (`NOTEELI_GIT_AUTOCOMMIT=1`). "End of an
  editing session" isn't an observable event, so it's approximated with
  an idle debounce: every save queues the file, and once it has been
  quiet for `NOTEELI_GIT_AUTOCOMMIT_IDLE_SECONDS` (default 300) a
  background loop commits it — signed by whoever saved it last, same
  attribution rule as manual commits from the git menu. One commit per
  author per flush, so `git blame`/history in a shared workspace stays
  truthful even when nobody commits by hand. Pending checkpoints are
  force-flushed on shutdown, so a service restart loses nothing.
  Groundwork for the upcoming blame/diff view.

### Fixed

- **Git badge now updates after autosave.** Autosaving a document left the
  sidebar git counter (and the tree's modified markers) stale until a full
  page reload — only a manual save refreshed them, because it reloads the
  whole tree. Autosave now triggers a lightweight git-status refresh after
  each successful save (fire-and-forget, so a slow SFTP status call never
  delays the autosave loop). Covered by a new headless-Chromium e2e test
  (`tests/test_e2e_git_badge.py`) that boots a real server over a throwaway
  git repo, types into the editor and asserts the badge appears without a
  reload; it skips itself when Chromium or the editor CDN is unavailable.

## [1.4.1] - 2026-07-09

### Fixed

- **Restored the manifest, theme-color and apple-touch-icon head tags**
  that were dropped together with the service worker in 1.4.0. None of
  them needs a service worker, and without them a fresh local install got
  no mobile status-bar tint and no add-to-home-screen icon. The
  `/manifest.webmanifest` route is back (icons carry `?v=` cache-busters,
  served `no-store`); the service worker itself stays gone — the shell
  still registers nothing and the kill-switch keeps cleaning up old
  installs. Bonus: the `theme-color` meta now follows the active theme,
  so the light theme gets a light status bar instead of the old
  hardcoded dark one.

## [1.4.0] - 2026-07-09

### Removed

- **Dropped the PWA / service worker.** It only cached static assets and
  the main effect was stale versions lingering in browsers (deploys not
  showing up). `static/service-worker.js` is now a **kill-switch**:
  browsers still running the old SW re-fetch it, wipe all caches,
  unregister, and reload — no manual DevTools dance. The manifest link,
  `apple-touch-icon`, theme-color and apple-mobile metas were removed from
  the page head (the favicon stays); the `/manifest.webmanifest` route is
  gone. New visitors register nothing.

### Added

- **Rotating file logs.** Each instance now writes
  `<data_dir>/logs/noteeli.log`, rotated daily, keeping
  `NOTEELI_LOG_RETENTION_DAYS` days (default 14). Covers application
  logs (auth denials, git failures, unexpected errors) **and** uvicorn
  access/error logs, so incidents stay diagnosable after the systemd
  journal rotates away. Console/journal output is unchanged.

### Fixed

- **Custom toolbar buttons (undo / redo, diagram menu) no longer render as
  white boxes with dark glyphs on dark themes.** Toast UI's own stylesheet
  styles `.toastui-editor-defaultUI-toolbar button` with a hardcoded
  near-white border (and the Obsidian theme forced a #808080 glyph); both
  rules out-ranked `.noteeli-toolbar-button`'s theme variables. Invisible on
  the light theme, glaring on every dark one. The theme variables are now
  re-asserted with higher specificity, verified across all five themes.
- **`pdm run test` now runs the whole suite.** It silently ran only
  `test_workspace_service.py` (54 of 153 tests), hiding failures in other
  files. The suite is also hermetic now: a new `tests/conftest.py` scrubs
  `NOTEELI_*` env vars, ignores the repo-root `.env`, and sandboxes the
  content/data dirs — so tests pass on a production box with a real `.env`
  (previously hosted-mode settings leaked in and dozens of tests failed,
  one even tried to open a live SFTP connection from the production
  preferences DB).
- **Blank boolean env vars no longer crash startup.** A bare
  `NOTEELI_LOCK_WORKSPACE=` (or `NOTEELI_HOSTED_MODE=` / `NOTEELI_DEMO_MODE=`)
  line in `.env` arrives as an empty string, which pydantic couldn't parse as
  a bool and refused to start. Blank now means "not set" and resolves to the
  disabled default, so you no longer have to write `=0`.
- **Admin allowlist accepts space-separated emails again (fixes a hosted
  redirect loop).** `NOTEELI_ADMIN_EMAILS` / `NOTEELI_ALLOWED_GOOGLE_EMAILS`
  were split on commas only, but the production `.env` listed admins
  separated by spaces. The whole string collapsed into one bogus entry, so
  `is_admin()` returned False for a real admin — who, in hosted mode without
  an active subscription, was bounced to `/subscribe` and back to `/`
  forever (the browser showed nothing but redirects). Both settings are now
  split on any run of commas and/or whitespace.

- **Gmail dots no longer lock users out of the allowlist.** Google OAuth
  returns the canonical (dotless) gmail address, while operators naturally
  type the dotted variant into `NOTEELI_ALLOWED_GOOGLE_EMAILS` — the
  verbatim comparison then denied a legitimate user. Allowlist and admin
  checks now canonicalise gmail/googlemail addresses (dots stripped,
  domains unified); dots remain significant for all other domains.

- **Locked workspaces (`NOTEELI_LOCK_WORKSPACE=1`) were completely broken
  in the UI** — nothing saved (settings, files), the tree stayed empty.
  The lock removes the Settings "Source" panel from the HTML, but
  `app.js` still bound a click handler to the panel's Browse button
  without a null guard; the resulting TypeError aborted the entire init,
  so no later handler (saves, tree load, settings) was ever wired.
  The binding is now optional-chained (plus the directory-browser flow
  guards `content-root-input`).

- **Stale deploys now self-heal — no manual cache wipe.** After a deploy,
  clients stuck on an old service worker (from the previous PWA) or a
  cached HTML could keep running outdated JS and silently break saves —
  worst on iOS/Safari, where the kill-switch service worker updates
  lazily. Two changes fix this without asking users to touch DevTools:
  the app-shell HTML is now served `Cache-Control: no-store` (so every
  navigation re-fetches a fresh document with the cache-busted asset
  URLs), and a small **service-worker self-heal script runs inline from
  that HTML `<head>`** — before `app.js` — unregistering any leftover
  service worker, purging Cache Storage, and reloading once. Because it
  lives in the always-fresh HTML rather than in `app.js` (which may itself
  be served stale), it reaches clients the old `app.js` cleanup never
  could. Returning users, including iPad, recover on their next load.

- **Noteeli's SQLite DB no longer clutters the notes tree.** When the
  data dir sits inside the notes folder (e.g. `NOTEELI_DATA_DIR` pointed
  at the notes root), the database and its `-wal`/`-shm`/`-journal`
  sidecars — and a `.noteeli` data subdirectory — are now excluded from
  the file tree and from git status, so they don't mix with real notes or
  show up as uncommitted changes. (Fresh installs already keep the DB in a
  separate dir; this protects setups where it ended up alongside notes.)

### Added

- **Per-user preferences and saved profiles.** Each logged-in user now
  has their own theme, font size, sort mode, autosave, language, compact
  layout, active profile, and saved profile sets — keyed by their email.
  The **storage stays shared** (source / content root / SFTP / Drive),
  which is exactly what a collaborative workspace wants: everyone works
  on the same directory + git, but each person keeps their own look.
  Backend: new `user_settings` table overlays the per-user personal keys
  on top of the instance defaults; `preference_profiles` gains a
  `user_key` column (names are now unique per user). Existing single-user
  DBs migrate cleanly — old profiles become a shared/legacy bucket.
- **Git commits are signed by the logged-in user.** In a shared workspace,
  a commit is attributed (author + committer) to whoever made it — using
  their Google name + email — instead of the instance's ambient git
  config, so the history shows who did what. Localhost/demo synthetic
  users keep the repo's own git identity (a solo self-hoster isn't stamped
  `local@noteeli`).
- **Locked workspace (`NOTEELI_LOCK_WORKSPACE=1`).** Pins the storage
  source and root: users can't change the source / content root / SFTP
  settings, the Settings "Source" tab is hidden, and the directory picker
  is confined to the workspace root (no walking up the disk, no repointing
  the workspace). Lets you safely share a single directory with a group —
  combine with an email allowlist (self-hosted) or the Free-access panel
  (hosted). Works in any mode. Closes a gap where any logged-in user could
  browse the whole filesystem from the directory picker and repoint the
  workspace anywhere.

## [1.3.0] - 2026-06-29

### Added

- **Git integration for the workspace.** When the directory a workspace
  points at is a git repository, git features light up automatically
  (no config). Works for both **local** filesystem and **SFTP** sources
  — SFTP runs git over SSH on the remote server using the SFTP
  credentials. Google Drive has no git.
  - **Tree decorations:** changed files get a status badge (M/A/D/?/R)
    and folders containing changes get a coloured dot.
  - **Git menu** (icon in the topbar, next to zoom/profiles) with a
    change count badge: branch + ahead/behind, the list of changes, a
    commit message box with **Commit** / **Commit & Push**, and
    **Fetch / Pull / Push** buttons (remote + upstream assumed set).
  - **Per-item commit:** the tree context menu gains "Commit (this item)"
    and "Commit & push (this item)" to stage and commit just one file or
    folder.
  - Read-only demo has git disabled. The `.git` directory is excluded
    from the notes tree. Backend: new `app/domains/git/` domain with a
    runner abstraction (`subprocess` locally, paramiko SSH-exec for SFTP),
    a fixed subcommand allow-list, and client-path validation.
- **Undo / Redo buttons in the WYSIWYG editor toolbar.** Toast UI only
  shipped the keyboard shortcuts (Ctrl/Cmd+Z); now there's a visible
  Undo/Redo group at the front of the toolbar. Labels in all 5 locales.
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

[Unreleased]: https://github.com/marszalik/noteeli/compare/v1.5.11...HEAD
[1.5.11]: https://github.com/marszalik/noteeli/compare/v1.5.10...v1.5.11
[1.5.10]: https://github.com/marszalik/noteeli/compare/v1.5.9...v1.5.10
[1.5.9]: https://github.com/marszalik/noteeli/compare/v1.5.8...v1.5.9
[1.5.8]: https://github.com/marszalik/noteeli/compare/v1.5.7...v1.5.8
[1.5.7]: https://github.com/marszalik/noteeli/compare/v1.5.6...v1.5.7
[1.5.6]: https://github.com/marszalik/noteeli/compare/v1.5.5...v1.5.6
[1.5.5]: https://github.com/marszalik/noteeli/compare/v1.5.4...v1.5.5
[1.5.4]: https://github.com/marszalik/noteeli/compare/v1.5.3...v1.5.4
[1.5.3]: https://github.com/marszalik/noteeli/compare/v1.5.2...v1.5.3
[1.5.2]: https://github.com/marszalik/noteeli/compare/v1.5.1...v1.5.2
[1.5.1]: https://github.com/marszalik/noteeli/compare/v1.5.0...v1.5.1
[1.5.0]: https://github.com/marszalik/noteeli/compare/v1.4.1...v1.5.0
[1.1.0]: https://github.com/marszalik/noteeli/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/marszalik/noteeli/releases/tag/v1.0.0
