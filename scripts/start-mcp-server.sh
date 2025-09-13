#!/bin/bash
# Start the MCP Summary Server
# This script starts the native MCP server for stdio communication

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Starting MCP Summary Server..."
echo "Project root: $PROJECT_ROOT"

# Activate virtual environment if it exists
if [ -f "$PROJECT_ROOT/venv/bin/activate" ]; then
    echo "Activating virtual environment..."
    source "$PROJECT_ROOT/venv/bin/activate"
fi

# Change to project root and start the MCP server
cd "$PROJECT_ROOT"
python src/mcp_summary_server.py
