# Noteeli — Functionalities Inventory

A living catalogue of every user-facing feature in Noteeli, kept in sync with
the codebase and the automated test suite. Use it as the canonical answer to
"does Noteeli do X?" and as a regression checklist when shipping changes.

## Quick index

The most-used features, by everyday name. Each links to its detail row.

### Daily writing

- **WYSIWYG Markdown editor** → [§6 Editors](#6-editors)
- **Auto-save (debounced)** → [§5 Reading & saving](#5-reading--saving-documents)
- **Manual save (Ctrl+S / button)** → [§5 Reading & saving](#5-reading--saving-documents)
- **Inserting / pasting / dragging an image** → [§7 Embedded assets & images](#7-embedded-assets--images)
- **Drag image from the file tree into the editor** → [§7](#7-embedded-assets--images)
- **Auto-copy dragged image into the configured location (Obsidian-style)** → [§7](#7-embedded-assets--images)

### Navigating notes

- **Focus on a folder (tree scope)** → [§3 File tree](#3-file-tree--navigation)
- **File tree with type-aware icons** → [§3](#3-file-tree--navigation)
- **Show / hide dotfiles** → [§3](#3-file-tree--navigation)
- **Drag-drop in the tree (move / reorder)** → [§4 File CRUD](#4-file-crud)
- **Remember the last opened file across reloads** → [§3](#3-file-tree--navigation)

### New file / folder

- **New file / new folder from the context menu or sidebar toolbar** → [§4 File CRUD](#4-file-crud)
- **Rename preserves the original extension** → [§4](#4-file-crud)
- **Delete with double-click confirmation** → [§4](#4-file-crud)
- **Download a file or a folder as ZIP** → [§8 Upload & download](#8-file-upload--download)

### Configuration

- **5 themes (Light / Dark / Noteeli / Webnote / Obsidian)** → [§13 Themes](#13-themes--visual-styling)
- **5 UI languages (en / pl / es / de / ru)** → [§16 i18n](#16-internationalisation)
- **Saved preference profiles** → [§11 Preference profiles](#11-preference-profiles-saved-sets)
- **Code editor with syntax highlighting** → [§6 Editors](#6-editors) (CodeMirror)
- **JSON editor in form mode** → [§6](#6-editors)

### Distribution

- **PWA — installable as an app** → [§17 PWA](#17-pwa-support)
- **Switch the notes source (local / SFTP / Google Drive)** → [§2 Storage backends](#2-storage-backends)
- **Versioning + release-notes links** → [§19 Versioning & releases](#19-versioning--releases)
- **Read-only public demo** → [§18 Demo mode](#18-demo-mode-public-showcase)

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
| `require_api_access` guard on every workspace API endpoint | ✅ `tests/test_auth_guard.py` (10 tests covering tree, file, save, create, delete, rename, upload, preferences, profiles) | implicit dependency |
| Local-host bypass (`127.0.0.1`, `localhost`) | ✅ `test_local_host_bypass_allows_unauthenticated_access` | |
| Workspace HTML root redirects to login | ✅ `test_workspace_root_redirects_to_login` | 303 to `/login` |
| Google Drive OAuth (separate consent for Drive scope) | ❌ | `auth_gdrive_start`, `auth_gdrive_callback` |
| "Local mode" chip when running without Google auth | 🌐 | template branch on `user.is_local` |

## 2. Storage backends

| Feature | Status | Notes |
|---|---|---|
| Local filesystem storage | ⚠️ | every workspace test uses `LocalStorageBackend` (default backend) |
| SFTP / SSH storage | ✅ `tests/test_sftp_backend.py` (15 tests covering exists/is_file/is_dir, read & write text/bytes round-trip, list_children, browse_dirs, create dir & file, rename, delete file, recursive directory delete, rglob_files, root_display) | `SFTPStorageBackend` exercised end-to-end against a paramiko fake that delegates to a real `tmp_path` |
| Google Drive storage | ❌ | `GoogleDriveStorageBackend` |
| Storage backend selection from `source_type` preference | ❌ | `build_backend()` factory |
| SFTP password persisted in SQLite (warning surfaced in UI) | ❌ | preferences hint |
| SFTP session-password fallback when "Remember" is off | ✅ `test_build_backend_uses_session_password_when_db_password_empty`, `test_build_backend_prefers_db_password_over_session` | `session_sftp_password` ContextVar set by middleware in `app/main.py`, read in `build_backend()` |

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
| Path traversal protection (`..`, escape root) | ✅ `test_path_traversal_is_blocked`, `test_delete_blocks_path_traversal`, `test_create_item_rejects_separator_in_name` | `_sanitize_path` |
| Path normalisation (Windows backslashes, double slashes) | ✅ `test_path_sanitisation_handles_windows_style_separators` | |
| Last-opened-file persistence across reloads | 🌐 | `localStorage["last-opened-file"]` |

## 4. File CRUD

| Feature | Status | Notes |
|---|---|---|
| Create directory | ✅ `test_create_directory_and_markdown_file` | |
| Create Markdown file (auto-append `.md` if extension missing) | ✅ `test_create_directory_and_markdown_file` | `_normalize_item_name` |
| Reject duplicate name on create | ✅ `test_create_item_rejects_duplicates` | |
| Rename file/directory | ✅ `test_rename_image_preserves_original_extension`, `test_rename_code_file_preserves_extension`, `test_rename_markdown_keeps_md_suffix_when_user_omits_it`, `test_rename_explicit_extension_replaces_original`, `test_rename_directory_does_not_get_md_suffix`, `test_rename_rejects_path_separators`, `test_rename_rejects_collision_with_existing` | recent regression fix locked in |
| Delete file/directory (with confirm-twice UI gate) | ✅ `test_delete_removes_file`, `test_delete_removes_directory_recursively`, `test_delete_blocks_path_traversal` | service is one-shot, the double-click confirm lives in the frontend |
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
| JSON file detection (`.json`, `.json5`, `.jsonc`) | ✅ `test_editor_file_type_classifies_markdown_json_and_text` | `JSON_EXTENSIONS`, `is_json` |
| Editor file-type routing (`markdown` / `json` / `text`) | ✅ `test_editor_file_type_classifies_markdown_json_and_text`, `test_is_editable_true_for_markdown_and_json` | `get_editor_file_type` |
| Save and read a JSON document (round-trip) | ✅ `test_save_and_read_json_document` | |
| Auto-save (debounced, configurable) | 🌐 | `scheduleAutosave`, `AUTOSAVE_DELAY_MS` |
| Manual save with dirty indicator and disabled state | 🌐 | `markEditorDirty`, `saveButton.disabled` |
| Save button hidden when autosave is enabled | 🌐 | `applyPreferencesToUi` |

## 6. Editors

| Feature | Status | Notes |
|---|---|---|
| Toast UI Markdown WYSIWYG (default for `.md`) | 🌐 | `showEditorMode`, `editor.changeMode("wysiwyg")` |
| Toast UI Markdown source view | 🌐 | toggle persisted to `localStorage["markdown-editor-mode"]` |
| Editor mode toggle button (WYSIWYG ↔ Markdown) hidden for non-md | 🌐 | |
| Undo / Redo toolbar buttons (injected into Toast UI toolbar) | 🌐 | `attachUndoRedoToolbarButtons`, `editor.exec('undo'\|'redo')` |
| Cursor reset to start of doc after `setMarkdown` (fixes silent toolbar buttons) | 🌐 | `editor.moveCursorToStart()` after load |
| JSONEditor — form mode, fully expanded by default | 🌐 | `jsonEditor.setMode("form"); expandAll()` |
| JSONEditor — fallback to code mode for invalid JSON | 🌐 | catch-on-parse-error path |
| CodeMirror — syntax highlighting for ~30 languages (py/js/ts/php/rb/go/rs/java/c/cpp/cs/swift/kt/sh/sql/css/html/yaml/toml/...) | 🌐 | `detectCodeLanguage`, lazy mode loading from CDN |
| CodeMirror — plain-text fallback for unrecognised text files | 🌐 | mode `null` |
| User-pickable code highlighting theme (12 options) + auto | 🌐 | `code-theme-select`, lazy CSS loading |
| Editor font size adjustment (12–28 px) | 🌐 | `applyEditorFontSize` |
| Preview pane for images and PDFs (read-only) | 🌐 | `showPreviewMode` |
| Preview pane for `.docx` (Word) — read-only HTML render | ✅ `test_render_docx_preview_returns_html`, `test_get_preview_kind_classifies_office_documents` | `render_office_preview`, `mammoth` |
| Preview pane for `.xlsx` / `.xlsm` (Excel) — read-only HTML tables, one per sheet | ✅ `test_render_xlsx_preview_returns_html_table` | `render_office_preview`, `openpyxl`, 5000-row safety cap |
| Office preview rejects non-office files | ✅ `test_render_office_preview_rejects_non_office_file` | |

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
| `get_preferences` / `update_preferences` | ✅ `test_update_preferences_persists_basic_fields`, `test_update_preferences_normalises_local_content_root` | |
| Fall back to default content root when saved path is invalid | ✅ `test_get_preferences_falls_back_to_default_content_root_when_saved_path_is_invalid` | |
| Source-type preference (`local` / `sftp` / `gdrive`) | ✅ `test_update_preferences_switches_to_sftp_source_type` | switched via Settings modal |
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
| Reload open file from disk (topbar) — confirms if there are unsaved edits | 🌐 | `refreshFileButton` → `loadFile(selectedPath)` |
| Account menu (user icon) — email/local label + Settings + Logout dropdown | 🌐 | `userMenuToggle`, `#user-menu-dropdown` |
| File search box (magnifier toggle) — filter tree by name fragment, auto-expands matching folders | 🌐 | `filterTreeBySearch`, `treeSearchQuery`, toggle `#tree-search-toggle` |
| New file / new directory toolbar buttons | 🌐 | `openCreateModal` |
| Tree-row context menu with icons + i18n labels (open / scope / upload / new file / new folder / download / copy path / rename / duplicate / refresh / delete) | 🌐 | `renderTreeContextMenu` (recent overhaul) |
| Duplicate file (context menu) → copy in same folder as `<name>_N.<ext>` | ✅ | `duplicate_item`, `test_duplicate_item_*` |

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

## 18. Demo mode (public showcase)

| Feature | Status | Notes |
|---|---|---|
| `--demo` CLI flag and `NOTEELI_DEMO_MODE=1` env var | ✅ (covered indirectly via service-level demo tests) | `app/run.py`, `app/core/config.py` |
| Service-layer write guard (`_block_if_demo`) on save/create/rename/delete/move/upload/reorder/prefs/profiles | ✅ `test_demo_mode_blocks_save_document`, `..._create_item`, `..._rename`, `..._delete`, `..._move`, `..._upload`, `..._update_preferences`, `..._browsed_directory_creation` | every mutator gets the guard |
| Reading still works in demo mode | ✅ `test_demo_mode_allows_reading` | tree, file content, previews |
| Auto-login as "Demo guest" (no `/login` round-trip) | ❌ | `AuthService.get_current_user` early return |
| Sticky banner in the UI | 🌐 | template branch on `demo_mode` |
| Hide write-only UI (Save, New file/folder, Upload, Profiles tab, kebab menu) | 🌐 | `.app-shell.is-demo` CSS overrides |
| Bundled `demo-content/` tree copied into content root on startup | 🌐 | `_seed_demo_content_if_needed` in `app/main.py` |
| Friendly 403 with `{detail, demo: true}` JSON | ❌ | global `DemoReadOnlyError` handler in `app/main.py` |

## 19. Public publish

| Feature | Status | Notes |
|---|---|---|
| Publish a file or a folder under `/{id}/{slug}` | ✅ `test_publish_creates_an_item_and_returns_public_url`, `test_publish_directory` | `PublishService.publish` |
| Slug generation (drops extension, ASCII-folds diacritics) | ✅ `test_slugify_strips_extension_and_diacritics` | `PublishService.slugify` |
| Reject duplicate publish of the same path | ✅ `test_publish_rejects_duplicate_path` | |
| Unpublish | ✅ `test_unpublish_removes_the_entry`, `test_unpublish_404_for_unknown_id` | |
| List published items (used by tree to render globe badges + dispatch context-menu actions) | ✅ `test_list_returns_recently_published` | |
| Path scoping for files (only the published file is reachable) | ✅ `test_is_in_scope_for_file` | `PublishService.is_in_scope` |
| Path scoping for directories (descendants ok, siblings rejected) | ✅ `test_is_in_scope_for_directory` | |
| Cleanup on rename/delete (drops publish entries whose target is gone) | ✅ `test_cleanup_for_removed_path_drops_descendants` | called from `WorkspaceService.{rename,delete}_item` |
| `POST /api/publish` requires auth | ✅ `test_publish_api_requires_auth` | |
| Public viewer page works without auth (`GET /{id}/{slug}`) | ✅ `test_published_view_works_without_auth` | renders read-only `index.mako` |
| Public scoped tree/file APIs work without auth | ✅ `test_published_view_works_without_auth` | `/api/public/tree`, `/api/public/file` |
| Public APIs reject path-traversal beyond the published item | ✅ `test_public_routes_block_path_traversal` | 403 on out-of-scope `path` |
| Public viewer redirects to canonical slug on mismatch | ✅ `test_public_view_redirects_wrong_slug` | 301 |
| Public viewer 404 for unknown id | ✅ `test_public_view_404_for_unknown_id` | |
| Frontend: globe badge on published tree rows | 🌐 | `appendPublishBadge` |
| Frontend: Publish / Unpublish / Copy-public-link entries in the context menu | 🌐 | `renderTreeContextMenu` |
| Frontend: read-only public view (banner + write UI hidden via `body[data-public]`) | 🌐 | `.app-shell.is-public` CSS scope |
| Demo mode blocks publish/unpublish at the API layer | ✅ (route-level guard, 403) | `if get_settings().demo_mode` in router |

## 20. Versioning & releases

| Feature | Status | Notes |
|---|---|---|
| `__version__` read from `pyproject.toml` at startup | ❌ | `app/__init__.py` |
| `noteeli --version` CLI flag | ❌ | `app/run.py` |
| Sidebar version chip linking to release notes | 🌐 | template-rendered |
| GitHub Actions release workflow on `vX.Y.Z` tag | — | `.github/workflows/release.yml`, requires CI |
| Changelog at `CHANGELOG.md` (Keep a Changelog format) | — | manually maintained |
| Installer pin to release tag (`NOTEELI_VERSION=v1.0.0`) | — | `install.sh` env override |

## 21. Git integration

| Feature | Status | Notes |
|---|---|---|
| Auto-detect git repo for the workspace dir (local + SFTP) | ✅ `tests/test_git_service.py` | `GitService`; local `subprocess`, SFTP `paramiko` SSH-exec |
| `git status` parsing (branch, ahead/behind, file states) | ✅ `test_status_lists_*`, `test_branch_parsing_no_upstream` | porcelain v1 `-z`, paths re-relativised to workspace |
| Commit (all) / commit specific paths | ✅ `test_commit_*` | `git add -A` or `git add -- <paths>` then commit |
| Commit + push in one call; fetch / pull / push | ✅ `test_git_api_status_commit_flow` (push failure is graceful) | `/api/git/*` endpoints |
| Tree decorations: file status badges + folder dirty dots | 🌐 | `gitStatusByPath`, `gitDirtyDirs`, `renderNode` |
| Git menu (branch, change list, commit box, remote ops) | 🌐 | `#git-menu`, `renderGitMenu`, `gitCommit`, `gitRemoteOp` |
| Per-item commit / commit & push from context menu | 🌐 | `gitCommitPath` |
| `.git` excluded from the notes tree | ✅ `test_dot_git_excluded_from_tree` | `_build_directory_node` skip |
| Client-path validation + subcommand allow-list (injection guard) | ✅ `test_commit_rejects_path_traversal` | `_safe_rel`, `_ALLOWED_SUBCOMMANDS` |
| Git disabled in demo mode | ✅ `test_demo_mode_disables_git` | runner is `None` in demo |

## 22. Locked workspace (`NOTEELI_LOCK_WORKSPACE`)

| Feature | Status | Notes |
|---|---|---|
| Pin storage source + root; ignore client changes | ✅ `test_locked_update_preferences_pins_storage` | `update_preferences` overrides storage fields when locked |
| Directory picker confined to root (no escaping up the disk) | ✅ `test_browse_confined_cannot_escape_root` | `browse_dirs(confine=True)`, Local + SFTP |
| Unconfined picker still walks up (default) | ✅ `test_browse_unconfined_can_walk_up` | regression guard |
| Block creating dirs outside the root when locked | ✅ `test_locked_blocks_creating_dirs_outside` | `create_browsed_directory` |
| Hide Settings "Source" tab + default to Appearance when locked | 🌐 | mako `_locked` gate, `setActiveSettingsTab` fallback |

---

## Test coverage at a glance

```
tests/
├── test_workspace_service.py        — 47 tests (file CRUD, tree, preview, embed,
│                                       upload/download, rename, delete, path safety,
│                                       editor file-type routing, JSON round-trip,
│                                       office previews docx/xlsx/pptx, demo mode)
├── test_directory_browser_service.py —  3 tests (browser modal backend)
├── test_preferences_service.py      —  4 tests (fallback to default root,
│                                       update fields, source-type switching, content-root norm.)
├── test_preference_profiles.py      —  3 tests (save/list/apply, update, delete)
├── test_auth_guard.py               — 11 tests (every workspace API endpoint
│                                       gets 401 from non-local hosts; HTML root
│                                       redirects to /login; local-host bypass)
└── test_sftp_backend.py             — 15 tests (exists/is_file/is_dir, read &
                                        write round-trips, listing, browse_dirs,
                                        create/rename/delete, rglob, root_display)
                                       — 85 tests total
```

## Coverage gaps (priority order)

These are the largest "if it broke, the user would notice" surfaces with **no**
automated coverage. Each one is a candidate for the next batch of tests.

### Storage backends
1. ~~**SFTP backend**~~ ✅ done — 15 tests via a paramiko fake that delegates to `tmp_path`.
2. **Google Drive backend** — likely mock-only (still pending).

### Editor / frontend (would benefit from a Playwright or Selenium harness)
3. **Drag-and-drop image copy** — Obsidian-style auto-copy when source isn't in target dir.
4. **Auto-save debounce** — fires after delay, doesn't double-save during in-flight save, cancels on file switch.
5. **Cursor reset after `setMarkdown`** — toolbar buttons (Task, list) operate on the new doc.
6. **Tree scope (focus on a folder)** — localStorage-backed, frontend-only.
7. **Drag-to-reorder** in manual sort mode — full UI flow.

### Auth (full flow)
8. **Google OAuth callback** — happy path and disallowed email.
9. **Password login** — happy path, wrong password, missing config.
10. **Logout clears the session.**
11. **Password login throttling** — currently none; worth adding before exposing publicly.

### PWA
12. **Service-worker registration & cache invalidation** — manual only.

### Done since the last audit ✅
- ~~Rename preserves extension~~ — 7 tests covering image, code, markdown, dirs, separators, collisions
- ~~Delete item path traversal~~ — 3 tests including a sensitive-file-survival check
- ~~Auth guard on every API endpoint~~ — 10 tests
- ~~Path normalization edge cases~~ — backslashes, double-dots in names
- ~~Editor file-type routing~~ — `is_editable`, `is_json`, `get_editor_file_type`
- ~~Source-type switching~~ — sftp round-trip
- ~~Update preferences round-trip~~ — basic fields + content-root normalisation

## How to keep this document honest

- When you add a feature, append a row to the matching section.
- When you write a test that covers an existing row, swap the status from ❌ / 🌐 to ✅ and reference the test name.
- When you rip a feature out, delete the row (don't leave dead entries).
- If the table starts to drift from reality, the fix is "audit the codebase and rewrite", not "patch one row".
