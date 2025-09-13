#!/bin/bash
# Start the Flow MCP Server
# This script starts the native MCP server for stdio communication

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Starting Flow MCP Server..."
echo "Project root: $PROJECT_ROOT"

# Activate virtual environment if it exists
if [ -f "$PROJECT_ROOT/mcp-flow/.venv/bin/activate" ]; then
    echo "Activating MCP virtual environment..."
    source "$PROJECT_ROOT/mcp-flow/.venv/bin/activate"
fi

# Change to mcp-flow directory and start the MCP server
cd "$PROJECT_ROOT/mcp-flow"
python flow_mcp_server.py
