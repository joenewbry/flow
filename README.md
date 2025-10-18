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

![Example Usage](images/Flow%20Example.png)

The entire codebase is in pre-release. And it's packed with a bunch of other interesting tools:

- Background audio recording 
- Simple website creation backed by human readable markdown files and sharable over ngrok

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
python -m venv .venv
source .venv/bin/activate
pip install -r flow-requirements.txt

# Start ChromaDB (Terminal 1)
chroma run --host localhost --port 8000

# Start Screen Capture (Terminal 2 - from refinery directory)
source .venv/bin/activate && python run.py
```

**That's it!** Flow is now capturing screenshots every minute and storing them in ChromaDB.

---

## 🤖 Claude Desktop Integration

### Setup MCP Server for Claude Desktop
To search your screen history through Claude Desktop, set up the MCP server:

```bash
# Setup (from project root)
cd mcp-server
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
chmod +x start.sh
```

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

**Then restart** Claude Desktop to load the MCP server.

📖 **Configuration Guide:** See [Claude's MCP documentation](https://modelcontextprotocol.io/quickstart/user) for more details on setting up MCP servers.

---

## 🔍 Using Flow

### MCP Tools in Claude Desktop

Once Flow is running, you can query your screen history through Claude Desktop using natural language:

**Example queries:**
- "Find the GitHub repository I was looking at yesterday"
- "What was I working on between 2pm and 5pm?"
- "Show me screenshots containing 'project deadline'"
- "Create a webpage summary of my work this week"

**Available tools:**
- 🔍 `search-screenshots` - Search OCR and audio data
- 📊 `get-stats` - System statistics  
- 📈 `activity-graph` - Activity timeline
- 📅 `time-range-summary` - Time range data
- ▶️ `start-flow` / ⏹️ `stop-flow` - System control
- 🌐 `create-webpage` - Generate shareable pages

### Search Capabilities

Flow uses **semantic vector search** across all your data:

**OCR Data** (`data_type: "ocr"`)
- Screenshots captured every minute
- Text extracted via Tesseract OCR
- Stored in `refinery/data/ocr/*.json`

**Audio Data** (`data_type: "audio"`) - if enabled
- Continuous audio transcription
- Microphone + system audio (with BlackHole)
- Stored in `refinery/data/audio/*.md`

Both are searchable together or separately:
```python
# Search everything
"Find anything about the project deadline"

# Search only audio
search_screenshots(query="zoom meeting notes", data_type="audio")

# Search only screens
search_screenshots(query="github repository", data_type="ocr")
```

---

## 🎛️ Optional Setup

### 🎙️ Audio Recording & Transcription
Record and transcribe microphone + system audio (Zoom, YouTube, etc.).

**Setup:**
```bash
# 1. Install BlackHole (for system audio capture)
brew install blackhole-2ch

# 2. Configure Audio MIDI Setup
# - Open "Audio MIDI Setup" app
# - Create Multi-Output Device (Speakers + BlackHole)
# - Set as system default output
# See AUDIO_SETUP_GUIDE.md for detailed instructions

# 3. Install dependencies
./setup_audio_recorder.sh

# 4. Add OpenAI API key
echo "OPENAI_API_KEY=sk-your-key-here" > .env
```

**Start Recording:**
```bash
# Terminal 5
./start_audio_background.sh
```

**What it captures:**
- 🎤 Microphone input
- 🔊 System audio (YouTube, Zoom, music)
- 💬 Both sides of video calls

**Storage:**
- `refinery/data/audio/*.md` - Markdown transcripts
- ChromaDB - Searchable with `data_type: "audio"` tag

📖 **Full Guide:** See `AUDIO_SETUP_GUIDE.md`

---

### 🌐 Website Builder & Ngrok Sharing
Create and share webpage summaries of your work publicly.

#### Creating Webpages
Use the MCP `create-webpage` tool in Claude Desktop:
```
"Create a webpage called 'weekly-update' with title 'Weekly Team Update' 
containing my activity from this week"
```

Pages are saved as markdown in `website-builder/pages/` and rendered on-the-fly.

---

#### HTTP MCP Server
Serves both MCP tools AND webpages. Use this if you want remote MCP access too.

**Start Server:**
```bash
cd mcp-server
source .venv/bin/activate
python http_server.py --port 8082
```

**Expose via Ngrok:**
```bash
ngrok http 8082
```

**Access Pages:**
- Local: `http://localhost:8082/page/my-summary`
- Public: `https://abc123.ngrok-free.app/page/my-summary`

**Bonus:** Update MCP config to use ngrok URL for remote Claude Desktop access.

---

## 🌐 Team Collaboration with Ngrok

Flow supports team collaboration by exposing your MCP server via ngrok, allowing team members to query each other's screen history remotely.

**⚠️ Note:** Team usage features are currently untested.

### Why Use This?

- **Cross-team queries**: Ask "Has John finished the UI designs?" by searching his Flow instance
- **Remote access**: Access your own Flow data from anywhere
- **Team coordination**: Check what teammates are working on without interrupting them
- **Knowledge sharing**: Create and share searchable pages with findings

### Quick Setup

1. **Install ngrok**:
```bash
brew install ngrok/ngrok/ngrok
ngrok config add-authtoken YOUR_AUTH_TOKEN
```

2. **Start HTTP MCP Server**:
```bash
cd mcp-server
python http_server.py --port 8082
```

3. **Expose via ngrok**:
```bash
ngrok http 8082
# Save the https URL provided
```

4. **Configure Claude Desktop for Multiple Instances**:

Edit your Claude Desktop config to connect to multiple team members:

```json
{
  "mcpServers": {
    "flow-team": {
      "command": "python",
      "args": ["/Users/joe/dev/flow/mcp-server/multi_instance_client.py"],
      "cwd": "/Users/joe/dev/flow/mcp-server",
      "env": {
        "FLOW_INSTANCES": "joe:local,john:https://john-abc.ngrok.io,jill:https://jill-def.ngrok.io"
      }
    }
  }
}
```

### Multi-Instance Usage

With the multi-instance setup, tools are automatically prefixed with usernames:

```
# Search John's Flow
"Use john-search-screenshots to find mobile app designs"

# Check Jill's activity
"Use jill-activity-graph to see what she worked on this week"

# Search your own Flow
"Use joe-search-screenshots to find that email I saw yesterday"
```

### Security

For production use, enable authentication:

```bash
# Basic auth
ngrok http 8082 --basic-auth="username:password"

# OAuth with Google
ngrok http 8082 --oauth=google --oauth-allow-domain="yourcompany.com"

# IP restrictions
ngrok http 8082 --cidr-allow="192.168.1.0/24"
```

**📖 Full Documentation**: See `workspace/ngrok-for-mcp-server.md` for complete setup instructions, security considerations, and advanced configurations.

---

## 🏗️ Architecture

### System Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Screen Capture │    │   ChromaDB      │    │  Audio Recording│
│   (refinery/)   │    │ (Port 8000)     │    │ (background)    │
│                 │    │                 │    │                 │
│ • Auto Screenshots   │ • Vector Store  │    │ • Microphone    │
│ • OCR Processing│    │ • Search Engine │    │ • System Audio  │
│ • Data Storage  │    │ • Embeddings    │    │ • Transcription │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   MCP Server    │
                    │  (Port varies)  │
                    │                 │
                    │ • Claude Tools  │
                    │ • API Gateway   │
                    │ • Search Logic  │
                    │ • Web Pages     │
                    └─────────────────┘
                             │
                    ┌─────────────────┐
                    │ Claude Desktop  │
                    │                 │
                    │ • Natural Lang. │
                    │ • Tool Calling  │
                    │ • User Interface│
                    └─────────────────┘
```

### Team Architecture Usage

```
┌─────────────────────────────────────────────────────────┐
│                    Team Collaboration                    │
└─────────────────────────────────────────────────────────┘

    User 1 (Joe)              User 2 (John)             User 3 (Jill)
         │                         │                         │
    ┌────▼────┐               ┌────▼────┐              ┌────▼────┐
    │  Flow   │               │  Flow   │              │  Flow   │
    │ Instance│               │ Instance│              │ Instance│
    └────┬────┘               └────┬────┘              └────┬────┘
         │                         │                         │
    ┌────▼────┐               ┌────▼────┐              ┌────▼────┐
    │ MCP     │               │ MCP     │              │ MCP     │
    │ Server  │               │ Server  │              │ Server  │
    │ (local) │               │ (ngrok) │              │ (ngrok) │
    └────┬────┘               └────┬────┘              └────┬────┘
         │                         │                         │
         │         https://john    │    https://jill         │
         │         -abc.ngrok.io   │    -def.ngrok.io        │
         │                         │                         │
         └─────────────────────────┼─────────────────────────┘
                                   │
                          ┌────────▼────────┐
                          │  Multi-Instance │
                          │  MCP Client     │
                          └────────┬────────┘
                                   │
                          ┌────────▼────────┐
                          │ Claude Desktop  │
                          │                 │
                          │ joe-search-*    │
                          │ john-search-*   │
                          │ jill-search-*   │
                          └─────────────────┘
```

**Note:** Team collaboration features are untested. Use with caution in production environments.

### Data Flow

#### Screen OCR Pipeline:
1. **Screen Capture**: Automatic screenshots every 60 seconds across all monitors
2. **OCR Processing**: Tesseract extracts text from screenshots in background threads
3. **Data Storage**: OCR results saved as JSON files with timestamp and screen info
4. **Vector Indexing**: ChromaDB creates semantic embeddings tagged with `data_type: "ocr"`
5. **Search & Retrieval**: MCP server processes queries and returns relevant results

#### Audio Transcription Pipeline:
1. **Audio Detection**: Monitors system audio for activity (Zoom, meetings, etc.)
2. **Chunk Recording**: Captures audio in 30-second chunks when detected
3. **OpenAI Transcription**: Real-time transcription using Whisper API
4. **Markdown Storage**: Saves as readable `.md` files in `refinery/data/audio/`
5. **Vector Indexing**: ChromaDB stores transcripts tagged with `data_type: "audio"`
6. **Unified Search**: Audio and OCR data searchable together in same collection

#### Website Creation Pipeline:
1. **Content Generation**: Use `create-webpage` MCP tool to generate markdown pages
2. **Page Storage**: Markdown files saved in `website-builder/pages/`
3. **HTTP Serving**: MCP HTTP server renders pages on-the-fly
4. **Public Sharing**: Expose via ngrok for team access
5. **Dynamic Updates**: Edit markdown files to update pages instantly

### File Structure

```
flow/
├── dashboard/                      # Web dashboard
│   ├── app.py                     # FastAPI application
│   ├── lib/                       # Core libraries
│   ├── api/                       # API endpoints
│   ├── templates/                 # HTML templates
│   └── static/                    # CSS, JS, assets
├── mcp-server/                    # Python MCP server
│   ├── server.py                  # Main MCP server
│   ├── http_server.py             # HTTP MCP server with web pages
│   ├── multi_instance_client.py   # Multi-instance team client
│   ├── tools/                     # MCP tool implementations
│   └── start.sh                   # Startup script
├── refinery/                      # Screen capture system
│   ├── run.py                     # Main capture script
│   ├── lib/                       # OCR and ChromaDB logic
│   └── data/                      # Captured data storage
│       ├── ocr/                   # OCR JSON files (tagged: data_type="ocr")
│       └── audio/                 # Audio transcripts (tagged: data_type="audio")
│           ├── *.md              # Markdown transcripts
│           ├── *.json            # Session metadata
│           └── *.wav             # Audio recordings
├── website-builder/               # Website builder
│   ├── server.py                  # Web server
│   ├── pages/                     # Markdown pages
│   └── templates/                 # HTML templates
├── audio_background_recorder.py  # Audio recording service
├── start_audio_background.sh     # Audio service startup
└── README.md                      # This file
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# OpenAI Configuration (required for audio transcription)
OPENAI_API_KEY=sk-your-api-key-here

# ChromaDB Configuration
CHROMA_HOST=localhost
CHROMA_PORT=8000

# Screen Capture Configuration
CAPTURE_INTERVAL=60
MAX_CONCURRENT_OCR=4

# Logging Configuration
LOG_LEVEL=INFO
```

### Screen Capture Settings

Edit `refinery/config.json`:

```json
{
  "capture_interval": 60,
  "max_concurrent_ocr": 4,
  "auto_start": false,
  "data_retention_days": 90,
  "compress_old_data": true
}
```

## 📊 Search Capabilities

### Vector Search vs Exact Search

Flow uses **vector-based semantic search**, which means:

✅ **Supported Queries:**
- "Find the email I drafted to Emily about dog sitting last month"
- "Show me the GitHub repository I was looking at yesterday"
- "What was that error message about database connection?"
- "Find the meeting notes from the project review"
- "What did we discuss in the Zoom call yesterday afternoon?" (audio)

❌ **Less Effective Queries:**
- "Find the exact word 'banana' on my screen"
- "Show me all instances of the text 'ERROR 404'"

### Search Tips

1. **Use natural language**: Describe what you're looking for conversationally
2. **Include context**: Mention timeframes, people, or topics
3. **Be specific about intent**: "email about X" vs "document containing X"
4. **Use date ranges**: Narrow down searches to specific periods
5. **Filter by type**: Use metadata filters to search only OCR or audio data

### Filtering Audio vs OCR Data

You can filter searches by data type in the ChromaDB collection:

```python
# Search only audio transcripts
results = collection.query(
    query_texts=["project discussion"],
    where={"data_type": "audio"}
)

# Search only screen OCR
results = collection.query(
    query_texts=["github repository"],
    where={"data_type": "ocr"}
)

# Search both (default - no filter)
results = collection.query(
    query_texts=["project deadline"]
)
```

## 🛠️ Troubleshooting

### Common Issues

#### ChromaDB Connection Failed
```bash
# Verify ChromaDB is running
curl http://localhost:8000/api/v1/heartbeat

# Restart ChromaDB
cd refinery && chroma run --host localhost --port 8000
```

#### Screen Capture Not Working
```bash
# Check OCR dependencies
tesseract --version

# Verify screen recording permissions (macOS)
# System Preferences > Security & Privacy > Privacy > Screen Recording
```

#### MCP Server Issues
```bash
# Test MCP server directly
cd mcp-server && python server.py

# Check Claude Desktop logs
# macOS: ~/Library/Logs/Claude/
# Windows: %APPDATA%/Claude/logs/
```

### Performance Optimization

1. **Reduce Capture Interval**: Increase from 60s to 120s for less frequent captures
2. **Limit OCR Processes**: Reduce `max_concurrent_ocr` if system is slow
3. **Enable Data Compression**: Turn on compression for older data
4. **Disk Space Management**: Set appropriate data retention policies

## 🎯 Roadmap

### Completed Features
- ✅ **Audio recording with speech-to-text integration** (October 11, 2025)
- ✅ **Sharable pages with markdown export** (October 11, 2025)

### Planned Features
- [ ] Team collaboration via ngrok
- [ ] Improve Website Page Creation

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## 📧 Support

- **Email**: joenewbry+flow@gmail.com
- **Issues**: [GitHub Issues](https://github.com/joenewbry/flow/issues)
- **Discussions**: [GitHub Discussions](https://github.com/joenewbry/flow/discussions)
