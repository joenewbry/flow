#!/bin/bash
# Flow MCP Server Startup Script

cd "$(dirname "$0")"

# Activate virtual environment
source .venv/bin/activate

# Start the MCP server
echo "Starting Flow MCP Server..."
python server.py
