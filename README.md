# Flow

[![GitHub stars](https://img.shields.io/github/stars/joenewbry/flow.svg?style=social&label=Star)](https://github.com/joenewbry/flow)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://python.org)

Flow takes a screenshot each minute in the background and makes it searchable via well structured MCP tools. 

I use it with Claude.

**So you can get questions like:**
- Find the URL of the hacker news posts about Anthropic
- Can you summarize what I worked on yesterday?
- Please create onboarding documentation for the Centurion Project that I worked on in March 2025.

**It's designed for Claude (or any other MCP frontend)**

The entire codebase is in pre-release.

## 🚀 Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/joenewbry/flow.git
cd flow
```

### 2. Setup & Start ChromaDB + Screen Capture
```bash
# Setup
cd refinery
python3 -m venv .venv
source .venv/bin/activate
pip install -r flow-requirements.txt

# Start ChromaDB (Terminal 1)
brew install tesseract
chroma run --host localhost --port 8000

# Start Screen Capture (Terminal 2 - from refinery directory)
source .venv/bin/activate && python run.py
```
*You'll need to accept screen recording in system settings for terminal (or Cursor) or wherever you're running the OCR process*

**That's it!** Flow is now capturing screenshots every minute and storing them in ChromaDB.

---

## 🤖 Claude Desktop Integration

**Configure Claude Desktop:**
Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "flow": {
      "command": "/Users/YOUR_USERNAME/dev/flow/mcp-server/.venv/bin/python",
      "args": ["-u", "/Users/YOUR_USERNAME/dev/flow/mcp-server/server.py"]
    }
  }
}
```

**Setup steps:**
1. Open settings in Claude
2. Open developer settings (this creates the config file mentioned above)
3. Open the config file in your favorite text editor and paste in your config
4. Make sure to update the `YOUR_USERNAME` portion
5. Restart Claude Desktop

📖 **Configuration Guide:** See [Claude's MCP documentation](https://modelcontextprotocol.io/quickstart/user) for more details.

---

## 🔍 Using Flow

### MCP Tools in Claude Desktop

Once Flow is running, you can query your screen history through Claude Desktop using natural language:

**Example queries:**
- "Find the GitHub repository I was looking at yesterday"
- "What was I working on between 2pm and 5pm?"
- "Show me screenshots containing 'project deadline'"

**Available tools:**
- 🔍 `search-screenshots` - Search OCR data
- 📊 `get-stats` - System statistics  
- 📈 `activity-graph` - Activity timeline
- 📅 `time-range-summary` - Time range data
- ▶️ `start-flow` / ⏹️ `stop-flow` - System control

### Search Capabilities

Flow uses **vector-based semantic search**, which means:

✅ **Supported Queries:**
- "Find the email I drafted to Emily about dog sitting last month"
- "Show me the GitHub repository I was looking at yesterday"
- "What was that error message about database connection?"

❌ **Less Effective Queries:**
- "Find the exact word 'banana' on my screen"
- "Show me all instances of the text 'ERROR 404'"

---

## 🌐 NGROK Setup (Optional)

To expose your MCP server via NGROK for remote access:

1. **Install ngrok:**
```bash
brew install ngrok/ngrok/ngrok
ngrok config add-authtoken YOUR_AUTH_TOKEN
```

2. **Start HTTP MCP Server:**
```bash
cd mcp-server
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python http_server.py --port 8082
```

3. **Expose via ngrok:**
```bash
ngrok http 8082
```

4. **Update Claude Desktop config** to use the ngrok URL for remote access.

---

## 🏗️ Architecture

**Data Flow:**
1. Screen Capture → Automatic screenshots every 60 seconds
2. OCR Processing → Tesseract extracts text
3. Data Storage → JSON files with timestamps
4. Vector Indexing → ChromaDB creates semantic embeddings
5. Search & Retrieval → MCP server processes queries

---

## 🛠️ Troubleshooting

### ChromaDB Connection Failed
```bash
# Verify ChromaDB is running
curl http://localhost:8000/api/v1/heartbeat

# Restart ChromaDB
cd refinery && chroma run --host localhost --port 8000
```

### Screen Capture Not Working
```bash
# Check OCR dependencies
tesseract --version

# Verify screen recording permissions (macOS)
# System Preferences > Security & Privacy > Privacy > Screen Recording
```

### MCP Server Issues
```bash
# Test MCP server directly
cd mcp-server && python server.py

# Check Claude Desktop logs
# macOS: ~/Library/Logs/Claude/
```

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 📧 Support

- **Issues**: [GitHub Issues](https://github.com/joenewbry/flow/issues)
- **Email**: joenewbry+flow@gmail.com
