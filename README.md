# Noteeli

Noteeli is a Markdown-first web workspace built around real folders, plain files, and storage you control.

It is designed for people who want an Obsidian-like workflow in the browser without moving their notes into a proprietary format or storage model.

Website: [noteeli.com](https://noteeli.com)

![Noteeli](https://noteeli.com/static/screenshots/noteeli-markdown-workspace.png)

## Quick install

One line, on Linux or macOS:

```bash
curl -fsSL https://raw.githubusercontent.com/marszalik/noteeli/main/install.sh | bash
```

This clones Noteeli into `~/.noteeli`, sets up a Python virtualenv, generates a
random session secret in `.env`, and installs a `noteeli` command in
`~/.local/bin`. Then:

```bash
noteeli                  # dev mode, auto-reload
noteeli prod             # production
noteeli prod --port 9000 # specific port
```

Open <http://127.0.0.1:8000>. Notes live in `~/notes` by default. Re-running the
installer fast-forwards to the latest version without touching your `.env` or
notes.

Pin to a release tag instead of `main`:

```bash
NOTEELI_VERSION=v1.0.0 \
  bash -c 'curl -fsSL https://raw.githubusercontent.com/marszalik/noteeli/main/install.sh | bash'
```

Custom paths:

```bash
NOTEELI_DIR=/opt/noteeli NOTEELI_NOTES_DIR=/data/notes \
  bash -c 'curl -fsSL https://raw.githubusercontent.com/marszalik/noteeli/main/install.sh | bash'
```

Requires Python 3.11+ and git. On Debian/Ubuntu also: `sudo apt install python3-venv`.

The installer is plain shell — feel free to read it first:
[install.sh](https://github.com/marszalik/noteeli/blob/main/install.sh).

## Versioning & releases

Noteeli follows [Semantic Versioning](https://semver.org/) — `MAJOR.MINOR.PATCH`.
Each version is tagged in git as `vX.Y.Z` and published as a
[GitHub Release](https://github.com/marszalik/noteeli/releases) with notes
generated from the commits since the previous tag. The full human-readable log
lives in [`CHANGELOG.md`](./CHANGELOG.md).

The currently running version is shown as a small chip at the bottom of the
sidebar — clicking it opens the release notes for that version. From the CLI:

```bash
noteeli --version
```

### Cutting a release (maintainers)

1. Update `CHANGELOG.md` — move items from `[Unreleased]` to a new
   `[X.Y.Z] - YYYY-MM-DD` section.
2. Bump `version` in `pyproject.toml` to match.
3. Commit (`Release vX.Y.Z`) and tag:

   ```bash
   git tag vX.Y.Z
   git push origin main vX.Y.Z
   ```

The `release.yml` workflow verifies the tag matches `pyproject.toml`, then
publishes a GitHub Release with auto-generated notes.

## What Noteeli is for

Noteeli is built for workflows where plain files matter:

- private Markdown notes available in the browser
- folder-based knowledge bases
- self-hosted note workflows
- file-based content and lightweight documentation
- browser access on machines where local note setups are not practical

## Core ideas

- Markdown first
- real folder tree and sidebar
- browser-based editing
- storage under user control
- low lock-in
- self-hosted or hosted product direction

## Why Noteeli

Many note tools force a tradeoff between browser access and file ownership.

Noteeli is built around a simpler model:

- keep notes in plain Markdown files
- keep real folders instead of abstract note containers
- use storage you already control
- access the workspace in the browser when local setups are inconvenient

The goal is not to replace every notes app. The goal is to make browser-based Markdown workflows feel direct again.

## Current capabilities

- folder and file tree in the sidebar
- Markdown preview and editing
- Google login for non-local traffic
- local auth bypass for development environments
- SQLite-backed app preferences and manual tree ordering
- UI-based configuration for content root and sorting
- support for switching between different content sources and workflows

## Project status

Noteeli is an actively evolving project.

The current repository contains the core application built with:

- FastAPI
- Mako templates
- SQLite for app preferences

Project architecture and conventions are described in [ARCHITECTURE.md](./ARCHITECTURE.md).

## License

This project is licensed under `AGPL-3.0-or-later`.

That license fits a web-based product that can be both self-hosted and used as a network service. See [LICENSE](./LICENSE) for the full text.

## Contributing

Issues, suggestions, and contributions are welcome.

Before making larger changes, it is best to open an issue or start a discussion so the direction stays aligned with the product and architecture.

## Installation

### Requirements

- Python 3.11+

### Environment variables

Copy `.env.example` to `.env` and configure the values you need.

Main variables:

- `NOTEELI_CONTENT_ROOT` - base directory for notes
- `NOTEELI_DATA_DIR` - directory for SQLite and app data
- `NOTEELI_SESSION_SECRET` - session secret
- `NOTEELI_GOOGLE_CLIENT_ID` - Google OAuth client ID
- `NOTEELI_GOOGLE_CLIENT_SECRET` - Google OAuth client secret

### Clone

```bash
git clone https://github.com/marszalik/noteeli.git
cd noteeli
```

### Install venv

```bash
python3 -m venv .venv
source .venv/bin/activate
./.venv/bin/pip install -e ".[dev]"
```

### Install with PDM

```bash
pdm install
```

### Set credentials

```bash
cp .env.example .env
nano .env
```

### Run with PDM

```bash
pdm run dev
```

Then open:

```text
http://127.0.0.1:8000
```

`pdm run dev` starts with `reload` enabled and picks the first free port starting from `8000`.

Production mode with PDM:

```bash
pdm run prod
```

Or on a specific port:

```bash
pdm run prod --port 9000
```
