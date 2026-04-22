# Noteeli

Noteeli is a Markdown-first web workspace built around real folders, plain files, and storage you control.

It is designed for people who want an Obsidian-like workflow in the browser without moving their notes into a proprietary format or storage model.

Website: [noteeli.com](https://noteeli.com)

![Noteeli](https://noteeli.com/og-image.png)

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

### clone
Clone repo to your folder

```bash
git clone https://github.com/marszalik/noteeli.git
```

### Install venv

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Install with PDM

```bash
pdm install
```


### set credencials

its enough to set some login and password

```bash
cp .env.example .env

nano .env
```



### run with PDM

```bash
pdm run dev
```

Then open:

```text
http://127.0.0.1:8000
```
