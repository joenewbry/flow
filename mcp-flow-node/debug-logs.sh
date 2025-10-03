#!/bin/bash

# Debug script for Flow MCP Server logs
echo "🔍 Monitoring Flow MCP Server logs in real-time..."
echo "Press Ctrl+C to stop monitoring"
echo ""

# Monitor multiple log files simultaneously
tail -f \
  ~/Library/Logs/Claude/mcp-server-flow.log \
  ~/Library/Logs/Claude/mcp.log \
  2>/dev/null | while read line; do
    # Add timestamp and color coding
    timestamp=$(date '+%H:%M:%S')
    if [[ $line == *"ERROR"* || $line == *"Error"* ]]; then
        echo -e "\033[31m[$timestamp] 🚨 $line\033[0m"  # Red for errors
    elif [[ $line == *"WARN"* || $line == *"warn"* ]]; then
        echo -e "\033[33m[$timestamp] ⚠️  $line\033[0m"   # Yellow for warnings
    elif [[ $line == *"INFO"* || $line == *"info"* ]]; then
        echo -e "\033[32m[$timestamp] ℹ️  $line\033[0m"   # Green for info
    else
        echo -e "\033[37m[$timestamp] 📝 $line\033[0m"    # Gray for other
    fi
done
