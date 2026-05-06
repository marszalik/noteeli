# Noteeli Architecture

This document describes the current shape of the application and the
conventions worth keeping as the project grows.

## Goal

Noteeli is a simple Obsidian-flavoured Markdown notebook that runs in
the browser:

- FastAPI handles HTTP routing and the API
- Mako renders HTML views server-side
- SQLite holds app preferences and the manual tree order
- the frontend in `static/app.js` drives the file tree, modals,
  editing, and drag-and-drop

## Layout principle

The single most important rule: the project is organised **by domain,
not by layer**.

That means everything related to one functional area lives together:

- routing
- domain logic
- data schemas
- Mako views specific to that domain

Instead of one `routers/`, `services/`, `templates/` directory shared
across the whole app, the preferred layout splits the code by domain.

## Directory layout

```text
app/
  core/
    config.py
    templates.py
  domains/
    auth/
      router.py
      service.py
      views/
        login.mako
    preferences/
      repository.py
      schemas.py
      service.py
    workspace/
      router.py
      schemas.py
      service.py
      views/
        index.mako
  views/
    base.mako
static/
  app.css
  app.js
content/
  ...
```

## Where things go

- **Routing** — under each domain's `router.py`. Routers stay thin: they
  decode the HTTP layer and call the domain service.
- **Domain logic** — under `service.py` of each domain. This is where
  invariants, validation, and business rules live.
- **Data schemas** — in `schemas.py` of each domain (Pydantic v2). One
  module per domain keeps the public surface small.
- **Storage** — abstracted behind `StorageBackend` (`workspace/storage.py`)
  with implementations for local filesystem, SFTP, and Google Drive.
  Services never touch `pathlib.Path` directly.
- **SQLite access** — only through `PreferencesRepository`. Routers
  must never run SQL.
- **Templates** — Mako, scoped to their domain in `views/`. Only
  `app/views/base.mako` is shared.
- **Frontend** — single `static/app.js`, no build step. CDN-loaded
  libraries (Toast UI, JSONEditor, CodeMirror, Mermaid).

## Things to avoid

- going back to one global `templates/` directory for all views
- piling all the logic into `app.js` if the UI grows more complex
- direct SQLite access from routers
- mixing auth and workspace concerns
- creating a `utils.py` without a clear domain owner

## Functionality inventory and tests

The full list of what Noteeli does, and the test-coverage status of
every feature, lives in [`functionalities.md`](./functionalities.md)
at the repo root. The file is organised by domain (auth, storage,
file tree, editors, themes, …) and marks each feature as:

- ✅ — covered by an automated test (with the test name)
- ⚠️ — partially covered (e.g. only the happy path)
- ❌ — no test
- 🌐 — frontend-only, no service-level test possible

**Rule: update this document with every code change.** Add a row when
you add a feature, flip the status to ✅ when you write a test, delete
the row when you remove a feature.

## Testing strategy

Tests live in `tests/` and run at the service level (`PreferencesService`
/ `WorkspaceService`) using `tmp_path`. Each test builds a fresh
`LocalStorageBackend` against an isolated directory.

```bash
pdm run test            # canonical command
pytest tests/           # equivalent
```

### When to write a test

- **Bug fix → regression test, always.** If the bug could be introduced
  once, it can be introduced again.
- **New backend feature → service-level test.** Routers get integration
  tests when the logic isn't trivial (auth, sanitisation).
- **Pure frontend behaviour** stays uncovered for now — designing a
  Playwright/Selenium harness is its own project.

### What to test first

The "Coverage gaps" section in `functionalities.md` is the prioritised
queue. The shortlist of currently unprotected surfaces:

1. SFTP and Google Drive storage backends (with mocks)
2. drag-and-drop image copy in the editor (Playwright)
3. autosave debouncing (Playwright)
4. cursor reset after `setMarkdown` (Playwright)
5. tree scope (focus on a folder) — frontend localStorage state

### Don't break the suite

- avoid global state mutation (SFTP cache, files outside `tmp_path`)
- don't depend on test-execution order
- use `tmp_path` instead of manual `mktemp` — pytest handles cleanup
- each test builds its own service instance — never share state
