# Flow CLI

[![GitHub stars](https://img.shields.io/github/stars/yourusername/flow.svg?style=social&label=Star)](https://github.com/yourusername/flow)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://python.org)

> A powerful CLI tool for screen activity tracking, AI-powered analysis, and content generation using ChromaDB and Model Context Protocol (MCP).

## Installation

### Prerequisites
- **Python 3.10+** (tested with Python 3.13.7)
- **Tesseract OCR** (install via system package manager)
- **Screen capture permissions** (macOS: System Preferences > Security & Privacy > Privacy > Screen Recording)

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/flow.git
   cd flow
   ```

2. **Set up ChromaDB environment**
   ```bash
   cd chroma
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r chroma-requirements.txt
   cd ..
   ```

3. **Set up Refinery tracking environment**
   ```bash
   cd refinery
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r flow-requirements.txt
   cd ..
   ```

4. **Set up MCP server environment**
   ```bash
   cd mcp-flow-node
   npm install
   cd ..
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
Flow CLI
├── Screen Detection & OCR
├── ChromaDB Vector Store
├── MCP Server (stdio)
├── Summary Tools (via MCP)
├── Sprout Generator
└── CLI Interface
```

**Multi-Screen Support:**
- Flow automatically detects all available screens
- Screen naming convention: `screen_0` (primary), `screen_1` (secondary), `screen_N` (additional)
- Screenshots saved as: `{timestamp}_{screen_name}.png`
- OCR data saved as: `{timestamp}_{screen_name}.json`

**Background Processing:**
- Screenshots are captured every minute by default
- OCR processing happens in background threads to avoid blocking
- All data is stored in ChromaDB collection "screenshots" for search and analysis

**Data Storage:**
- Screenshots: Processed in memory only (not saved to disk)
- OCR data: `refinery/data/ocr/` (JSON files with extracted text)
- ChromaDB: Vector database for semantic search across all captured content

---

⭐ **Star this repository** if you find it helpful!