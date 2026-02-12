#!/bin/bash
# Memex Prometheus Setup Script
# Run this on the Jetson Orin Nano to set up the entire system.
#
# Usage: sudo bash /ssd/memex/scripts/setup.sh
set -euo pipefail

echo "=== Memex Prometheus Setup ==="
echo ""

MEMEX_DIR="/ssd/memex"
USER="prometheus"

# Check we're on the Jetson
if [ ! -d "/ssd" ]; then
    echo "ERROR: /ssd directory not found. Is this the Jetson?"
    exit 1
fi

# Create directory structure
echo "1. Creating directory structure..."
mkdir -p "$MEMEX_DIR"/{config,server/tools,sync,scripts,systemd,docs,logs}
mkdir -p "$MEMEX_DIR"/data/{personal,walmart,alaska}/ocr
mkdir -p "$MEMEX_DIR"/chroma
echo "   Done."

# Install system packages
echo ""
echo "2. Installing system packages..."
apt-get update -qq
apt-get install -y -qq python3-pip python3-venv rsync curl
echo "   Done."

# Create virtual environment
echo ""
echo "3. Setting up Python virtual environment..."
if [ ! -d "$MEMEX_DIR/.venv" ]; then
    python3 -m venv "$MEMEX_DIR/.venv"
fi
source "$MEMEX_DIR/.venv/bin/activate"
pip install --quiet -r "$MEMEX_DIR/requirements.txt"
echo "   Done."

# Check Ollama
echo ""
echo "4. Checking Ollama..."
if command -v ollama &>/dev/null; then
    echo "   Ollama found."
    if ! ollama list 2>/dev/null | grep -q "llama3.2:1b"; then
        echo "   Pulling llama3.2:1b model..."
        ollama pull llama3.2:1b
    else
        echo "   llama3.2:1b model already available."
    fi
else
    echo "   Ollama not found. Install it with:"
    echo "   curl -fsSL https://ollama.com/install.sh | sh"
    echo "   Then run: ollama pull llama3.2:1b"
fi

# Set up SSH key auth directory
echo ""
echo "5. SSH key setup..."
PROMETHEUS_HOME=$(eval echo ~$USER 2>/dev/null || echo "/home/$USER")
if [ -d "$PROMETHEUS_HOME" ]; then
    mkdir -p "$PROMETHEUS_HOME/.ssh"
    chmod 700 "$PROMETHEUS_HOME/.ssh"
    touch "$PROMETHEUS_HOME/.ssh/authorized_keys"
    chmod 600 "$PROMETHEUS_HOME/.ssh/authorized_keys"
    echo "   SSH directory ready at $PROMETHEUS_HOME/.ssh/"
    echo "   Add your laptop's public key to authorized_keys."
else
    echo "   User $USER home directory not found. Create the user or adjust SSH config."
fi

# Install systemd services
echo ""
echo "6. Installing systemd services..."
if [ -f "$MEMEX_DIR/systemd/memex-chromadb.service" ]; then
    cp "$MEMEX_DIR/systemd/memex-chromadb.service" /etc/systemd/system/
    cp "$MEMEX_DIR/systemd/memex-server.service" /etc/systemd/system/
    systemctl daemon-reload
    echo "   Services installed. Enable with:"
    echo "     sudo systemctl enable memex-chromadb memex-server"
    echo "     sudo systemctl start memex-chromadb memex-server"
else
    echo "   Systemd unit files not found in $MEMEX_DIR/systemd/"
fi

# Set permissions
echo ""
echo "7. Setting permissions..."
if id "$USER" &>/dev/null; then
    chown -R "$USER:$USER" "$MEMEX_DIR"
    echo "   Ownership set to $USER."
else
    echo "   User $USER not found. Set permissions manually."
fi

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "  1. Add SSH public keys to $PROMETHEUS_HOME/.ssh/authorized_keys"
echo "  2. Edit $MEMEX_DIR/config/api_keys.env with your API keys"
echo "  3. Run initial sync from your laptop: ~/bin/memex-sync.sh"
echo "  4. Start ChromaDB: sudo systemctl start memex-chromadb"
echo "  5. Run initial index: $MEMEX_DIR/.venv/bin/python $MEMEX_DIR/sync/reindex.py --instance personal"
echo "  6. Start server: sudo systemctl start memex-server"
echo "  7. Set up Cloudflare tunnel (see docs/multi-peer-architecture.md)"
echo ""
