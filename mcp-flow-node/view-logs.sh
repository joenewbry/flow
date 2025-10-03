#!/bin/bash

# Flow MCP Server Log Viewer
LOG_DIR="$HOME/Library/Logs/Claude"

show_help() {
    echo "Flow MCP Server Log Viewer"
    echo ""
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  -t, --tail [N]    Show last N lines and follow (default: 50)"
    echo "  -e, --errors      Show only error messages"
    echo "  -s, --search TEXT Search for specific text in logs"
    echo "  -l, --list        List all available log files"
    echo "  -h, --help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 -t 20          Show last 20 lines and follow"
    echo "  $0 -e             Show only errors"
    echo "  $0 -s \"ChromaDB\"   Search for ChromaDB mentions"
}

list_logs() {
    echo "Available MCP log files:"
    ls -la "$LOG_DIR"/mcp*.log 2>/dev/null | while read -r line; do
        echo "  $line"
    done
}

show_errors() {
    echo "🚨 Recent errors from Flow MCP server:"
    grep -i "error\|failed\|exception" "$LOG_DIR/mcp-server-flow.log" 2>/dev/null | tail -20
}

search_logs() {
    local search_term="$1"
    echo "🔍 Searching for '$search_term' in Flow MCP logs:"
    grep -i "$search_term" "$LOG_DIR/mcp-server-flow.log" 2>/dev/null | tail -20
}

tail_logs() {
    local lines="${1:-50}"
    echo "📋 Last $lines lines from Flow MCP server (following):"
    echo "Press Ctrl+C to stop"
    echo ""
    tail -n "$lines" -f "$LOG_DIR/mcp-server-flow.log" 2>/dev/null
}

# Parse command line arguments
case "${1:-}" in
    -h|--help)
        show_help
        ;;
    -l|--list)
        list_logs
        ;;
    -e|--errors)
        show_errors
        ;;
    -s|--search)
        if [ -z "$2" ]; then
            echo "Error: Search term required"
            show_help
            exit 1
        fi
        search_logs "$2"
        ;;
    -t|--tail)
        tail_logs "$2"
        ;;
    "")
        tail_logs 50
        ;;
    *)
        echo "Unknown option: $1"
        show_help
        exit 1
        ;;
esac
