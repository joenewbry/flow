# Simple Flow MCP System - Implementation Plan

## Overview

This plan outlines the creation of a streamlined Flow MCP system from scratch, focusing on simplicity, minimal file count, and direct integration with Anthropic's API for summarization. The system will capture screenshots every second, store them in ChromaDB, and provide MCP tools for intelligent work activity analysis.

## Project Structure

```
simple-flow-mcp/
├── venv/                           # Virtual environment
├── data/
│   ├── screenshots/                # Raw screenshot storage
│   ├── screen_history/             # JSON files with analysis
│   └── chroma/                     # ChromaDB database
├── src/
│   ├── __init__.py
│   ├── screenshot_capture.py       # Screenshot capture + AI analysis
│   ├── mcp_server.py              # MCP server with all tools
│   └── chroma_manager.py          # ChromaDB operations
├── start.py                       # Main startup script
├── requirements.txt               # Dependencies
├── .env.example                   # Environment variables template
└── README.md                      # Documentation
```

**Total Core Files: 8 files** (excluding virtual env and data directories)

## Implementation Plan

### Phase 1: Environment Setup & Dependencies

#### Virtual Environment Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

#### Dependencies (`requirements.txt`)
```
# MCP Framework
mcp==1.0.0

# Database & Vector Search
chromadb==0.4.18

# AI & API
anthropic==0.34.0
python-dotenv==1.0.0

# Screenshot & Image Processing
Pillow==10.1.0
mss==9.0.1

# Utilities
asyncio-throttle==1.0.2
click==8.1.7
```

#### Environment Variables (`.env`)
```bash
ANTHROPIC_API_KEY=your_api_key_here
CHROMA_HOST=localhost
CHROMA_PORT=8000
SCREENSHOT_INTERVAL=1
DATA_PATH=./data
```

### Phase 2: Core Components

#### 1. Screenshot Capture & Analysis (`src/screenshot_capture.py`)

**Responsibilities:**
- Capture screenshots every second
- Analyze screenshots with Anthropic's Claude
- Store results as JSON in `screen_history/`
- Add to ChromaDB for vector search

**Key Features:**
```python
class ScreenshotCapture:
    def __init__(self):
        self.anthropic_client = Anthropic()
        self.chroma_manager = ChromaManager()
        self.capture_interval = 1  # seconds
        
    async def capture_and_analyze(self):
        """Main loop: capture → analyze → store"""
        
    async def analyze_screenshot(self, image_path: str) -> dict:
        """Use Anthropic API to analyze screenshot"""
        
    async def store_analysis(self, analysis: dict):
        """Store in both JSON file and ChromaDB"""
```

**Screenshot Analysis Prompt:**
```python
ANALYSIS_PROMPT = """
Analyze this screenshot and provide:
1. Active application name
2. Brief summary of what the user is doing
3. Task category (coding, communication, research, etc.)
4. Productivity score (1-10)
5. Any visible text content (if relevant)

Return as JSON format:
{
  "active_app": "...",
  "summary": "...", 
  "task_category": "...",
  "productivity_score": 8,
  "extracted_text": "..."
}
"""
```

#### 2. ChromaDB Manager (`src/chroma_manager.py`)

**Responsibilities:**
- Initialize ChromaDB collections
- Store screenshot analyses with vector embeddings
- Provide search functionality
- Handle database operations

**Key Features:**
```python
class ChromaManager:
    def __init__(self):
        self.client = chromadb.HttpClient(host="localhost", port=8000)
        self.collection = None
        
    async def init_database(self):
        """Initialize ChromaDB and create collections"""
        
    async def store_analysis(self, analysis_data: dict):
        """Store analysis with vector embedding"""
        
    async def search_activities(self, query: str, limit: int = 10, 
                               time_filter: dict = None) -> list:
        """Vector search through screen history"""
        
    async def get_time_range_data(self, start_time: str, end_time: str) -> list:
        """Get all activities in time range"""
```

#### 3. MCP Server (`src/mcp_server.py`)

**Responsibilities:**
- Implement MCP protocol
- Provide 4 main tools
- Handle tool requests
- Interface with ChromaDB and Anthropic

**MCP Tools Implementation:**

##### Tool 1: `get_daily_work_summary`
```python
async def get_daily_work_summary(date: str = None) -> dict:
    """
    Get comprehensive daily work summary
    1. Query ChromaDB for all activities in date range
    2. Group activities by hour  
    3. Use Anthropic to summarize each hour
    4. Aggregate into daily overview
    """
```

##### Tool 2: `generate_standup_notes`
```python
async def generate_standup_notes(format: str = "standard") -> dict:
    """
    Generate standup notes with Yesterday/Today sections
    1. Get activities for yesterday and today
    2. Use Anthropic to create bullet-point summaries
    3. Format into standup template
    """
```

##### Tool 3: `search_activity_history`
```python
async def search_activity_history(query: str, limit: int = 10,
                                 time_filter: str = None) -> dict:
    """
    Search through activity history using vector search
    1. Perform ChromaDB vector search
    2. Apply time filters if specified
    3. Return relevant matches with context
    """
```

##### Tool 4: `get_time_range_summary`
```python
async def get_time_range_summary(start_time: str, end_time: str,
                                granularity: str = "auto") -> dict:
    """
    Generate summary for custom time ranges
    1. Validate time range
    2. Get activities from ChromaDB
    3. Use Anthropic for intelligent summarization
    4. Return structured summary
    """
```

#### 4. Main Startup Script (`start.py`)

**Responsibilities:**
- Start ChromaDB server
- Launch screenshot capture process
- Start MCP server
- Handle graceful shutdown

```python
#!/usr/bin/env python3
"""
Simple Flow MCP System Startup Script
Launches all required services in the correct order
"""

import asyncio
import subprocess
import signal
import sys
from pathlib import Path

class SimpleFlowMCP:
    def __init__(self):
        self.processes = []
        self.running = True
        
    async def start_chroma_db(self):
        """Start ChromaDB server"""
        
    async def start_screenshot_capture(self):
        """Start screenshot capture process"""
        
    async def start_mcp_server(self):
        """Start MCP server"""
        
    async def run(self):
        """Main execution flow"""
        print("🚀 Starting Simple Flow MCP System...")
        
        # 1. Ensure data directories exist
        # 2. Start ChromaDB
        # 3. Initialize database collections
        # 4. Start screenshot capture
        # 5. Start MCP server
        
    def shutdown(self):
        """Graceful shutdown"""

if __name__ == "__main__":
    system = SimpleFlowMCP()
    
    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        system.shutdown()
        sys.exit(0)
        
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        asyncio.run(system.run())
    except KeyboardInterrupt:
        system.shutdown()
```

### Phase 3: Documentation

#### README.md Structure

```markdown
# Simple Flow MCP System

Intelligent work activity tracking with MCP tools for seamless integration with Claude and Cursor.

## Installation

### Prerequisites
- Python 3.9+
- Anthropic API key

### Setup
```bash
# Clone and setup
git clone <repo>
cd simple-flow-mcp
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your Anthropic API key

# Start the system
python start.py
```

## Usage

### MCP Tools Available

#### 1. Daily Work Summary
**Tool:** `get_daily_work_summary`
**Purpose:** Get comprehensive summary of daily activities
**Parameters:**
- `date` (optional): YYYY-MM-DD format, defaults to today

**Example:**
```
Human: What did I work on today?
Claude: [Uses get_daily_work_summary tool]
```

#### 2. Standup Notes Generator  
**Tool:** `generate_standup_notes`
**Purpose:** Generate structured standup notes with Yesterday/Today sections
**Parameters:**
- `format` (optional): "standard", "brief", "detailed"

**Example:**
```
Human: Generate my standup notes
Claude: [Uses generate_standup_notes tool]
```

#### 3. Activity History Search
**Tool:** `search_activity_history` 
**Purpose:** Search through work history using natural language
**Parameters:**
- `query` (required): Search query
- `limit` (optional): Max results (default: 10)
- `time_filter` (optional): "today", "this-week", "this-month"

**Example:**
```
Human: What's that website about drone racing?
Claude: [Uses search_activity_history with query="drone racing website"]
```

#### 4. Time Range Summary
**Tool:** `get_time_range_summary`
**Purpose:** Generate summaries for custom time periods
**Parameters:**
- `start_time` (required): ISO 8601 timestamp
- `end_time` (required): ISO 8601 timestamp  
- `granularity` (optional): "auto", "hour", "day"

### Integration with Claude/Cursor

Add to your MCP configuration:
```json
{
  "mcpServers": {
    "simple-flow": {
      "command": "python",
      "args": ["/path/to/simple-flow-mcp/src/mcp_server.py"],
      "env": {
        "ANTHROPIC_API_KEY": "your_key_here"
      }
    }
  }
}
```

## Future Features

### Remote Access
- **ngrok Integration**: Enable remote access to activity data from other computers
- **Web Dashboard**: Browser-based interface for activity visualization
- **Multi-device Sync**: Synchronize activity data across multiple machines

### Feedback & Improvement
- **suggest_improvement Tool**: Quick feedback mechanism for workflow optimization
- **Activity Pattern Recognition**: AI-powered insights into productivity patterns  
- **Custom Productivity Metrics**: User-defined metrics and goals tracking

### Enhanced Analysis
- **Team Collaboration**: Share activity summaries with team members
- **Project Time Tracking**: Automatic project categorization and time allocation
- **Focus Session Analysis**: Deep-dive analysis of focused work periods
- **Distraction Detection**: Identify and categorize productivity interruptions

### Data & Privacy
- **Data Export**: Export activity data in various formats (JSON, CSV, PDF reports)
- **Privacy Controls**: Fine-grained control over what data is captured and analyzed
- **Local LLM Option**: Alternative to Anthropic API for fully local processing
```

## Implementation Timeline

### Week 1: Core Infrastructure
- Set up virtual environment and dependencies
- Implement `screenshot_capture.py` with basic Anthropic integration
- Create `chroma_manager.py` with database operations
- Build `start.py` script with service orchestration

### Week 2: MCP Tools
- Implement all 4 MCP tools in `mcp_server.py`
- Test tool functionality with sample data
- Ensure proper error handling and validation

### Week 3: Integration & Testing
- Test complete system integration
- Verify MCP protocol compliance
- Test with Claude Desktop and Cursor
- Performance optimization

### Week 4: Documentation & Polish
- Complete README.md with examples
- Add code comments and docstrings
- Create usage examples and troubleshooting guide
- Final testing and bug fixes

## Technical Considerations

### Performance Optimizations
- **Async Processing**: All I/O operations use async/await
- **Throttled Screenshots**: Configurable capture intervals
- **Efficient Vector Search**: Optimized ChromaDB queries
- **Response Caching**: Cache frequent summaries to reduce API calls

### Error Handling
- **Graceful Degradation**: System continues if one component fails
- **API Rate Limiting**: Handle Anthropic API rate limits
- **Storage Failures**: Fallback mechanisms for data storage issues
- **Network Resilience**: Handle ChromaDB connection issues

### Security & Privacy
- **Local Data Storage**: All screenshots and analyses stored locally
- **API Key Security**: Secure handling of Anthropic API keys
- **Data Encryption**: Optional encryption for sensitive data
- **Access Controls**: Basic authentication for MCP server access

### Scalability Considerations
- **Modular Architecture**: Easy to add new MCP tools
- **Database Optimization**: Efficient indexing and querying
- **Resource Management**: Monitor memory and storage usage
- **Background Processing**: Non-blocking screenshot analysis

This plan provides a clear roadmap for creating a simple, effective MCP system that meets all requirements while maintaining flexibility for future enhancements.
