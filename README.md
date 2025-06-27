# Digital Surface Screen Tracking System

A comprehensive screen tracking and analysis system that captures screenshots, analyzes them with Claude AI, and stores the data in ChromaDB for semantic search and retrieval using Claude's Desktop Client.

Some questions you can answer with Claude Desktop + Chroma integration:

- "Update the README.md based on the work I've done today."
- "Write a summary for my daily time tracking of what I've worked on including my JIRA tickets"

## Overview

The system consists of three main components:
- **Automatic Screenshot Capture**: Takes screenshots every 60 seconds and analyzes them with Claude AI
- **ChromaDB Vector Storage**: Stores screen analysis data for semantic search and retrieval
- **Claude MCP Integration**: Allows Claude Desktop to query your screen history through MCP tools

## Features

- **Automatic Screenshot Capture**: Takes screenshots every 60 seconds
- **AI Analysis**: Uses Claude AI to analyze screenshots and extract:
  - Active application
  - Summary of activities
  - Extracted text content
  - Task categories
  - Productivity scores
  - User-generated text
- **Vector Storage**: Stores data in ChromaDB for semantic search
- **Query Interface**: Natural language querying of your screen history
- **MCP Integration**: Compatible with Claude Desktop MCP for enhanced AI interactions

## Prerequisites

- Node.js 18+
- Python 3.8+ (for ChromaDB)
- Claude API key from Anthropic
- Claude Desktop App (for MCP integration)

## Installation

### 1. Clone and Setup

```bash
git clone <your-repo>
cd digital-surface
npm install
```

### 2. Install Dependencies

```bash
# Install Node.js dependencies
npm install screenshot-desktop @anthropic-ai/sdk chromadb chromadb-default-embed dotenv date-fns

# Install ChromaDB Python package
pip install chromadb
```

### 3. Environment Configuration

Create a `.env` file in the `digital-surface` directory:

```env
# Required: Your Anthropic API key
ANTHROPIC_API_KEY=your_claude_api_key_here

# Optional: ChromaDB server settings (defaults to localhost:8000)
CHROMA_HOST=localhost
CHROMA_PORT=8000
CHROMA_SSL=false
```

### 4. Configure Package.json for ES6 Modules

Ensure your `package.json` includes:

```json
{
  "type": "module",
  "dependencies": {
    "@anthropic-ai/sdk": "^latest",
    "chromadb": "^latest",
    "chromadb-default-embed": "^latest",
    "screenshot-desktop": "^latest",
    "dotenv": "^latest",
    "date-fns": "^latest"
  }
}
```

## Usage

### 1. Start ChromaDB Server
```bash
# Option A: Start ChromaDB server locally
chroma run --host localhost --port 8000

# Option B: Use Docker
docker run -p 8000:8000 chromadb/chroma
```

### 2. Start Screen Tracking

```bash
cd digital-surface
node chroma-track.js
```

The script will:
- Initialize ChromaDB connection and create "screen_history" collection
- Load existing screen history data into memory
- Start taking screenshots every 60 seconds
- Process each screenshot with Claude AI for analysis
- Store results in both JSON files and ChromaDB vector store

### 3. Query Your Screen History

Once running, you can query your data through Claude Desktop MCP integration or programmatically:

Examples of what you can ask:
- "What was I working on today?"
- "Show me all the coding sessions from this week"
- "What applications did I use most?"
- "Find activities related to Chroma setup"
- "Update the README.md based on the work I've done today."
- "Write a summary for my daily time tracking of what I've worked on including my JIRA tickets"

### 4. MCP Integration with Claude Desktop

To connect with Claude Desktop via MCP:

1. **Install uvx** (if not already installed):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. **Configure Claude Desktop** by editing your config file:

**On macOS:**
```bash
~/Library/Application Support/Claude/claude_desktop_config.json
```

**On Windows:**
```bash
%APPDATA%/Claude/claude_desktop_config.json
```

**On Linux:**
```bash
~/.config/Claude/claude_desktop_config.json
```

Add the Chroma MCP configuration:

```json
{
  "mcpServers": {
    "chroma": {
      "command": "uvx",
      "args": [
        "chroma-mcp",
        "--client-type",
        "http",
        "--host",
        "http://localhost:8000",
        "--port",
        "8000",
        "--ssl",
        "false"
      ]
    }
  }
}
```

3. **Restart Claude Desktop** and look for the 🔨 icon to access Chroma tools.

## File Structure

```
digital-surface/
├── chroma-track.js              # Main tracking script
├── chroma-vector-store.js       # ChromaDB integration utilities
├── package.json                 # Node.js dependencies and configuration
├── .env                         # Environment variables (API keys, etc.)
├── screenshots/                 # Captured screenshot images (.png files)
├── screenhistory/              # JSON analysis files from Claude AI
└── claude_desktop_config.json  # Claude Desktop MCP configuration
```

## Configuration Options

### Screenshot Interval
Modify the `waitTimeSeconds` variable in `chroma-track.js`:
```javascript
const waitTimeSeconds = 60; // Capture every 60 seconds
```

### Claude Model Selection
The system uses Claude for screenshot analysis. You can modify the model in the `processScreenshotWithClaude()` function:
- `claude-3-5-sonnet-20240620` (recommended for balance of speed/quality)
- `claude-3-opus-20240229` (highest quality, slower)

### ChromaDB Collection Settings
The system creates a "screen_history" collection by default. You can modify collection settings in `chroma-vector-store.js`.

## Troubleshooting

### Common Issues

1. **ChromaDB Connection Error**
   - Ensure ChromaDB server is running on localhost:8000
   - Check if port 8000 is available: `lsof -i :8000`
   - Verify CHROMA_HOST and CHROMA_PORT in `.env`

2. **ES6 Import/Export Errors**
   - Ensure `"type": "module"` is in your package.json
   - Check that all imports use `.js` extensions for local files
   - Verify Node.js version is 18+

3. **Screenshot Permission Error**
   - **macOS**: Grant screen recording permission to Terminal/VS Code in System Preferences > Security & Privacy > Privacy > Screen Recording
   - **Linux**: May need additional setup for screenshot capture
   - **Windows**: Check if running with appropriate permissions

4. **Claude API Errors**
   - Verify ANTHROPIC_API_KEY is set correctly in `.env`
   - Check API usage limits in Anthropic dashboard
   - Monitor rate limits (the system processes one screenshot per minute)

5. **MCP Connection Issues**
   - Restart Claude Desktop after changing configuration
   - Check that uvx is properly installed
   - Verify the MCP server configuration syntax in claude_desktop_config.json

6. **JSON Parsing Error in Claude Desktop**
   - Common error: "Expected property name or '}' in JSON at position 22"
   - Validate your claude_desktop_config.json syntax
   - Remove trailing commas and ensure proper JSON formatting

### Performance Optimization

1. **For Large Screenshot Collections**:
   - The system automatically loads existing files in batches
   - Consider using an SSD for better I/O performance
   - Monitor memory usage during initial data loading

2. **ChromaDB Performance**:
   - Use a dedicated ChromaDB server for production
   - Consider cloud-hosted ChromaDB for better scalability
   - Monitor collection size with `collection.count()`

3. **Claude API Optimization**:
   - Adjust screenshot interval based on your needs
   - Monitor token usage in Anthropic dashboard
   - Consider using smaller Claude models for faster processing

## Security Considerations

1. **API Keys**: Never commit `.env` files to version control
2. **Screenshots**: Contains sensitive information; ensure secure storage
3. **Network**: Use HTTPS for remote ChromaDB connections if applicable
4. **Permissions**: Limit access to screenshot and analysis data
5. **Local Storage**: Screenshots and analysis data are stored locally by default

## Development and Customization

### Adding New Analysis Fields

Modify the Claude prompt in `processScreenshotWithClaude()` function in `chroma-track.js` to extract additional information from screenshots.

### Custom Query Types

The system supports natural language queries through the ChromaDB vector search. You can extend functionality by adding custom query handlers.

### Integration with Other Tools

The system is designed to be extensible. You can add integrations with:
- Git repositories for code change tracking
- Calendar applications for meeting correlation
- Task management systems
- Time tracking tools

## Example Queries

Once your system is running and has collected data, you can query it through Claude Desktop:

- "What did I work on today?"
- "Show me all screenshots where I was coding"
- "Find activities related to Chroma setup"
- "What applications did I use most this week?"
- "Show me when I was working on JavaScript projects"

## Technical Architecture

The system consists of:
1. **Screenshot Capture**: Uses `screenshot-desktop` npm package
2. **AI Analysis**: Claude AI processes screenshots to extract structured data
3. **Vector Storage**: ChromaDB stores analysis results for semantic search
4. **MCP Integration**: Allows Claude Desktop to query the stored data
5. **File Storage**: Local storage of screenshots and JSON analysis files

## Performance Notes

- **Memory Usage**: Initial loading of existing history may use significant memory
- **Storage**: Screenshots and JSON files will accumulate over time
- **API Usage**: One Claude API call per screenshot (60 seconds interval by default)
- **ChromaDB**: Vector embeddings are generated for all analysis text

## Next Steps

After getting the basic system running:
1. Customize the analysis prompts for your specific use cases
2. Set up automated backups of your screenshot and analysis data
3. Consider implementing data retention policies
4. Explore advanced ChromaDB features like metadata filtering
5. Add custom analysis for specific applications or workflows

This system provides a foundation for comprehensive activity tracking and can be extended based on your specific needs and workflow patterns.