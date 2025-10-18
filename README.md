# Flow

[![GitHub stars](https://img.shields.io/github/stars/joenewbry/flow.svg?style=social&label=Star)](https://github.com/joenewbry/flow)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://python.org)

Don't loose your work. 

Flow takes a screenshot each minute in the background and makes it searchable via well structured MCP tools. 

I use it with Claude.

**So you can get questions like:**

- Find the URL of the hacker news posts about Anthropic
- Can you summarize what I worked on yesterday?
- Please create onboarding documentation for the Centurion Project that I worked on in March 2025.

** It's designed for Claude**
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

## 🤖 Claude/Cursor Integration

### Setup MCP Server for Claude Desktop or Cursor
To search your screen history through Claude or Cursor, set up the MCP server:

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

**Configure Cursor:**
Add to Cursor's MCP settings with the same configuration format.

**Then restart** Claude Desktop or Cursor to load the MCP server.

---

## 🎛️ Optional Setup

### 📊 Flow Dashboard (Web UI)
Monitor and control Flow through a web interface.

**Setup & Run:**
```bash
# Setup (from project root)
cd dashboard
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Start Dashboard (Terminal 4)
python app.py
```

**Access:** http://localhost:8081

**Features:**
- 📈 Real-time system monitoring
- 🔍 Search interface with date filtering
- 📊 OCR activity graphs
- ⚙️ System configuration panel
- 📝 Live system logs

---

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
Use the MCP `create-webpage` tool in Claude/Cursor:
```
"Create a webpage called 'weekly-update' with title 'Weekly Team Update' 
containing my activity from this week"
```

Pages are saved as markdown in `website-builder/pages/` and rendered on-the-fly.

---

#### Option 1: HTTP MCP Server (Recommended)
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

**Bonus:** Update MCP config to use ngrok URL for remote Claude/Cursor access.

---

#### Option 2: Website Builder Server (Simpler)
Just serves webpages, no MCP functionality. Use for simple page sharing.

**Start Server:**
```bash
cd website-builder
python3 server.py --port 8084
```

**Expose via Ngrok:**
```bash
ngrok http 8084
```

**Access Pages:**
- Local: `http://localhost:8084/page/my-summary`
- Public: `https://abc123.ngrok-free.app/page/my-summary`

**Features:**
- 📝 Renders markdown files on-the-fly
- 🎨 Beautiful BearBlog-inspired styling
- 📱 Responsive mobile design
- 🌓 Automatic dark/light theme
- 🔗 Simple, shareable URLs

**Page Management:**
```bash
# List all pages
curl http://localhost:8084/

# View specific page
open http://localhost:8084/page/my-summary

# Pages are stored as .md files
ls website-builder/pages/
```

---

## 🔍 Using Flow

### MCP Tools in Claude/Cursor

Once Flow is running, you can query your screen history through Claude Desktop or Cursor using natural language:

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

### Dashboard Features (if enabled)

Access the Flow Dashboard at **http://localhost:8081**

#### Dashboard Sections

#### 📈 **System Status & Controls**
- Real-time status of ChromaDB and screen capture processes
- One-click start/stop controls for all system components
- System health monitoring with automatic error recovery

#### 📊 **OCR Activity Graphs**
- Interactive timeline showing when screenshots were captured
- Scrollable history with zoom and pan functionality
- Visual gaps indicate periods of inactivity
- Customizable time ranges (hourly, daily views)

#### 🔍 **Search Interface**
- Search through all captured OCR data
- Date range filtering for targeted searches
- Real-time results with relevance scoring
- Export search results

#### ⚙️ **System Configuration**
- **Screen Capture Settings**: Interval, concurrent OCR processes, auto-start
- **Data Management**: Retention policies, file size limits, compression
- **Dashboard Settings**: Theme (light/dark/auto), refresh intervals, notifications
- **Advanced Settings**: Log levels, telemetry, experimental features

#### 📋 **System Logs**
- Real-time log viewer with automatic refresh
- Filter by log level (ERROR, WARNING, INFO, DEBUG)
- Download logs for analysis
- Clear logs and pagination support

#### 🛠️ **MCP Tools Dashboard**
- Overview of all 7 available MCP tools
- Test individual tools and verify functionality
- Usage examples and parameter documentation
- Claude Desktop configuration instructions

---

## 🤖 Advanced: Team Collaboration with Ngrok

Enable team collaboration by exposing your Flow instance over ngrok, allowing multiple team members to query each other's screen history.

**Team collaboration (with multi-instance setup):**
> "Has John finished the UI designs for XYZ? Search his Flow for figma mentions."
> "What was Jill working on yesterday afternoon between 2pm and 5pm?"
> "Search both John's and my Flow for discussions about the API redesign."

## 🏗️ Architecture

### System Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Flow Dashboard │    │  Screen Capture │    │   ChromaDB      │
│   (Port 8080)   │    │   (refinery/)   │    │ (Port 8000)     │
│                 │    │                 │    │                 │
│ • Web Interface │    │ • Auto Screenshots│   │ • Vector Store  │
│ • System Control│    │ • OCR Processing │    │ • Search Engine │
│ • Configuration │    │ • Data Storage   │    │ • Embeddings    │
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
├── audio_background_recorder.py  # Audio recording service
├── start_audio_background.sh     # Audio service startup
└── README.md                      # This file
```

## 🌐 Team Collaboration with Ngrok

Flow supports team collaboration by exposing your MCP server via ngrok, allowing team members to query each other's screen history remotely.

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

## 🔌 Using Flow MCP with Cursor

Flow's MCP server can be used as an extension in Cursor, allowing you to search your screen history and audio transcripts directly from Cursor's AI.

### Setup for Cursor

1. **Start the HTTP MCP Server**:
```bash
cd mcp-server
source .venv/bin/activate  # Activate the virtual environment
python http_server.py --port 8082
```

2. **Expose via ngrok** (for remote access):
```bash
# In another terminal
ngrok http 8082
```

You'll get an ngrok URL like: `https://abc123.ngrok-free.app`

3. **Verify the server is running**:
```bash
curl https://your-ngrok-url.ngrok-free.app
```

You should see:
```json
{
  "name": "Flow MCP HTTP Server",
  "version": "1.0.0",
  "status": "running",
  "endpoints": {
    "list_tools": "/tools/list",
    "call_tool": "/tools/call"
  }
}
```

4. **Configure Cursor**:

Open Cursor Settings → Features → MCP (or edit `.cursor/config.json`) and add:

```json
{
  "mcpServers": {
    "flow": {
      "url": "https://your-ngrok-url.ngrok-free.app",
      "transport": "http"
    }
  }
}
```

Replace `your-ngrok-url.ngrok-free.app` with your actual ngrok URL.

5. **Restart Cursor** to load the MCP extension.

### Using Flow in Cursor

Once configured, you can use Flow tools directly in Cursor:

**Search your screen history:**
```
@flow search for "github repository" from last week
```

**Search only audio transcripts:**
```
@flow search for "meeting discussion" in audio data_type
```

**Search only OCR:**
```
@flow search for "error message" in ocr data_type
```

**Get statistics:**
```
@flow show me system statistics
```

**Activity graph:**
```
@flow generate activity graph for last 7 days
```

### Available Tools in Cursor

All 7 Flow MCP tools are available:
- 🔍 `search-screenshots` - Search OCR and audio data
- ℹ️ `what-can-i-do` - Get Flow capabilities
- 📊 `get-stats` - System statistics
- 📈 `activity-graph` - Activity timeline
- 📅 `time-range-summary` - Time range data
- ▶️ `start-flow` - Start Flow system
- ⏹️ `stop-flow` - Stop Flow system

### Local vs Remote Access

**Local Only (no ngrok):**
- Faster, lower latency
- More secure
- Use: `http://localhost:8082`
- Only accessible from your machine

**With ngrok (remote):**
- Access from anywhere
- Share with team members
- Use: `https://your-ngrok-url.ngrok-free.app`
- Requires internet connection

### Troubleshooting

**Cursor can't connect:**
- Verify the HTTP server is running: `curl http://localhost:8082`
- Check ngrok is forwarding: `curl https://your-ngrok-url.ngrok-free.app`
- Ensure URL in Cursor config matches your ngrok URL

**Tools not appearing:**
- Restart Cursor after adding MCP configuration
- Check Cursor's MCP settings panel
- Verify HTTP server shows "status": "running"

**Search returns no results:**
- Ensure ChromaDB is running: `curl http://localhost:8000/api/v1/heartbeat`
- Check OCR data exists: `ls refinery/data/ocr/*.json`
- Verify MCP server can access ChromaDB (check logs)

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# OpenAI Configuration (required for audio transcription)
OPENAI_API_KEY=sk-your-api-key-here

# ChromaDB Configuration
CHROMA_HOST=localhost
CHROMA_PORT=8000

# Dashboard Configuration
DASHBOARD_HOST=0.0.0.0
DASHBOARD_PORT=8080

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

### Dashboard Configuration

The dashboard includes a comprehensive configuration panel accessible at:
**http://localhost:8080** → System Configuration

Available settings:
- **Screen Capture**: Interval, OCR processes, auto-start
- **Data Management**: Retention, file size limits, compression
- **Dashboard**: Theme, refresh rate, notifications
- **Advanced**: Logging, telemetry, experimental features

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

#### Dashboard Won't Start
```bash
# Check if port 8080 is available
lsof -i :8080

# Try a different port
cd dashboard && python app.py --port 8081
```

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

### Getting Help

- **Dashboard Logs**: Check the System Logs section in the dashboard
- **System Health**: Use the dashboard's health monitoring features
- **Error Recovery**: The system includes automatic error recovery
- **Manual Recovery**: Restart individual components as needed

## 🔄 Updates & Maintenance

### Updating Flow

```bash
# Pull latest changes
git pull origin main

# Update dependencies
cd dashboard && pip install -r requirements.txt
cd ../mcp-server && pip install -r requirements.txt
cd ../refinery && pip install -r flow-requirements.txt
```

### Data Backup

```bash
# Backup OCR data
cp -r refinery/data/ backup/data-$(date +%Y%m%d)/

# Backup ChromaDB
cp -r refinery/chroma/ backup/chroma-$(date +%Y%m%d)/
```

### Maintenance Tasks

- **Weekly**: Check disk space usage in dashboard
- **Monthly**: Review and clean old logs
- **Quarterly**: Update dependencies and restart system

## 📄 Sharable Webpages

Flow includes a website builder tool that lets you create shareable webpages from your search results and findings. Perfect for team updates, project documentation, or sharing specific discoveries.

### Features

- **Markdown Support**: Full markdown with code highlighting, tables, images, videos
- **Search Integration**: Embed Flow search results directly in pages
- **Local or Public**: Serve pages locally or share via ngrok
- **Custom Styling**: Modern, responsive design with dark/light themes
- **Easy Sharing**: Generate unique URLs for each page

### Quick Start

1. **Create a page** via Claude Desktop:
```
"Create a webpage called 'ui-progress' with title 'UI Design Progress' 
containing my search results for 'figma mobile designs' from this week"
```

2. **Access locally**:
```
http://localhost:8084/page/ui-progress
```

3. **Share publicly** (optional):
```bash
cd website-builder
python server.py --port 8084
# In another terminal:
ngrok http 8084
```

Your page is now accessible at: `https://your-ngrok-url.ngrok.io/page/ui-progress`

### Use Cases

- **Team Updates**: Weekly standup summaries with screenshots
- **Documentation**: Step-by-step guides with embedded images
- **Project Tracking**: Progress reports with activity graphs  
- **Knowledge Sharing**: Tutorials and findings with code examples

**📖 Full Documentation**: See `workspace/website-builder-tool.md` for implementation details and advanced features.

## 🎯 Roadmap

### Planned Features
- [x] Audio recording with speech-to-text integration
- [x] Sharable pages with markdown export
- [x] Team collaboration via ngrok
- [ ] Standup update automation tool
- [ ] Mobile app for remote monitoring
- [ ] Advanced analytics and insights
- [ ] API for third-party integrations
- [ ] Speaker diarization for audio transcripts

### Recent Updates
- ✅ **Audio recording and transcription** with OpenAI Whisper API
- ✅ **Unified search** across audio and OCR data with type filtering
- ✅ **Markdown storage** for audio transcripts in `refinery/data/audio/`
- ✅ Complete Python MCP server migration
- ✅ Team collaboration with ngrok and multi-instance support
- ✅ Sharable webpage builder for search results
- ✅ Modern web dashboard with real-time monitoring
- ✅ Advanced configuration system with themes
- ✅ Comprehensive error handling and recovery
- ✅ System logs viewer with filtering
- ✅ Enhanced search capabilities with date filtering

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## 📧 Support

- **Email**: joenewbry+flow@gmail.com
- **Issues**: [GitHub Issues](https://github.com/joenewbry/flow/issues)
- **Discussions**: [GitHub Discussions](https://github.com/joenewbry/flow/discussions)

---

⭐ **Star this repository** if you find it helpful! Your support helps us continue improving Flow.

![Dataflow Diagram](images/Dataflow%20Diagram.png)