# Flow MCP

[![GitHub stars](https://img.shields.io/github/stars/yourusername/flow.svg?style=social&label=Star)](https://github.com/yourusername/flow)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://python.org)


## Installation

### Prerequisites
- **Python 3.10+** (tested with Python 3.13.7)
- **Node.js 16+** (for MCP server)
- **Tesseract OCR** (install via system package manager)
- **ChromaDB server** (running on localhost:8000)
- **Screen capture permissions** (macOS: System Preferences > Security & Privacy > Privacy > Screen Recording)

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/flow.git
   cd flow
   ```

2. **Set up Python environment for screen tracking**
   ```bash
   cd refinery
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r flow-requirements.txt
   cd ..
   ```

3. **Set up MCP server environment**
   ```bash
   cd mcp-flow-node
   npm install
   cd ..
   ```

4. **Start ChromaDB server in /refinery folder** (in a separate terminal)
   ```bash
   cd refinery && chroma run --host localhost --port 8000
   ```

5. **Run the Flow tracker**
   ```bash
   cd refinery
   python run.py
   ```

### Claude Desktop MCP Configuration

To integrate Flow with Claude Desktop, add the following configuration to your Claude Desktop config file:

```json
{
  "mcpServers": {
    "flow": {
      "command": "node",
      "args": [
        "/Users/joe/dev/flow/mcp-flow-node/server.js"
      ],
      "cwd": "/Users/joe/dev/flow"
    }
  }
}
```

For detailed MCP setup instructions, see the [Claude Desktop MCP guide](https://modelcontextprotocol.io/docs/develop/connect-local-servers).

## Architecture Guide

```
Flow System
├── refinery/run.py (Screenshot Capture & OCR)
├── ChromaDB Server (Vector Storage)
├── mcp-flow-node/server.js (MCP Interface)
└── Claude Desktop (Search Interface)
```

**Screen Tracking Process:**
- Flow automatically detects all available monitors/displays
- Screen naming convention: `screen_0` (primary), `screen_1` (secondary), `screen_N` (additional)
- Screenshots captured every 60 seconds by default
- OCR text extraction via Tesseract happens in background threads
- Data stored as `{timestamp}_{screen_name}.json` files

**ChromaDB Integration:**
- All OCR text content stored in "screenshots" collection
- Semantic embeddings enable intelligent search across captured content
- Both new captures and existing OCR files are automatically indexed
- HTTP client connects to ChromaDB server on localhost:8000

**MCP Server Features:**
- Provides `search-screenshots` tool for semantic text search
- Supports date range filtering and result limiting
- Integrates with Claude Desktop for natural language queries
- Returns relevant screen content with metadata and similarity scores

**Data Flow:**
1. Screenshots captured → OCR processed → JSON saved → ChromaDB indexed
2. Claude queries → MCP server → ChromaDB search → Results returned
3. All processing happens automatically in the background

---

⭐ **Star this repository** if you find it helpful!