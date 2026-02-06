#!/usr/bin/env sh
#
# Memex (Flow) easy install — one command, no virtual env setup.
# Usage: curl -fsSL https://raw.githubusercontent.com/joenewbry/flow/main/install.sh | sh
#
# Installs to ~/.memex and adds a `memex` command. Add ~/.local/bin to your PATH
# if needed, then run: memex start
#

set -e

MEMEX_HOME="${MEMEX_HOME:-$HOME/.memex}"
BIN_DIR="${HOME}/.local/bin"
REPO_URL="${MEMEX_REPO_URL:-https://github.com/joenewbry/flow.git}"
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

# Detect if we're running from inside the repo (e.g. development)
in_repo() {
  [ -d "refinery" ] && [ -d "mcp-server" ] && [ -f "refinery/flow-requirements.txt" ] && [ -f "mcp-server/requirements.txt" ]
}

# Install from current directory
install_from_cwd() {
  log_info "Installing from current directory into ${MEMEX_HOME}"
  mkdir -p "$MEMEX_HOME"
  cp -R refinery mcp-server "$MEMEX_HOME/"
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
    (cd "$tmpdir" && curl -sL "https://github.com/joenewbry/flow/tarball/${BRANCH}" -o flow.tar.gz && tar xzf flow.tar.gz)
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
  cp -R "$tmpdir/repo/refinery" "$tmpdir/repo/mcp-server" "$MEMEX_HOME/"
}

# Create single venv and install dependencies
setup_venv() {
  log_info "Creating environment (one-time setup)..."
  python3 -m venv "$MEMEX_HOME/.venv"
  # shellcheck disable=SC1090
  . "$MEMEX_HOME/.venv/bin/activate"
  pip install -q --upgrade pip
  pip install -q -r "$MEMEX_HOME/refinery/flow-requirements.txt"
  if pip install -q -r "$MEMEX_HOME/mcp-server/requirements.txt" 2>/dev/null; then
    log_ok "Dependencies installed (refinery + MCP server)"
  else
    log_warn "MCP server deps failed (optional). Memex start will work; for Claude add MCP deps later."
    log_ok "Refinery dependencies installed"
  fi
}

# Write the memex launcher script
write_memex_script() {
  mkdir -p "$MEMEX_HOME/bin" "$BIN_DIR"
  cat > "$MEMEX_HOME/bin/memex" << 'MEMEX_SCRIPT'
#!/usr/bin/env sh
# Memex launcher - start/stop screen capture and ChromaDB

MEMEX_HOME="${MEMEX_HOME:-$HOME/.memex}"
VENV_PYTHON="$MEMEX_HOME/.venv/bin/python"
VENV_BIN="$MEMEX_HOME/.venv/bin"
PID_DIR="$MEMEX_HOME/var"
mkdir -p "$MEMEX_HOME/logs" "$PID_DIR"

start_chroma() {
  if [ -f "$PID_DIR/chroma.pid" ] && kill -0 "$(cat "$PID_DIR/chroma.pid")" 2>/dev/null; then
    echo "ChromaDB already running"
    return 0
  fi
  nohup "$VENV_BIN/chroma" run --host localhost --port 8000 >> "$MEMEX_HOME/logs/chroma.log" 2>&1 &
  echo $! > "$PID_DIR/chroma.pid"
  echo "ChromaDB started (port 8000)"
  sleep 2
}

stop_chroma() {
  if [ -f "$PID_DIR/chroma.pid" ]; then
    pid=$(cat "$PID_DIR/chroma.pid")
    kill "$pid" 2>/dev/null && echo "ChromaDB stopped" || true
    rm -f "$PID_DIR/chroma.pid"
  fi
}

start_capture() {
  if [ -f "$PID_DIR/capture.pid" ] && kill -0 "$(cat "$PID_DIR/capture.pid")" 2>/dev/null; then
    echo "Screen capture already running"
    return 0
  fi
  cd "$MEMEX_HOME/refinery" && nohup "$VENV_PYTHON" run.py >> "$MEMEX_HOME/logs/capture.log" 2>&1 &
  echo $! > "$PID_DIR/capture.pid"
  echo "Screen capture started"
}

stop_capture() {
  if [ -f "$PID_DIR/capture.pid" ]; then
    pid=$(cat "$PID_DIR/capture.pid")
    kill "$pid" 2>/dev/null && echo "Screen capture stopped" || true
    rm -f "$PID_DIR/capture.pid"
  fi
}

case "${1:-}" in
  start)
    start_chroma
    start_capture
    echo ""
    echo "Memex is running. Use 'memex stop' to stop."
    ;;
  stop)
    stop_capture
    stop_chroma
    ;;
  status)
    running=0
    if [ -f "$PID_DIR/chroma.pid" ] && kill -0 "$(cat "$PID_DIR/chroma.pid")" 2>/dev/null; then
      echo "ChromaDB: running"
      running=1
    else
      echo "ChromaDB: stopped"
    fi
    if [ -f "$PID_DIR/capture.pid" ] && kill -0 "$(cat "$PID_DIR/capture.pid")" 2>/dev/null; then
      echo "Screen capture: running"
      running=1
    else
      echo "Screen capture: stopped"
    fi
    [ $running -eq 0 ] && exit 1
    ;;
  *)
    echo "Usage: memex {start|stop|status}"
    exit 1
    ;;
esac
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

  if ! command -v python3 >/dev/null 2>&1; then
    log_err "python3 not found. Please install Python 3.10+ and try again."
    exit 1
  fi

  if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
    pyver=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || echo "?")
    log_err "Python 3.10+ required; found $pyver."
    exit 1
  fi

  if in_repo; then
    install_from_cwd
  else
    install_from_repo
  fi

  if [ ! -d "$MEMEX_HOME/.venv" ]; then
    setup_venv
  else
    log_info "Using existing environment at $MEMEX_HOME/.venv"
  fi

  write_memex_script

  echo ""
  log_ok "Installation complete."
  echo ""
  echo "Add memex to your shell (if not already on PATH):"
  echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
  echo ""
  echo "Then run:"
  echo "  memex start"
  echo ""
}

main "$@"
