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
- Python 3.8+
- Docker (for ChromaDB)
- Tesseract OCR

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/flow.git
   cd flow
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

### Basic Usage

1. **Start ChromaDB server**
   ```bash
   chroma run --host localhost --port 8000
   ```
   > **Note**: Run this command in a separate terminal/venv as it needs to stay running in the background.

2. **Start screen tracking**
   ```bash
   ./bin/flow track --interval 30
   ```

3. **Generate a summary**
   ```bash
   ./bin/flow summary --hours 8
   ```

4. **Create a sprout (HTML document)**
   ```bash
   ./bin/flow sprout "My Document" "Description" --content "Hello World!"
   ```

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