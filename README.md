# Flow CLI

[![GitHub stars](https://img.shields.io/github/stars/yourusername/flow.svg?style=social&label=Star)](https://github.com/yourusername/flow)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://python.org)

> A powerful CLI tool for screen activity tracking, AI-powered analysis, and content generation using ChromaDB and Model Context Protocol (MCP).

## ✨ Features

### 🖥️ Screen Activity Tracking
- **Automatic Screenshot Capture**: Continuously monitors screen activity with configurable intervals
- **OCR Processing**: Extracts text content from screenshots using Tesseract
- **Smart Detection**: Focuses on main screen or multi-monitor setups
- **Activity Summarization**: Generates intelligent summaries of screen activity over time

### 🧠 AI-Powered Analysis
- **Vector Search**: ChromaDB integration for semantic search across screen content
- **Time-based Queries**: Get summaries for specific days, hours, or custom time ranges
- **Content Analysis**: AI-driven insights from your screen activity patterns

### 🔌 Model Context Protocol (MCP) Integration
- **Native MCP Server**: Direct integration with MCP-compatible AI clients
- **HTTP REST API**: RESTful endpoints for web applications and integrations
- **Tool Ecosystem**: Extensible tool system for custom functionality

### 🌱 Sprout Generation
- **HTML Content Creation**: Generate beautiful HTML documents from markdown
- **Password Protection**: Secure content with optional password protection
- **Custom Styling**: Multiple style themes for different use cases
- **Static Site Generation**: Create standalone HTML files for sharing

### 🛠️ Developer Experience
- **Simple CLI Interface**: Easy-to-use commands with intuitive options
- **Environment Configuration**: Secure configuration with `.env` files
- **Docker Support**: Easy deployment with Docker containers
- **Extensible Architecture**: Plugin system for custom functionality

## 🚀 Quick Start

### Prerequisites
- **Python 3.10+** (tested with Python 3.13.7)
- **Tesseract OCR** (install via system package manager)
- **Screen capture permissions** (macOS: System Preferences > Security & Privacy > Privacy > Screen Recording)

### Installation

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

3. **Set up Flow tracking environment**
   ```bash
   cd flow
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r flow-requirements.txt
   cd ..
   ```

4. **Set up MCP server environment**
   ```bash
   # Option 1: Node.js server (recommended)
   cd mcp-flow-node
   npm install
   cd ..
   
   # Option 2: Python server (legacy)
   cd mcp-flow
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r flow-mcp-requirements.txt
   cd ..
   ```

5. **Configure environment** (optional)
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

### System Requirements

**Python 3.10+** (tested with Python 3.13.7) required for:
- **ChromaDB Server**: Python 3.10+ (for ChromaDB compatibility)
- **Flow Tracking**: Python 3.10+ (for modern async features)
- **MCP Server (Python)**: Python 3.10+ (MCP requires Python 3.10+)

**Node.js LTS** required for:
- **MCP Server (Node.js)**: Recommended implementation following MCP best practices

**Recommended**: Use version managers like [pyenv](https://github.com/pyenv/pyenv) for Python and [nvm](https://github.com/nvm-sh/nvm) for Node.js to easily switch between versions.

### Basic Usage

1. **Start ChromaDB server**
   ```bash
   cd chroma
   source .venv/bin/activate
   chroma run --host localhost --port 8000
   cd ..
   ```
   > **Important**: Start ChromaDB from the **root directory** after activating the chroma virtual environment. This ensures proper database initialization and persistence.

2. **Start screen tracking**
   ```bash
   cd flow
   source .venv/bin/activate
   python run.py
   cd ..
   ```

3. **Start MCP server** (for Claude Desktop integration)
   ```bash
   cd mcp-flow-node
   npm install
   node server.js
   cd ..
   ```

### Testing the Installation

To verify everything is working correctly:

1. **Test ChromaDB connection**
   ```bash
   # In a new terminal, test ChromaDB is running
   curl http://localhost:8000/api/v1/heartbeat
   ```

2. **Test Flow tracking**
   - Start the Flow runner and verify OCR data is being saved to `flow/data/ocr/`
   - Check logs for successful screenshot capture and OCR processing
   - Note: Screenshots are processed in memory and not saved to disk

3. **Test MCP server with Claude Desktop**
   
   **Configure Claude Desktop:**
   
   Create or edit the Claude Desktop configuration file:
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
   
   Add the following configuration:
   ```json
   {
     "mcpServers": {
       "flow": {
         "command": "node",
         "args": [
           "/Users/joe/dev/flow/mcp-flow-node/server.js"
         ],
         "cwd": "/Users/joe/dev/flow/mcp-flow-node"
       }
     }
   }
   ```
   
   **Important**: Replace the paths with your actual installation paths.
   
   **Restart Claude Desktop** after making configuration changes.
   
   **Test the integration:**
   - Open Claude Desktop
   - Try using the Flow tools:
     - `@flow hello-world` - Test the hello-world tool
     - Look for the MCP server indicator (🔨) in the bottom-right corner
     - Click the indicator to see available Flow tools

## 🔧 Developer Setup: Connecting to Claude Desktop

Flow provides MCP (Model Context Protocol) servers that extend Claude Desktop's capabilities. This section covers how to connect Flow as a developer, following the [official MCP documentation](https://modelcontextprotocol.io/docs/develop/connect-local-servers).

### Prerequisites

Before connecting Flow to Claude Desktop, ensure you have:

- **Claude Desktop** installed and updated to the latest version
- **Node.js** (LTS version recommended) for the MCP server
- **Python 3.10+** for the Flow tracking components

### Understanding MCP Servers

MCP servers are programs that run on your computer and provide specific capabilities to Claude Desktop through a standardized protocol. Flow's MCP server exposes tools that Claude can use to:

- Search your screenshot data with semantic queries
- Generate summaries of your screen activity
- Get statistics about your screenshot collection
- Access time-based activity analysis

All actions require your explicit approval before execution, ensuring you maintain full control over what Claude can access.

### Configuration Methods

Flow supports two MCP server implementations:

#### Option 1: Node.js Server (Recommended)

The Node.js implementation follows MCP best practices and is easier to configure:

1. **Open Claude Desktop Settings:**
   - Click the Claude menu in your system's menu bar
   - Select "Settings..." (not the settings within the Claude window)
   - Navigate to the "Developer" tab
   - Click "Edit Config" to open the configuration file

2. **Configure the Node.js Server:**
   ```json
   {
     "mcpServers": {
       "flow": {
         "command": "node",
         "args": [
           "/Users/joe/dev/flow/mcp-flow-node/server.js"
         ],
         "cwd": "/Users/joe/dev/flow/mcp-flow-node"
       }
     }
   }
   ```

3. **Replace paths** with your actual Flow installation directory.

#### Option 2: Python Server (Legacy)

For the Python implementation:

```json
{
  "mcpServers": {
    "flow": {
      "command": "/Users/joe/dev/flow/mcp-flow/.venv/bin/python",
      "args": [
        "-u",
        "/Users/joe/dev/flow/mcp-flow/flow_mcp_server.py"
      ],
      "cwd": "/Users/joe/dev/flow/mcp-flow",
      "env": {
        "PYTHONPATH": "/Users/joe/dev/flow/src",
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

### Configuration File Locations

The Claude Desktop configuration file is located at:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

### Step-by-Step Setup

1. **Install Dependencies:**
   ```bash
   # For Node.js server
   cd mcp-flow-node
   npm install
   
   # For Python server
   cd mcp-flow
   source .venv/bin/activate
   pip install -r flow-mcp-requirements.txt
   ```

2. **Configure Claude Desktop:**
   - Open Claude Desktop settings
   - Navigate to Developer tab
   - Click "Edit Config"
   - Add the appropriate configuration (see options above)
   - Save the file

3. **Restart Claude Desktop:**
   - Completely quit Claude Desktop
   - Restart the application
   - Look for the MCP server indicator (🔨) in the bottom-right corner

4. **Verify Connection:**
   - Click the MCP server indicator to see available tools
   - Try using Flow tools in Claude Desktop

### Testing the Integration

Once connected, you can test Flow tools in Claude Desktop:

- **"Hello from Flow"** - Test the hello-world tool
- **"Search my screenshots for 'meeting notes'"** - Search your screenshot data
- **"Get my daily activity summary"** - Generate activity summaries
- **"Show me Flow statistics"** - Get collection statistics

### Troubleshooting

If you encounter issues:

1. **Server not showing up:**
   - Restart Claude Desktop completely
   - Check your `claude_desktop_config.json` file syntax
   - Ensure file paths are absolute (not relative)
   - Verify Node.js/Python is installed and accessible

2. **Check logs:**
   ```bash
   # macOS/Linux
   tail -n 20 -f ~/Library/Logs/Claude/mcp*.log
   
   # Windows
   tail -n 20 -f %APPDATA%\Claude\logs\mcp*.log
   ```

3. **Manual server testing:**
   ```bash
   # Test Node.js server
   cd mcp-flow-node
   node server.js
   
   # Test Python server
   cd mcp-flow
   source .venv/bin/activate
   python flow_mcp_server.py
   ```

4. **Common issues:**
   - **ENOENT errors on Windows**: Add expanded `%APPDATA%` path to `env` section
   - **NPM not found**: Install NPM globally with `npm install -g npm`
   - **Python path issues**: Verify virtual environment activation and PYTHONPATH

### Security Considerations

- Only grant access to directories you're comfortable with Claude reading/modifying
- The server runs with your user account permissions
- All file operations require explicit approval
- Review each request carefully before approving

### Next Steps

Once Flow is connected to Claude Desktop:

- Explore Flow's screen activity analysis capabilities
- Use semantic search across your screenshot data
- Generate time-based activity summaries
- Build custom workflows with Flow's MCP tools

For more advanced usage, see the [MCP documentation](https://modelcontextprotocol.io/docs/develop/connect-local-servers) and [Flow's architecture section](#architecture).

### Details on How Flow Runs

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
- OCR data: `flow/data/ocr/` (JSON files with extracted text)
- ChromaDB: Vector database for semantic search across all captured content

## 📚 Documentation

### Commands

#### Screen Tracking
```bash
# Track screen activity
./bin/flow track [OPTIONS]

Options:
  --interval INTEGER    Screenshot interval in seconds (default: 30)
  --ocr               Enable OCR processing
  --main-screen-only  Only capture main screen
```

#### Summaries
```bash
# Get activity summaries
./bin/flow summary [OPTIONS]

Options:
  --date TEXT         Specific date (YYYY-MM-DD)
  --hours INTEGER     Last N hours
  --time-range TEXT   Custom time range
```

#### Sprout Generation
```bash
# Generate HTML documents
./bin/flow sprout TITLE DESCRIPTION [OPTIONS]

Options:
  --content TEXT      Content text
  --file PATH         Markdown file
  --style TEXT        Style theme
  --password TEXT     Password protection
```

### Server Management

#### Start ChromaDB
```bash
./scripts/start-chroma.sh
```

#### Start MCP Server
```bash
./scripts/start-mcp-server.sh
```


## 🔧 Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

```env
# ChromaDB Configuration
CHROMA_HOST=localhost
CHROMA_PORT=8000
CHROMA_PERSIST_DIRECTORY=./data/chroma

# MCP HTTP Bridge Configuration
MCP_HTTP_PORT=3000

# Logging Configuration
LOG_LEVEL=INFO

# Optional: API Keys
# OPENAI_API_KEY=your_key_here
# ANTHROPIC_API_KEY=your_key_here
```

## 🏗️ Architecture

```
Flow CLI
├── Screen Detection & OCR
├── ChromaDB Vector Store
├── MCP Server (stdio)
├── Summary Tools (via MCP)
├── Sprout Generator
└── CLI Interface
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [ChromaDB](https://www.trychroma.com/) for vector search capabilities
- [Model Context Protocol](https://modelcontextprotocol.io/) for AI integration
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) for text extraction
- [FastAPI](https://fastapi.tiangolo.com/) for the HTTP bridge

---

⭐ **Star this repository** if you find it helpful!