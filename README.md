# Flow - Intelligent Screen History & Search System

[![GitHub stars](https://img.shields.io/github/stars/yourusername/flow.svg?style=social&label=Star)](https://github.com/yourusername/flow)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://python.org)

## 🎯 Overview

Flow is an intelligent screen history and search system that automatically captures, processes, and indexes your screen activity. Using advanced OCR and vector search technology, Flow enables you to search through your entire screen history using natural language queries.

![Example Usage](images/Example%20Usage.png)

**Perfect for:**
- Remembering what you worked on weeks or months ago
- Finding specific conversations, emails, or documents you viewed
- Tracking your productivity and work patterns
- Quickly locating setup instructions or configurations you've forgotten

## ✨ Key Features

### 🖥️ **Flow Dashboard** - Modern Web Interface
- **Real-time System Monitoring**: Live status of all Flow components
- **Interactive OCR Activity Graphs**: Visualize your screen activity over time
- **Advanced Search Interface**: Search your screen history with date filtering
- **System Configuration**: Comprehensive settings panel with theme support
- **System Logs Viewer**: Real-time log monitoring with filtering
- **MCP Tools Dashboard**: Monitor and test all available Claude Desktop tools

### 🔍 **Intelligent Search**
- **Vector-based Search**: Find content by meaning, not just exact text matches
- **Natural Language Queries**: Ask questions like "Find the email about the project deadline"
- **Date Range Filtering**: Search within specific time periods
- **Relevance Scoring**: Results ranked by semantic similarity

### 🤖 **Claude Desktop Integration**
- **Python MCP Server**: High-performance server with 7 powerful tools
- **Standalone Operation**: No need to launch through Claude Desktop
- **Remote System Control**: Start/stop Flow processes from Claude
- **Comprehensive Analytics**: Detailed statistics and activity reports

### 📊 **Advanced Analytics**
- **Activity Timeline**: Visual representation of your screen activity
- **Productivity Insights**: Understand your work patterns
- **Data Statistics**: Comprehensive metrics about your captured data
- **Export Capabilities**: Download logs and data for analysis

## 🚀 Quick Start

### Prerequisites
- **Python 3.10+** (tested with Python 3.13)
- **Tesseract OCR** (install via system package manager)
- **Screen capture permissions** (macOS: System Preferences > Security & Privacy > Privacy > Screen Recording)

### 1. Clone and Setup
```bash
git clone https://github.com/yourusername/flow.git
cd flow
```

### 2. Set up Screen Tracking System
```bash
cd refinery
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r flow-requirements.txt
cd ..
```

### 3. Set up Flow Dashboard
```bash
cd dashboard
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
cd ..
```

### 4. Set up Python MCP Server
```bash
cd mcp-server
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
chmod +x start.sh
cd ..
```

### 5. Start the System
```bash
# Terminal 1: Start ChromaDB server
cd refinery && source .venv/bin/activate && chroma run --host localhost --port 8000

# Terminal 2: Start screen capture
cd refinery && source .venv/bin/activate && python run.py

# Terminal 3: Start Flow Dashboard
cd dashboard && source .venv/bin/activate && python app.py

# Terminal 4: Start MCP Server (for Claude Desktop)
cd mcp-server && ./start.sh
```

### 6. Access Flow Dashboard
Open your browser and navigate to: **http://localhost:8081**

## 🌐 Flow Dashboard

The Flow Dashboard is your central control center for managing and monitoring the entire Flow system.

### Dashboard Sections

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

### Dashboard Features
- **Responsive Design**: Works on desktop and mobile devices
- **Dark/Light Themes**: Automatic system theme detection
- **Real-time Updates**: Live data refresh without page reload
- **Error Recovery**: Automatic error handling and system recovery
- **Configuration Persistence**: Settings saved across sessions

## 🤖 Claude Desktop Integration & Team Collaboration

Flow integrates seamlessly with Claude Desktop through a powerful Python MCP server. With ngrok support, you can enable team collaboration by querying multiple team members' Flow instances simultaneously.

### MCP Server Setup

1. **Add to Claude Desktop Configuration**

Edit your Claude Desktop config file and add:

```json
{
  "mcpServers": {
    "flow": {
      "command": "/Users/joe/.local/bin/uv",
      "args": [
        "--directory",
        "/Users/joe/dev/flow/mcp-server",
        "run",
        "server.py"
      ]
    }
  }
}
```

**Or use direct Python execution:**

```json
{
  "mcpServers": {
    "flow": {
      "command": "python",
      "args": ["/path/to/flow/mcp-server/server.py"],
      "cwd": "/path/to/flow/mcp-server"
    }
  }
}
```

⚠️ **Important**: Replace `/path/to/flow/` with your actual Flow installation path.

2. **Restart Claude Desktop** to load the new MCP server.

### Available MCP Tools

The Flow MCP server provides 7 powerful tools for interacting with your screen history:

#### 🔍 **search-screenshots**
Search through OCR data with natural language queries.
```
Example: "Find the email about the project deadline from last week"
```

#### ℹ️ **what-can-i-do**
Get comprehensive information about Flow capabilities and system status.
```
Example: "What can Flow do?"
```

#### 📊 **get-stats**
Retrieve detailed statistics about your OCR data and system performance.
```
Example: "Show me Flow statistics"
```

#### 📈 **activity-graph**
Generate activity timeline graphs showing capture patterns over time.
```
Example: "Generate an activity graph for the last 7 days"
```

#### 📅 **time-range-summary**
Get sampled OCR data over specific time ranges with intelligent sampling.
```
Example: "Summarize my activity from 9am to 5pm yesterday"
```

#### ▶️ **start-flow**
Start the Flow system including ChromaDB server and screen capture process.
```
Example: "Start the Flow system"
```

#### ⏹️ **stop-flow**
Stop the Flow system processes gracefully with proper cleanup.
```
Example: "Stop the Flow system"
```

### Usage Examples

**Search for specific content:**
> "Search for screenshots containing 'github.com' from yesterday"

**Get system overview:**
> "What can Flow do? Show me the current system status."

**Analyze productivity:**
> "Generate an activity graph for the past week and show me statistics"

**System control:**
> "Start Flow monitoring and show me when it's ready"

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

1. **Screen Capture**: Automatic screenshots every 60 seconds across all monitors
2. **OCR Processing**: Tesseract extracts text from screenshots in background threads
3. **Data Storage**: OCR results saved as JSON files with timestamp and screen info
4. **Vector Indexing**: ChromaDB creates semantic embeddings for intelligent search
5. **Search & Retrieval**: MCP server processes queries and returns relevant results
6. **Dashboard Monitoring**: Real-time visualization and system control

### File Structure

```
flow/
├── dashboard/                 # Web dashboard
│   ├── app.py                # FastAPI application
│   ├── lib/                  # Core libraries
│   ├── api/                  # API endpoints
│   ├── templates/            # HTML templates
│   └── static/               # CSS, JS, assets
├── mcp-server/               # Python MCP server
│   ├── server.py            # Main MCP server
│   ├── tools/               # MCP tool implementations
│   └── start.sh             # Startup script
├── refinery/                 # Screen capture system
│   ├── run.py               # Main capture script
│   ├── lib/                 # OCR and ChromaDB logic
│   └── data/                # Captured data storage
└── README.md                # This file
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

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
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

❌ **Less Effective Queries:**
- "Find the exact word 'banana' on my screen"
- "Show me all instances of the text 'ERROR 404'"

### Search Tips

1. **Use natural language**: Describe what you're looking for conversationally
2. **Include context**: Mention timeframes, people, or topics
3. **Be specific about intent**: "email about X" vs "document containing X"
4. **Use date ranges**: Narrow down searches to specific periods

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
- [ ] Audio recording with speech-to-text integration
- [x] Sharable pages with markdown export
- [x] Team collaboration via ngrok
- [ ] Standup update automation tool
- [ ] Mobile app for remote monitoring
- [ ] Advanced analytics and insights
- [ ] API for third-party integrations

### Recent Updates
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
- **Issues**: [GitHub Issues](https://github.com/yourusername/flow/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/flow/discussions)

---

⭐ **Star this repository** if you find it helpful! Your support helps us continue improving Flow.

![Dataflow Diagram](images/Dataflow%20Diagram.png)