#!/bin/bash
# Start the MCP HTTP Bridge
# This script starts the HTTP REST API bridge for MCP functionality

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Default configuration
MCP_HTTP_PORT=${MCP_HTTP_PORT:-3000}

echo "Starting MCP HTTP Bridge..."
echo "Port: $MCP_HTTP_PORT"
echo "Project root: $PROJECT_ROOT"

# Activate virtual environment if it exists
if [ -f "$PROJECT_ROOT/venv/bin/activate" ]; then
    echo "Activating virtual environment..."
    source "$PROJECT_ROOT/venv/bin/activate"
fi

# Change to project root and start the HTTP bridge
cd "$PROJECT_ROOT"
python src/mcp_http_bridge.py --port $MCP_HTTP_PORT
