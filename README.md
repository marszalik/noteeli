# Noteeli

A Python web application built with FastAPI and Mako templates. It displays a tree of note folders, lets you browse Markdown files, and edit them in a WYSIWYG interface.

Project architecture and conventions are described in `ARCHITECTURE.md`.

## Features

- folder and file tree in the sidebar
- Markdown preview and editing on the right side
- Google login for traffic outside `127.0.0.1`, `localhost`, and `::1`
- local auth bypass for development addresses
- SQLite in `.noteeli/noteeli.sqlite3` for settings and manual tree ordering
- UI-based configuration for notes root and sorting

## Running locally

1. Copy `.env.example` to `.env` and fill in the values.
2. Install dependencies:

```bash
python3 -m venv .venv
./.venv/bin/pip install -e ".[dev]"
```

Or with PDM:

```bash
pdm install -d
```

3. Start the server:

```bash
./.venv/bin/uvicorn app.main:app --reload
```

Or with PDM:

```bash
pdm run dev
```

4. Open the app at `http://127.0.0.1:8000`.

## Environment variables

- `NOTEELI_CONTENT_ROOT` - base directory for notes
- `NOTEELI_DATA_DIR` - directory for SQLite and app data
- `NOTEELI_SESSION_SECRET` - session secret
- `NOTEELI_GOOGLE_CLIENT_ID` - Google OAuth client ID
- `NOTEELI_GOOGLE_CLIENT_SECRET` - Google OAuth client secret

## License

This project is licensed under `AGPL-3.0-or-later`.

This license fits a web-based product that can be both self-hosted and used as a network service. See `LICENSE` for the full text.
