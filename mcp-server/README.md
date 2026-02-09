# Memex MCP Server

A standalone Python implementation of the Memex MCP (Model Context Protocol) server, replacing the previous Node.js version.

## Features

- **Standalone Operation**: Runs independently of Claude Desktop
- **Complete Tool Set**: All original MCP tools ported to Python
- **Enhanced Performance**: Direct integration with OCR data processing
- **Better Error Handling**: Comprehensive logging and error recovery
- **Unified Codebase**: All Python, easier maintenance

## Available Tools

### Search Tools
- `search-screenshots` - Search OCR data from screenshots with date filtering
- `what-can-i-do` - Get information about Memex capabilities

### Analytics Tools  
- `get-stats` - Get comprehensive system and data statistics
- `activity-graph` - Generate activity timeline visualizations
- `time-range-summary` - Get sampled data over specific time ranges

### System Control Tools
- `start-memex` - Start Memex system (ChromaDB + screen capture)
- `stop-memex` - Stop Memex system

## Installation

**Modern uv-based setup (Recommended):**
1. **Install uv** (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Install dependencies**:
   ```bash
   cd mcp-server
   uv sync
   ```

3. **Test the server**:
   ```bash
   uv run server.py
   ```

**Alternative pip-based setup:**
1. **Set up virtual environment**:
   ```bash
   cd mcp-server
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Test the server**:
   ```bash
   python server.py --help
   ```

## Usage

### Standalone Mode
Run the MCP server independently:
```bash
./start.sh
```

### Claude Desktop Integration

**Modern uv-based configuration (Recommended):**
```json
{
  "mcpServers": {
    "memex": {
      "command": "/Users/joe/.local/bin/uv",
      "args": [
        "--directory",
        "/Users/joe/dev/memex/mcp-server",
        "run",
        "server.py"
      ]
    }
  }
}
```

**Alternative configurations:**

Using the startup script:
```json
{
  "mcpServers": {
    "memex": {
      "command": "/Users/joe/dev/memex/mcp-server/start.sh"
    }
  }
}
```

Direct Python execution:
```json
{
  "mcpServers": {
    "memex": {
      "command": "python",
      "args": ["/Users/joe/dev/memex/mcp-server/server.py"],
      "cwd": "/Users/joe/dev/memex/mcp-server"
    }
  }
}
```

## Architecture

```
mcp-server/
├── server.py              # Main MCP server
├── start.sh               # Startup script
├── requirements.txt       # Dependencies
└── tools/                 # Tool implementations
    ├── search.py          # Search functionality
    ├── stats.py           # Statistics and system info
    ├── activity.py        # Activity graphs and summaries
    └── system.py          # System control and info
```

## Tool Details

### search-screenshots
Search through OCR data with optional date filtering.

**Parameters**:
- `query` (required): Search text
- `start_date` (optional): Start date (YYYY-MM-DD)
- `end_date` (optional): End date (YYYY-MM-DD)  
- `limit` (optional): Max results (default: 10)

### get-stats
Get comprehensive statistics about the Memex system.

**Returns**: File counts, date ranges, screen info, activity metrics

### activity-graph
Generate activity timeline data for visualization.

**Parameters**:
- `days` (optional): Number of days (default: 7)
- `grouping` (optional): "hourly" or "daily" (default: "hourly")
- `include_empty` (optional): Include empty periods (default: true)

### start-memex / stop-memex
Control the Memex system processes.

**Returns**: Operation status and process information

## Logging

The server logs to stderr with structured logging:
- INFO: General operations
- ERROR: Error conditions
- DEBUG: Detailed debugging (set MEMEX_DEBUG=1)

## Error Handling

- Graceful degradation when components fail
- Detailed error messages with context
- Automatic recovery for transient issues
- Comprehensive validation of inputs

## Migration from Node.js

This Python server replaces the previous Node.js implementation with:

1. **Better Performance**: Direct Python integration
2. **Enhanced Features**: More detailed error handling
3. **Unified Codebase**: All Python components
4. **Improved Reliability**: Better process management

## Development

To extend the server:

1. Add new tools in the `tools/` directory
2. Register tools in `server.py`
3. Update the tool list in `list_tools()`
4. Add corresponding `call_tool()` handlers

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure virtual environment is activated
2. **Permission Errors**: Check file permissions on startup script
3. **OCR Data Access**: Verify `refinery/data/ocr/` directory exists
4. **ChromaDB Connection**: Ensure ChromaDB server is accessible

### Debug Mode
Set environment variable for detailed logging:
```bash
export MEMEX_DEBUG=1
python server.py
```
