#!/usr/bin/env sh
#
# Memex (Flow) easy install — one command, no virtual env setup.
# Usage: curl -fsSL https://raw.githubusercontent.com/joenewbry/memex/main/install.sh | sh
#
# Installs to ~/.memex and adds a `memex` command. Add ~/.local/bin to your PATH
# if needed, then run: memex start
#

set -e

MEMEX_HOME="${MEMEX_HOME:-$HOME/.memex}"
BIN_DIR="${HOME}/.local/bin"
REPO_URL="${MEMEX_REPO_URL:-https://github.com/joenewbry/memex.git}"
BRANCH="${MEMEX_BRANCH:-main}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo "${BLUE}→${NC} $1"; }
log_ok()   { echo "${GREEN}✓${NC} $1"; }
log_warn() { echo "${YELLOW}⚠${NC} $1"; }
log_err()  { echo "${RED}✗${NC} $1"; }

# Find a Python 3.10+ executable (prefer 3.12, 3.11, 3.10 over default python3)
find_python() {
  for cmd in python3.12 python3.11 python3.10 python3; do
    if command -v "$cmd" >/dev/null 2>&1; then
      if "$cmd" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
        echo "$cmd"
        return 0
      fi
    fi
  done
  return 1
}

# Detect if we're running from inside the repo (e.g. development)
in_repo() {
  [ -d "refinery" ] && [ -d "mcp-server" ] && [ -d "cli" ] && [ -f "refinery/flow-requirements.txt" ] && [ -f "mcp-server/requirements.txt" ]
}

# Install from current directory
install_from_cwd() {
  log_info "Installing from current directory into ${MEMEX_HOME}"
  mkdir -p "$MEMEX_HOME"
  cp -R refinery mcp-server cli "$MEMEX_HOME/"
  [ -f "setup.sh" ] && cp setup.sh "$MEMEX_HOME/" || true
}

# Install by cloning repo
install_from_repo() {
  log_info "Downloading Memex (Flow) from ${REPO_URL}..."
  tmpdir=$(mktemp -d 2>/dev/null || mktemp -d -t memex)
  trap 'rm -rf "$tmpdir"' EXIT

  if command -v git >/dev/null 2>&1; then
    git clone --depth 1 --branch "$BRANCH" "$REPO_URL" "$tmpdir/repo"
  else
    log_info "Git not found, downloading tarball..."
    (cd "$tmpdir" && curl -sL "https://github.com/joenewbry/memex/tarball/${BRANCH}" -o flow.tar.gz && tar xzf flow.tar.gz)
    # GitHub tarball extracts to owner-repo-commitHash/
    repodir=$(find "$tmpdir" -maxdepth 1 -type d -name '*-flow-*' | head -1)
    if [ -n "$repodir" ] && [ -d "$repodir/refinery" ]; then
      mv "$repodir" "$tmpdir/repo"
    else
      log_err "Download or extract failed"
      exit 1
    fi
  fi

  log_info "Copying files to ${MEMEX_HOME}"
  mkdir -p "$MEMEX_HOME"
  cp -R "$tmpdir/repo/refinery" "$tmpdir/repo/mcp-server" "$tmpdir/repo/cli" "$MEMEX_HOME/"
}

# Create single venv and install dependencies
setup_venv() {
  log_info "Creating environment (one-time setup)..."
  "${PYTHON:-python3}" -m venv "$MEMEX_HOME/.venv"
  # shellcheck disable=SC1090
  . "$MEMEX_HOME/.venv/bin/activate"
  pip install -q --upgrade pip
  pip install -q -r "$MEMEX_HOME/refinery/flow-requirements.txt"
  pip install -q -r "$MEMEX_HOME/cli/requirements.txt"
  if pip install -q -r "$MEMEX_HOME/mcp-server/requirements.txt" 2>/dev/null; then
    log_ok "Dependencies installed (refinery + CLI + MCP server)"
  else
    log_warn "MCP server deps failed (optional). memex start/chat will work; for Claude add MCP deps later."
    log_ok "Refinery + CLI dependencies installed"
  fi
}

# Write the memex launcher script (invokes full Python CLI)
write_memex_script() {
  mkdir -p "$MEMEX_HOME/bin" "$BIN_DIR"
  cat > "$MEMEX_HOME/bin/memex" << MEMEX_SCRIPT
#!/usr/bin/env sh
# Memex launcher - full CLI (chat, start, status, doctor, etc.)

MEMEX_HOME="\${MEMEX_HOME:-\$HOME/.memex}"
export PYTHONPATH="\$MEMEX_HOME:\$PYTHONPATH"
exec "\$MEMEX_HOME/.venv/bin/python" -m cli.main "\$@"
MEMEX_SCRIPT
  chmod +x "$MEMEX_HOME/bin/memex"

  # Symlink or copy into ~/.local/bin so user can run `memex` after adding to PATH
  if [ -w "$BIN_DIR" ] 2>/dev/null; then
    ln -sf "$MEMEX_HOME/bin/memex" "$BIN_DIR/memex"
    log_ok "memex command installed to $BIN_DIR"
  else
    log_warn "Could not write to $BIN_DIR (run: mkdir -p $BIN_DIR and ensure it is on your PATH)"
  fi
}

# Main
main() {
  echo ""
  echo "Memex (Flow) — easy install"
  echo ""

  PYTHON=$(find_python) || true
  if [ -z "$PYTHON" ]; then
    log_err "Python 3.10+ required but not found."
    echo ""
    echo "Install a newer Python, then re-run this script. Examples:"
    echo "  macOS (Homebrew):  brew install python@3.12"
    echo "  Then run:          curl -fsSL https://raw.githubusercontent.com/joenewbry/memex/main/install.sh | sh"
    exit 1
  fi
  log_info "Using $PYTHON"

  if in_repo; then
    install_from_cwd
  else
    install_from_repo
  fi

  if [ ! -d "$MEMEX_HOME/.venv" ]; then
    setup_venv
  else
    log_info "Using existing environment at $MEMEX_HOME/.venv"
    # Ensure deps are present (refinery=chromadb, cli, mcp-server)
    # shellcheck disable=SC1090
    . "$MEMEX_HOME/.venv/bin/activate"
    pip install -q -r "$MEMEX_HOME/refinery/flow-requirements.txt" 2>/dev/null || true
    pip install -q -r "$MEMEX_HOME/cli/requirements.txt" 2>/dev/null || true
    pip install -q -r "$MEMEX_HOME/mcp-server/requirements.txt" 2>/dev/null || true
  fi

  write_memex_script

  echo ""
  log_ok "Installation complete."
  echo ""
  echo "Add memex to your shell (if not already on PATH):"
  echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
  echo ""
  echo "Then run:"
  echo "  memex start      # Start capture (and optionally MCP server)"
  echo "  memex chat       # Chat with Memex"
  echo "  memex help       # See all commands"
  echo ""
}

main "$@"
