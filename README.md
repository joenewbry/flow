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

**It's designed for Claude Desktop, Cursor, or any other MCP frontend**

The entire codebase is in pre-release.

## 🚀 Quick Start

### Easy install (Memex) — one command, no venv setup

Install like the Claude CLI: one curl, add to PATH, then start.

```bash
# Install (installs to ~/.memex and creates the memex command)
curl -fsSL https://raw.githubusercontent.com/joenewbry/flow/main/install.sh | sh

# Add memex to your shell (if ~/.local/bin isn’t already on PATH)
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc   # or ~/.bashrc
source ~/.zshrc

# Start Memex (ChromaDB + screen capture in the background)
memex start
```

**macOS:** Install Tesseract for OCR: `brew install tesseract`.  
Grant **Screen Recording** permission to Terminal (or Cursor) in System Settings → Privacy & Security.

Use `memex stop` to stop, `memex status` to check if it’s running.

---

### Manual setup (clone + venv)

**1. Clone Repository**
```bash
git clone https://github.com/joenewbry/flow.git
cd flow
```

**2. Setup & Start ChromaDB + Screen Capture**
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

## 💻 Memex CLI

Memex is a command-line interface for Flow that lets you search your screen history directly from the terminal, with optional AI-powered natural language queries.

### Installation

```bash
# Add to your PATH (add this line to ~/.zshrc or ~/.bashrc)
export PATH="$HOME/dev/flow/bin:$PATH"

# Reload your shell
source ~/.zshrc
```

### Basic Commands

```bash
memex status          # Quick health check - is everything running?
memex doctor          # Full system diagnostics
memex stats           # Activity statistics (screenshots today, etc.)
memex search "query"  # Direct text search
```

### AI-Powered Search (Optional)

The `memex ask` command uses AI to search your screen history with natural language and streaming responses.

**1. Install AI dependencies:**

```bash
# For Anthropic (Claude)
pip install anthropic

# For OpenAI (GPT-4)
pip install openai

# Or install all CLI dependencies
pip install -r ~/dev/flow/cli/requirements.txt
```

**2. Configure your API key:**

```bash
memex auth login
```

This will prompt you to select a provider (Anthropic or OpenAI) and enter your API key. Keys are stored securely in `~/.memex/credentials.json`.

Alternatively, set environment variables:
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
# or
export OPENAI_API_KEY="sk-..."
```

**3. Ask questions:**

```bash
memex ask "What was I working on yesterday?"
memex ask "Find any mentions of the API bug"
memex ask "Summarize my activity this week"
```

The AI will:
- Search your screenshot history using semantic search
- Show tool calls as they happen
- Stream the response token-by-token

### All CLI Commands

| Command | Description |
|---------|-------------|
| `memex status` | Quick health check |
| `memex doctor` | Full system diagnostics with fix suggestions |
| `memex stats` | Activity statistics and charts |
| `memex ask` | AI-powered natural language search |
| `memex search` | Direct text search |
| `memex start` | Start capture daemon |
| `memex stop` | Stop capture daemon |
| `memex watch` | Live view of captures |
| `memex auth` | Manage API keys |
| `memex config` | View/edit settings |
| `memex sync` | Sync OCR files to ChromaDB |

---

## 🤖 MCP Client Integration

Flow works with any MCP-compatible client. Choose your setup below:

### Option 1: Claude Desktop (Local)

**Configure Claude Desktop:**  
Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

- **If you used the easy install (Memex):** use your home directory and the shared venv:
```json
{
  "mcpServers": {
    "flow": {
      "command": "/Users/YOUR_USERNAME/.memex/.venv/bin/python",
      "args": ["-u", "/Users/YOUR_USERNAME/.memex/mcp-server/server.py"]
    }
  }
}
```

- **If you cloned the repo manually:** use your clone path:
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
4. Replace `YOUR_USERNAME` with your macOS username
5. Restart Claude Desktop

📖 **Configuration Guide:** See [Claude's MCP documentation](https://modelcontextprotocol.io/quickstart/user) for more details.

### Option 2: Cursor (Remote via NGROK)

**Prerequisites:**
- Flow HTTP server running (see NGROK Remote Access section below)
- NGROK tunnel active

**Configure Cursor:**
Edit `~/.cursor/mcp.json` (create if it doesn't exist):
```json
{
  "mcpServers": {
    "Memex": {
      "url": "https://YOUR_NGROK_URL.ngrok-free.dev/sse"
    }
  }
}
```

**Setup steps:**
1. Start the Flow HTTP server (see NGROK section below)
2. Start NGROK tunnel pointing to port 8082
3. Copy your NGROK URL (e.g., `https://abc123xyz.ngrok-free.dev`)
4. Create or edit `~/.cursor/mcp.json` with the configuration above
5. Replace `YOUR_NGROK_URL.ngrok-free.dev` with your actual NGROK URL
6. Restart Cursor

**Note:** The `/sse` endpoint is required for Cursor's MCP client. The HTTP server includes both SSE and standard HTTP endpoints.

---

## 🔍 Using Flow

### MCP Tools in Claude Desktop or Cursor

Once Flow is running, you can query your screen history through Claude Desktop or Cursor using natural language:

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

## 🌐 NGROK Remote Access (Required for Cursor)

To expose your MCP server via NGROK for remote access (required for Cursor, optional for Claude Desktop on a second computer):

### 1. Install and Configure NGROK

```bash
# Install ngrok
brew install ngrok/ngrok/ngrok

# Get your auth token from https://dashboard.ngrok.com/get-started/your-authtoken
ngrok config add-authtoken YOUR_AUTH_TOKEN
```

### 2. Start HTTP MCP Server

On your **primary computer** (where Flow is running):

```bash
cd mcp-server
source .venv/bin/activate
python http_server.py --port 8082
```

Keep this terminal open - the server needs to stay running.

### 3. Expose via NGROK

In a **new terminal** on your primary computer:

```bash
ngrok http 8082
```

Copy the forwarding URL (e.g., `https://abc123xyz.ngrok-free.app`). This is your public NGROK URL.

### 4. Connect from Remote Computer or Cursor

**For Cursor (on the same or different computer):**

Edit `~/.cursor/mcp.json`:
```json
{
  "mcpServers": {
    "Memex": {
      "url": "https://YOUR_NGROK_URL.ngrok-free.dev/sse"
    }
  }
}
```

Replace `YOUR_NGROK_URL.ngrok-free.dev` with your actual NGROK URL. The `/sse` endpoint is required for Cursor.

**For Claude Desktop on a second computer:**

If Claude Desktop supports HTTP transport, add to `~/Library/Application Support/Claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "flow-remote": {
      "url": "https://YOUR_NGROK_URL.ngrok-free.app/mcp",
      "transport": "http"
    }
  }
}
```

**For Gemini:**

Configure Gemini's MCP settings to point to your NGROK URL: `https://YOUR_NGROK_URL.ngrok-free.app/mcp`

**Note:** Free tier NGROK URLs change each time you restart. For a stable URL, consider upgrading to a paid plan.

**Security:** The current setup has no authentication. Consider adding API key authentication or using NGROK's basic auth: `ngrok http 8082 --basic-auth="username:password"`

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
# Test MCP server directly (stdio mode)
cd mcp-server && python server.py

# Test HTTP server
cd mcp-server && python http_server.py --port 8082

# Check Claude Desktop logs
# macOS: ~/Library/Logs/Claude/

# Check Cursor MCP connection
# Look for connection errors in Cursor's MCP server panel
```

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 📧 Support

- **Issues**: [GitHub Issues](https://github.com/joenewbry/flow/issues)
- **Email**: joenewbry+flow@gmail.com
