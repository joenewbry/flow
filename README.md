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
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r chroma-requirements.txt
   cd ..
   ```

3. **Set up Flow tracking environment**
   ```bash
   cd flow
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r flow-requirements.txt
   cd ..
   ```

4. **Set up MCP server environment**
   ```bash
   cd mcp-flow
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r flow-mcp-requirements.txt
   cd ..
   ```

5. **Configure environment** (optional)
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

### Python Version Requirements

All three virtual environments require **Python 3.10+** (tested with Python 3.13.7):

- **ChromaDB Server**: Python 3.10+ (for ChromaDB compatibility)
- **Flow Tracking**: Python 3.10+ (for modern async features)
- **MCP Server**: Python 3.10+ (MCP requires Python 3.10+)

**Recommended**: Use a Python version manager like [pyenv](https://github.com/pyenv/pyenv) to easily switch between Python versions if needed.

### Basic Usage

1. **Start ChromaDB server**
   ```bash
   cd chroma
   source venv/bin/activate
   chroma run --host localhost --port 8000
   cd ..
   ```
   > **Important**: Start ChromaDB from the **root directory** after activating the chroma virtual environment. This ensures proper database initialization and persistence.

2. **Start screen tracking**
   ```bash
   cd flow
   source venv/bin/activate
   python run.py
   cd ..
   ```

3. **Start MCP server** (for Claude Desktop integration)
   ```bash
   cd mcp-flow
   source venv/bin/activate
   python flow_mcp_server.py
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
   - Start the Flow runner and check that screenshots are being saved to `/flow/data/screenshots/`
   - Verify OCR data is being saved to `/flow/data/ocr/`
   - Check logs for successful screenshot capture and OCR processing

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
         "command": "python",
         "args": ["/Users/joe/dev/flow/mcp-flow/flow_mcp_server.py"],
         "cwd": "/Users/joe/dev/flow/mcp-flow"
       }
     }
   }
   ```
   
   **Important**: Replace the paths with your actual installation paths.
   
   **Restart Claude Desktop** after making configuration changes.
   
   **Test the integration:**
   - Open Claude Desktop
   - Try using the Flow tools:
     - `@flow what-can-i-do` - Get information about Flow capabilities
     - `@flow search-screenshots "your search query"` - Search your screenshot data
     - `@flow fetch-flow-stats` - Get statistics about your screenshot collection

### Adding Flow Tools to Claude Desktop

**Step-by-Step Guide:**

1. **Locate Claude Desktop Configuration File:**
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
   - **Linux**: `~/.config/Claude/claude_desktop_config.json`

2. **Create or Edit Configuration:**
   ```json
   {
     "mcpServers": {
       "flow": {
         "command": "python",
         "args": ["/path/to/your/flow/mcp-flow/flow_mcp_server.py"],
         "cwd": "/path/to/your/flow/mcp-flow",
         "env": {
           "PYTHONPATH": "/path/to/your/flow/src"
         }
       }
     }
   }
   ```

3. **Important Notes:**
   - Replace `/path/to/your/flow/` with your actual Flow installation path
   - Ensure the MCP server virtual environment is activated in the system PATH
   - The `PYTHONPATH` environment variable helps the MCP server find the Flow source modules

4. **Restart Claude Desktop:**
   - Completely quit Claude Desktop
   - Restart the application
   - The Flow tools should now be available

5. **Verify Integration:**
   - In Claude Desktop, you should see Flow tools available
   - Try the commands listed in the testing section above

**Troubleshooting:**
- If tools don't appear, check the Claude Desktop logs for errors
- Ensure all virtual environments are properly activated
- Verify Python paths are correct in the configuration
- Make sure the MCP server starts without errors when run manually

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
- Screenshots: `/flow/data/screenshots/` (temporarily stored, deleted after OCR)
- OCR data: `/flow/data/ocr/` (JSON files with extracted text)
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

#### Start HTTP Bridge
```bash
./scripts/start-mcp-http-bridge.sh
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
├── MCP Servers
│   ├── Native MCP Server (stdio)
│   └── HTTP Bridge (REST API)
├── Summary Service
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