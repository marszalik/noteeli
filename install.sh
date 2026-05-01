#!/usr/bin/env bash
#
# Noteeli installer — one-line setup for Linux & macOS.
#
#   curl -fsSL https://noteeli.com/install.sh | bash
#
# or, straight from GitHub:
#
#   curl -fsSL https://raw.githubusercontent.com/marszalik/noteeli/main/install.sh | bash
#
# Env overrides:
#   NOTEELI_DIR        Install directory     (default: ~/.noteeli)
#   NOTEELI_NOTES_DIR  Notes content root    (default: ~/notes)
#   NOTEELI_BRANCH     Git branch / tag      (default: main)
#
set -euo pipefail

REPO_URL="https://github.com/marszalik/noteeli.git"
BRANCH="${NOTEELI_BRANCH:-main}"
INSTALL_DIR="${NOTEELI_DIR:-$HOME/.noteeli}"
NOTES_DIR="${NOTEELI_NOTES_DIR:-$HOME/notes}"
LAUNCHER_DIR="$HOME/.local/bin"
LAUNCHER_PATH="$LAUNCHER_DIR/noteeli"

# Colours when stdout is a TTY, plain text otherwise.
if [[ -t 1 ]]; then
  RED=$'\033[0;31m'; GREEN=$'\033[0;32m'; YELLOW=$'\033[1;33m'
  CYAN=$'\033[0;36m'; BOLD=$'\033[1m'; RESET=$'\033[0m'
else
  RED=; GREEN=; YELLOW=; CYAN=; BOLD=; RESET=
fi

step() { printf '\n%s==>%s %s\n' "$CYAN$BOLD" "$RESET" "$*"; }
ok()   { printf '%s✓%s %s\n'  "$GREEN" "$RESET" "$*"; }
warn() { printf '%s!%s %s\n'  "$YELLOW" "$RESET" "$*"; }
fail() { printf '%s✗ %s%s\n' "$RED" "$*" "$RESET" >&2; exit 1; }

banner() {
  printf '%s' "$CYAN$BOLD"
  cat <<'EOF'
   _   _       _              _ _
  | \ | |     | |            | (_)
  |  \| | ___ | |_ ___  ___  | |_
  | . ` |/ _ \| __/ _ \/ _ \ | | |
  | |\  | (_) | ||  __/  __/ | | |
  |_| \_|\___/ \__\___|\___|_|_|_|
EOF
  printf '%s\n' "$RESET"
}

# ── 1. Prerequisites ─────────────────────────────────────────────
banner
step "Checking prerequisites"

PYTHON_BIN=""
for cmd in python3.13 python3.12 python3.11 python3; do
  if command -v "$cmd" >/dev/null 2>&1 && \
     "$cmd" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' 2>/dev/null; then
    PYTHON_BIN="$cmd"
    break
  fi
done
[[ -n "$PYTHON_BIN" ]] || fail "Python 3.11+ is required. Install python3.11 (or newer) and re-run."
ok "Python: $($PYTHON_BIN --version)"

command -v git >/dev/null 2>&1 || fail "git is required. Install it and re-run."
ok "git:    $(git --version | awk '{print $3}')"

# venv module ships with python on most distros, but not all (Debian/Ubuntu split it out).
"$PYTHON_BIN" -c 'import venv' 2>/dev/null \
  || fail "Python venv module missing. On Debian/Ubuntu run: sudo apt install python3-venv"

# ── 2. Source ────────────────────────────────────────────────────
step "Fetching source into $INSTALL_DIR"

if [[ -d "$INSTALL_DIR/.git" ]]; then
  ok "Existing checkout found, updating"
  git -C "$INSTALL_DIR" fetch --quiet origin "$BRANCH"
  git -C "$INSTALL_DIR" checkout --quiet "$BRANCH"
  git -C "$INSTALL_DIR" pull --ff-only --quiet
else
  mkdir -p "$(dirname "$INSTALL_DIR")"
  git clone --quiet --branch "$BRANCH" "$REPO_URL" "$INSTALL_DIR"
fi
ok "Source ready"

cd "$INSTALL_DIR"

# ── 3. Virtualenv & dependencies ─────────────────────────────────
step "Setting up virtual environment"

[[ -d .venv ]] || "$PYTHON_BIN" -m venv .venv
.venv/bin/pip install --quiet --upgrade pip

# Read the dependency list straight out of pyproject.toml so the installer
# stays in sync with the project without us maintaining a second list.
DEPS=$(.venv/bin/python - <<'PY'
import sys, tomllib
with open('pyproject.toml', 'rb') as f:
    project = tomllib.load(f)['project']
sys.stdout.write(' '.join(project['dependencies']))
PY
)
# shellcheck disable=SC2086
.venv/bin/pip install --quiet $DEPS
ok "Dependencies installed"

# ── 4. Configuration ─────────────────────────────────────────────
step "Configuring environment"

mkdir -p "$NOTES_DIR" "$INSTALL_DIR/data"

if [[ ! -f .env ]]; then
  SECRET=$("$PYTHON_BIN" -c 'import secrets; print(secrets.token_urlsafe(48))')
  cat > .env <<EOF
NOTEELI_CONTENT_ROOT=$NOTES_DIR
NOTEELI_DATA_DIR=$INSTALL_DIR/data
NOTEELI_SESSION_SECRET=$SECRET

# Google OAuth — leave blank to use built-in password login below.
NOTEELI_GOOGLE_CLIENT_ID=
NOTEELI_GOOGLE_CLIENT_SECRET=
NOTEELI_ALLOWED_GOOGLE_EMAILS=

# Built-in password login — change before exposing to the network.
NOTEELI_LOCAL_USERNAME=admin
NOTEELI_LOCAL_PASSWORD=changeme
EOF
  ok "Wrote .env (notes: $NOTES_DIR)"
else
  ok ".env already exists; left untouched"
fi

# ── 5. Launcher ──────────────────────────────────────────────────
step "Installing 'noteeli' launcher"

mkdir -p "$LAUNCHER_DIR"
cat > "$LAUNCHER_PATH" <<EOF
#!/usr/bin/env bash
cd "$INSTALL_DIR"
exec "$INSTALL_DIR/.venv/bin/python" -m app.run "\${1:-dev}" "\${@:2}"
EOF
chmod +x "$LAUNCHER_PATH"
ok "Installed: $LAUNCHER_PATH"

case ":$PATH:" in
  *":$LAUNCHER_DIR:"*) ;;
  *)
    warn "$LAUNCHER_DIR is not on your PATH."
    echo "    Add this to ~/.bashrc or ~/.zshrc:"
    echo "      ${BOLD}export PATH=\"$LAUNCHER_DIR:\$PATH\"${RESET}"
    ;;
esac

# ── 6. Done ──────────────────────────────────────────────────────
printf '\n%sNoteeli is installed.%s\n\n' "$GREEN$BOLD" "$RESET"
echo "Run it:"
echo "  ${BOLD}noteeli${RESET}                  # dev mode, auto-reload"
echo "  ${BOLD}noteeli prod${RESET}             # production"
echo "  ${BOLD}noteeli prod --port 9000${RESET} # specific port"
echo
echo "Notes:  $NOTES_DIR"
echo "Config: $INSTALL_DIR/.env  (edit credentials before exposing externally)"
echo "Data:   $INSTALL_DIR/data"
echo
echo "Re-running this installer at any time will fast-forward the source"
echo "and refresh dependencies — your .env and notes are left untouched."
