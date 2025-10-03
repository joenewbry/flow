#!/bin/bash

# Start the MCP server with logging
# Stderr goes to log file, stdout stays for MCP protocol

LOG_DIR="/Users/joe/dev/flow/mcp-flow-node/logs"
mkdir -p "$LOG_DIR"

LOG_FILE="$LOG_DIR/mcp-flow-$(date +%Y%m%d-%H%M%S).log"

echo "Starting Flow MCP Server with logging to: $LOG_FILE"
node server.js 2>"$LOG_FILE"
