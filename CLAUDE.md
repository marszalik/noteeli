# CLAUDE.md

Notes for Claude (and any AI assistant) working on the Noteeli codebase.

## Quick map

```
app/                FastAPI backend, organised by domain (auth/, preferences/, workspace/)
  main.py           app factory + PWA endpoints
  __init__.py       reads __version__ from pyproject.toml at import time
static/             frontend — single big app.js (≈3.8k lines) and app.css
content/            default notes root (overridable via NOTEELI_CONTENT_ROOT)
tests/              pytest suite — service-level tests against tmp_path
install.sh          one-line installer for end users (curl | bash)
ARCHITECTURE.md     architectural conventions (domain-oriented layout, etc.)
CHANGELOG.md        user-facing changelog (Keep a Changelog format)
functionalities.md  inventory of every feature + test coverage status
manual.md           user-facing manual — update it when behaviour users see changes
```

## Before you change anything

1. **Read `functionalities.md`.** It's the authoritative list of what Noteeli
   does and which features have automated coverage. If your change touches a
   feature not on the list, add a row when you're done. If your change adds a
   test for an existing feature, flip its status from ❌ / 🌐 to ✅.
2. **Skim `ARCHITECTURE.md`.** Don't add a top-level `services/` directory
   (we organise by domain), don't introduce a new template engine (Mako only),
   don't fork the frontend into modules unless you're prepared to rewrite the
   whole thing.
3. **Check `CHANGELOG.md` `[Unreleased]` section** — append your change there.

## Testing

```bash
pdm run test            # the canonical command
pytest tests/           # equivalent
pytest tests/test_workspace_service.py::test_save_document_updates_markdown_file
```

The suite uses `tmp_path` for isolation. Every test is hermetic — it builds a
`PreferencesRepository` and `WorkspaceService` against a fresh directory.

**When you fix a bug, write a test for it.** The bug list in
`functionalities.md` (section "Coverage gaps") is the queue of things that
should have been tested but aren't yet. Pick from there when you have spare
cycles.

**When you add a feature, write a test for it.** No exceptions for
"frontend-only" — even if the user-facing behaviour lives in `app.js`,
service-level invariants almost always exist (e.g. drag-to-embed-image goes
through `upload_files` server-side).

## Frontend layout

`static/app.js` is one big IIFE that runs once on page load. Key conventions:

- **No build step.** Code is plain ES2022, served as-is. Don't add a bundler.
- **CDN-loaded libraries:** Toast UI Editor, JSONEditor, CodeMirror, Mermaid.
  Pinned to specific versions in `index.mako`'s `head_extra`.
- **i18n** lives inline in `app.js` as 5 dictionaries (pl/en/es/de/ru). When
  you add a new UI string, add it to **all five** — pick decent translations,
  don't ship "TODO" placeholders.
- **`t(key)`** for dynamic strings, `data-i18n="key"` for static template text.
- **Theme variables** are CSS custom properties on `body[data-theme=…]`. New
  styles should reach for `var(--accent)`, `var(--surface)`, `var(--muted)`,
  etc. — never hardcode hex values that vary between themes.

## Backend conventions

- **One service per domain.** `WorkspaceService`, `PreferencesService`,
  `AuthService`. Routers are thin; they just translate HTTP into service calls
  and back.
- **Storage abstraction.** `StorageBackend` (ABC) has implementations for
  Local / SFTP / GDrive. New filesystem operations go through this interface;
  don't write to `pathlib.Path` directly from a service method.
- **Schemas in `schemas.py` per domain**, Pydantic v2.
- **Settings via `app/core/config.py`.** All env vars are namespaced
  `NOTEELI_*` and configured through pydantic-settings.

## Versioning

Semantic versioning, single source of truth in `pyproject.toml`.

When cutting a release:

1. Move `[Unreleased]` items to a new `[X.Y.Z] - YYYY-MM-DD` section in
   `CHANGELOG.md`.
2. Bump `version` in `pyproject.toml`.
3. Commit, tag (`git tag vX.Y.Z`), push (`git push origin main vX.Y.Z`).
4. The `release.yml` GitHub Actions workflow verifies the tag matches
   `pyproject.toml` and publishes a Release with auto-generated notes.

The currently running version is shown as a chip in the sidebar's bottom-left
corner; clicking it opens the release notes for that version.

## Deploy

The production instance lives at `app.noteeli.com` on `apieli.com` (Hetzner).
Deploy is currently a manual `git pull && systemctl restart noteeli.service`
on the server. nginx is the reverse proxy.

The installer (`install.sh`) is the canonical user-facing setup path for new
deployments. Don't break compatibility with `NOTEELI_DIR`, `NOTEELI_NOTES_DIR`,
`NOTEELI_VERSION` env overrides without updating the README.

## Things that look weird but are intentional

- **Tree icons in `static/app.js`** are inline SVG paths via a single
  `makeSvgIcon(d)` helper. We deliberately don't pull in an icon font /
  framework — the trade-off is a few hundred lines of `M…` paths in exchange
  for zero extra requests.
- **Theme variable colours sometimes use `color-mix(in srgb, …)`.** This is
  modern (Chrome 111+, Firefox 113+, Safari 16.2+) and lets one rule cover
  every theme. Don't replace it with per-theme overrides unless you have a
  good reason.
- **`__version__` is read from `pyproject.toml` via `tomllib`** rather than
  `importlib.metadata`. The latter only works once the package is installed;
  Noteeli is run directly from a checkout, not as a wheel.
- **The Toast UI editor** sometimes silently no-ops toolbar buttons because
  ProseMirror's internal cursor doesn't track DOM focus. We mitigate this by
  calling `editor.moveCursorToStart()` after `editor.setMarkdown(...)`.

## When tests aren't enough

Some classes of regressions don't show up in the service-level suite —
specifically anything that depends on the live ProseMirror state machine,
CodeMirror lazy mode loading, or theme switching across CDN'd CSS files.

For those, the practical workflow is:

1. Reproduce on prod with the Chrome extension MCP (`browser_batch`,
   `javascript_tool`) — drive the real UI and inspect computed styles / DOM
   state via JS.
2. Fix.
3. **Add a feature row to `functionalities.md`** so the next person knows
   the dragon exists, even if there's no test yet.

That last step is the part that's easy to skip — please don't.
