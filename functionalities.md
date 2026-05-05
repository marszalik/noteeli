# Noteeli — Functionalities Inventory

A living catalogue of every user-facing feature in Noteeli, kept in sync with
the codebase and the automated test suite. Use it as the canonical answer to
"does Noteeli do X?" and as a regression checklist when shipping changes.

## Legend

- ✅ — covered by an automated test (the test name follows in code font)
- ⚠️ — partially covered (e.g. only the happy path, or only one storage backend)
- ❌ — no automated test
- 🌐 — frontend-only behaviour (no Python service-level test possible without a browser harness)

Tests live under `tests/`. Run with `pdm run test` or `pytest tests/`.

---

## 1. Authentication & access control

| Feature | Status | Notes |
|---|---|---|
| Google OAuth sign-in (Authlib) | ❌ | `auth/router.py` — `auth_google_login`, `auth_google_callback` |
| Email allowlist for Google login (`NOTEELI_ALLOWED_GOOGLE_EMAILS`) | ❌ | enforced in `auth/service.py` |
| Built-in password login (`NOTEELI_LOCAL_USERNAME` / `_PASSWORD`) | ❌ | bypass for local/dev environments |
| Logout | ❌ | `auth/router.py` — `logout_action` |
| Session middleware (signed cookie) | ❌ | configured in `app/main.py` |
| `require_api_access` guard on every workspace endpoint | ❌ | implicit dependency |
| Google Drive OAuth (separate consent for Drive scope) | ❌ | `auth_gdrive_start`, `auth_gdrive_callback` |
| "Local mode" chip when running without Google auth | 🌐 | template branch on `user.is_local` |

## 2. Storage backends

| Feature | Status | Notes |
|---|---|---|
| Local filesystem storage | ⚠️ | every workspace test uses `LocalStorageBackend` (default backend) |
| SFTP / SSH storage | ❌ | `SFTPStorageBackend`, `invalidate_sftp_cache` |
| Google Drive storage | ❌ | `GoogleDriveStorageBackend` |
| Storage backend selection from `source_type` preference | ❌ | `build_backend()` factory |
| SFTP password persisted in SQLite (warning surfaced in UI) | ❌ | preferences hint |

## 3. File tree & navigation

| Feature | Status | Notes |
|---|---|---|
| Build hierarchical tree from storage root | ✅ `test_build_tree_keeps_directory_hierarchy` | `service.build_tree` |
| Alphabetical sorting | ⚠️ | implicit via `_sort_entries` in build_tree test |
| Manual ordering, persisted in SQLite | ✅ `test_manual_order_is_persisted_in_sqlite` | `reorder_items` |
| `is_editable` / `is_openable_from_tree` classifiers | ⚠️ | indirectly via save/preview tests |
| `get_preview_kind` (image / PDF) | ✅ `test_read_document_returns_image_preview_metadata`, `test_read_document_returns_pdf_preview_metadata` | |
| Tree scope (focus on a subfolder) | 🌐 | `setScopedRoot` in app.js |
| Hidden-file toggle (`.git/`, `.megaignore`, dotfiles) | 🌐 | `filterVisibleTree`, persisted in localStorage |
| File-type icons in the tree (md / json / code / image / pdf / audio / video / archive / text / generic) | 🌐 | `getFileIconInfo` |
| Path traversal protection (`..`, escape root) | ✅ `test_path_traversal_is_blocked` | `_sanitize_path` |
| Last-opened-file persistence across reloads | 🌐 | `localStorage["last-opened-file"]` |

## 4. File CRUD

| Feature | Status | Notes |
|---|---|---|
| Create directory | ✅ `test_create_directory_and_markdown_file` | |
| Create Markdown file (auto-append `.md` if extension missing) | ✅ `test_create_directory_and_markdown_file` | `_normalize_item_name` |
| Reject duplicate name on create | ✅ `test_create_item_rejects_duplicates` | |
| Rename file/directory | ❌ | `rename_item` — note: rename **preserves** the original extension when the new name has no dot (recent fix); not yet covered by a test |
| Delete file/directory (with confirm-twice UI gate) | ❌ | `delete_item` — service is one-shot, the double-click confirm lives in the frontend |
| Move file/directory | ✅ `test_move_item_to_another_directory` | `move_item` |
| Block moving a directory into its own child | ✅ `test_move_directory_into_child_is_blocked` | |
| Drag-to-reorder within parent | 🌐 | `reorderWithinParent` (uses `reorder_items`) |
| Drag-to-move between parents | 🌐 | `moveItemToDirectory` |
| Touch long-press to open context menu (tablets) | 🌐 | `addLongPressContextMenu` |

## 5. Reading & saving documents

| Feature | Status | Notes |
|---|---|---|
| Read Markdown document | ⚠️ | covered indirectly by save tests + preview tests |
| Save Markdown document | ✅ `test_save_document_updates_markdown_file` | |
| Reject save on non-editable file types (e.g. binary) | ✅ `test_non_markdown_file_cannot_be_saved` | |
| Open & save unknown small text files (1 MB cap, valid UTF-8, no NUL bytes) | ✅ `test_unknown_text_file_opens_and_saves_as_plain_text` | `_read_small_text_file`, `MAX_TEXT_FILE_BYTES` |
| JSON file detection (`.json`, `.json5`, `.jsonc`) | ❌ | `JSON_EXTENSIONS`, `is_json` |
| Editor file-type routing (`markdown` / `json` / `text`) | ❌ | `get_editor_file_type` |
| Auto-save (debounced, configurable) | 🌐 | `scheduleAutosave`, `AUTOSAVE_DELAY_MS` |
| Manual save with dirty indicator and disabled state | 🌐 | `markEditorDirty`, `saveButton.disabled` |
| Save button hidden when autosave is enabled | 🌐 | `applyPreferencesToUi` |

## 6. Editors

| Feature | Status | Notes |
|---|---|---|
| Toast UI Markdown WYSIWYG (default for `.md`) | 🌐 | `showEditorMode`, `editor.changeMode("wysiwyg")` |
| Toast UI Markdown source view | 🌐 | toggle persisted to `localStorage["markdown-editor-mode"]` |
| Editor mode toggle button (WYSIWYG ↔ Markdown) hidden for non-md | 🌐 | |
| Cursor reset to start of doc after `setMarkdown` (fixes silent toolbar buttons) | 🌐 | `editor.moveCursorToStart()` after load |
| JSONEditor — form mode, fully expanded by default | 🌐 | `jsonEditor.setMode("form"); expandAll()` |
| JSONEditor — fallback to code mode for invalid JSON | 🌐 | catch-on-parse-error path |
| CodeMirror — syntax highlighting for ~30 languages (py/js/ts/php/rb/go/rs/java/c/cpp/cs/swift/kt/sh/sql/css/html/yaml/toml/...) | 🌐 | `detectCodeLanguage`, lazy mode loading from CDN |
| CodeMirror — plain-text fallback for unrecognised text files | 🌐 | mode `null` |
| User-pickable code highlighting theme (12 options) + auto | 🌐 | `code-theme-select`, lazy CSS loading |
| Editor font size adjustment (12–28 px) | 🌐 | `applyEditorFontSize` |
| Preview pane for images and PDFs (read-only) | 🌐 | `showPreviewMode` |

## 7. Embedded assets & images

| Feature | Status | Notes |
|---|---|---|
| Resolve embedded asset (relative path, same/parent dir) | ✅ `test_resolve_embedded_asset_for_relative_image` | `resolve_embedded_asset` |
| `.excalidraw` → embedded `.excalidraw.png` export when present | ✅ `test_resolve_embedded_asset_uses_excalidraw_export_when_available` | |
| Image upload: clipboard paste, file browse, drag-drop | 🌐 | `handleImageBlob` (Toast UI hook) |
| Image upload location: same dir as note | 🌐 | `image_upload_mode = same_dir` |
| Image upload location: configurable subdir (e.g. `assets/`) | 🌐 | `image_upload_mode = subdir` + `image_upload_subdir` |
| Drag image from sidebar tree → embed in editor | 🌐 | `buildSidebarDropSnippet` |
| Auto-copy dragged image into the configured upload location (Obsidian-style) | 🌐 | recent feature — copies via preview→upload roundtrip |
| Markdown reference-style images preserved through preview | 🌐 | `decorateMarkdownForPreview` |

## 8. File upload & download

| Feature | Status | Notes |
|---|---|---|
| Multi-file upload via UI | ✅ `test_upload_files_creates_multiple_items_and_skips_duplicates` | `upload_files` |
| Skip duplicates within an upload batch | ✅ same | |
| Skip files that already exist at target | ✅ same | |
| Upload-stage UI panel (drop zone, file list, target dir) | 🌐 | `showUploadMode`, `submitUpload` |
| Single-file download (proxied through `/api/download`) | ✅ `test_prepare_download_returns_original_file_for_regular_file` | `prepare_download` |
| Directory download as ZIP | ✅ `test_prepare_download_returns_zip_for_directory` | |

## 9. Directory browser modal

| Feature | Status | Notes |
|---|---|---|
| List subdirectories of the current root | ✅ `test_browse_directories_returns_sorted_subdirectories` | `browse_directories` |
| Reject browsing a file path | ✅ `test_browse_directories_rejects_file_path` | |
| Create directory from inside the browser | ✅ `test_create_browsed_directory_creates_and_opens_new_folder` | `create_browsed_directory` |
| Reject duplicate directory name | ✅ `test_create_browsed_directory_rejects_duplicate_name` | |
| Reject invalid name (path separators, `..`) | ✅ `test_create_browsed_directory_rejects_invalid_name` | |
| Browser modal in settings — "Browse" for content root | 🌐 | wires `browseContentRootButton` |

## 10. Preferences

| Feature | Status | Notes |
|---|---|---|
| `get_preferences` / `update_preferences` | ⚠️ | `update_preferences` is exercised indirectly via profile-apply tests |
| Fall back to default content root when saved path is invalid | ✅ `test_get_preferences_falls_back_to_default_content_root_when_saved_path_is_invalid` | |
| Source-type preference (`local` / `sftp` / `gdrive`) | ❌ | switched via Settings modal |
| Sort mode (`alphabetical` / `manual`) | ⚠️ | manual mode reorder covered by manual_order test |
| Theme (`light` / `dark` / `noteeli` / `webnote` / `obsidian`) | 🌐 | `applyTheme` |
| Interface language (`pl` / `en` / `es` / `de` / `ru`) | 🌐 | `applyLanguage`, `t()` |
| Editor font size | 🌐 | persisted across reloads |
| Auto-save toggle | 🌐 | `autosave_enabled` |
| Image upload mode + subdir | 🌐 | covered above |
| Code highlighting theme — `localStorage["code-theme"]` (frontend-only) | 🌐 | not in backend `AppPreferences` |

## 11. Preference profiles ("saved sets")

| Feature | Status | Notes |
|---|---|---|
| Save current preferences as a named profile | ✅ `test_save_list_and_apply_preference_profile` | `save_preference_profile` |
| List saved profiles | ✅ same | |
| Apply a profile (becomes the active preferences) | ✅ same | `apply_preference_profile` |
| Update an existing profile | ✅ `test_update_preference_profile_changes_existing_entry` | |
| Delete a profile | ✅ `test_delete_preference_profile_removes_entry` | |
| Quick-switch dropdown in topbar | 🌐 | `togglePreferenceProfilesButton` |
| Profile management lives in Settings → Profile tab | 🌐 | recent UX move |

## 12. Settings modal UI

| Feature | Status | Notes |
|---|---|---|
| 5-tab sidebar layout (Source / Appearance / Editor / Images / Profiles) | 🌐 | `setActiveSettingsTab`, last tab persisted in localStorage |
| Wide modal (880 px), responsive (collapses tabs to a horizontal scroller below 640 px) | 🌐 | `.modal-card-settings` |
| Translated tab labels via `data-i18n` | 🌐 | |
| Smaller buttons inside any modal via scoped CSS | 🌐 | `.modal-actions .button` |

## 13. Themes & visual styling

| Feature | Status | Notes |
|---|---|---|
| 5 themes: Light / Dark / Noteeli / Webnote.li / Obsidian | 🌐 | `body[data-theme=…]` palette blocks |
| Webnote theme: IBM Plex Sans/Serif/Mono, single-panel layout (sidebar + editor share one outline) | 🌐 | based on the marketing-site mockup |
| Themed scrollbars across all themes (`color-mix` from `--muted`) | 🌐 | global `*` rule |
| Themed native checkboxes (`appearance: none`, accent-coloured) | 🌐 | dark tick on gold themes |
| Themed Toast UI task-list checkboxes (`::before` override) | 🌐 | dark tick on gold themes |
| Editor zoom controls (font ↑↓) | 🌐 | `adjustEditorFontSize` |
| Sidebar version chip linking to GitHub release | 🌐 | reads `__version__` from `pyproject.toml` at startup |

## 14. Diagrams (WYSIWYG previews)

| Feature | Status | Notes |
|---|---|---|
| Mermaid renders in WYSIWYG and in source preview | 🌐 | `renderWysiwygDiagrams`, `scheduleMermaidPreviewRender` |
| PlantUML rendered as remote SVG via `plantuml.com` | 🌐 | `plantUmlSvgUrl` (hex-encoded) |
| Custom Insert Diagram dropdown in the toolbar | 🌐 | `attachDiagramToolbarButtons` |
| Diagram block snippets (mermaid / plantuml templates) | 🌐 | `buildDiagramSnippet` |
| Cached Mermaid SVGs survive WYSIWYG ↔ Markdown switches | 🌐 | `restoreCachedMermaidDiagrams` |
| Mermaid theme follows app theme | 🌐 | `getMermaidTheme` |

## 15. Sidebar UX

| Feature | Status | Notes |
|---|---|---|
| Collapsible sidebar (hamburger, pin) | 🌐 | `setSidebarMode("collapsed" / "overlay" / "docked")` |
| Drag-resize sidebar width, persisted | 🌐 | `setSidebarWidth` |
| Mobile overlay mode with backdrop | 🌐 | `.app-shell.sidebar-overlay::before` |
| Refresh tree button | 🌐 | `refreshButton` |
| New file / new directory toolbar buttons | 🌐 | `openCreateModal` |
| Tree-row context menu with icons + i18n labels (open / scope / upload / new file / new folder / download / copy path / rename / refresh / delete) | 🌐 | `renderTreeContextMenu` (recent overhaul) |

## 16. Internationalisation

| Feature | Status | Notes |
|---|---|---|
| 5 UI languages: pl / en / es / de / ru | 🌐 | translations table inline in `app.js` |
| `data-i18n` attribute drives static text | 🌐 | `applyLanguage` |
| `t(key)` for dynamic strings | 🌐 | |
| Browser title not yet translated | — | `<title>Noteeli</title>` is fixed |

## 17. PWA support

| Feature | Status | Notes |
|---|---|---|
| `manifest.webmanifest` served from root | ❌ | `app/main.py` |
| `service-worker.js` served at root scope | ❌ | offline shell, asset caching |
| Installable as a desktop/mobile app | 🌐 | tested manually only |

## 18. Versioning & releases

| Feature | Status | Notes |
|---|---|---|
| `__version__` read from `pyproject.toml` at startup | ❌ | `app/__init__.py` |
| `noteeli --version` CLI flag | ❌ | `app/run.py` |
| Sidebar version chip linking to release notes | 🌐 | template-rendered |
| GitHub Actions release workflow on `vX.Y.Z` tag | — | `.github/workflows/release.yml`, requires CI |
| Changelog at `CHANGELOG.md` (Keep a Changelog format) | — | manually maintained |
| Installer pin to release tag (`NOTEELI_VERSION=v1.0.0`) | — | `install.sh` env override |

---

## Test coverage at a glance

```
tests/
├── test_workspace_service.py       — 18 tests (file CRUD, tree, preview, embed, upload/download)
├── test_directory_browser_service.py — 3 tests (browser modal backend)
├── test_preferences_service.py     — 1 test (fallback to default content root)
└── test_preference_profiles.py     — 3 tests (save/list/apply, update, delete)
                                     —  25 tests total
```

## Coverage gaps (priority order)

These are the largest "if it broke, the user would notice" surfaces with **no**
automated coverage. Each one is a candidate for the next batch of tests.

### Critical / safety
1. **Rename preserves extension** — recent regression caused by `_normalize_item_name` clobbering image suffixes. A test would lock in: `pic.png → pic2 → pic2.png`, `note.md → note2 → note2.md`.
2. **Delete item** — `delete_item` deletes any path; needs a test that confirms it refuses to traverse outside the content root.
3. **Auth guard** — every API endpoint requires a session; no test verifies that an unauthenticated request gets 401/redirect.
4. **Path normalization edge cases** — embedded `\\`, leading `/`, Unicode normalization.

### Storage backends
5. **SFTP backend** — at minimum, a fake-SFTP integration test (e.g. paramiko stub) covering exists/list/read/write/rename.
6. **Google Drive backend** — likely mock-only.

### Editor / frontend (would benefit from a Playwright or Selenium harness)
7. **Editor file-type routing** — Markdown → Toast UI, JSON → JSONEditor, code → CodeMirror, plain text → CodeMirror.
8. **Drag-and-drop image copy** — Obsidian-style auto-copy when source isn't in target dir.
9. **Auto-save debounce** — fires after delay, doesn't double-save during in-flight save, cancels on file switch.
10. **Cursor reset after `setMarkdown`** — toolbar buttons (Task, list) operate on the new doc.

### Preferences
11. **Source-type switching** — local → sftp → gdrive round-trip via `update_preferences`.
12. **Theme/language application** — frontend, but also that backend persists the value.

### PWA
13. **Service-worker registration & cache invalidation** — manual only.

### Auth
14. **Google OAuth callback** — happy path and disallowed email.
15. **Password login throttling** — currently none, worth adding.

## How to keep this document honest

- When you add a feature, append a row to the matching section.
- When you write a test that covers an existing row, swap the status from ❌ / 🌐 to ✅ and reference the test name.
- When you rip a feature out, delete the row (don't leave dead entries).
- If the table starts to drift from reality, the fix is "audit the codebase and rewrite", not "patch one row".
