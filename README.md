# Digital Surface Screen Tracking System

A comprehensive screen tracking and analysis system that captures screenshots, analyzes them with Claude AI, and stores the data in ChromaDB for semantic search and retrieval.

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
- **Automatic Summaries**: Generates hourly and daily summaries
- **Communication Style Analysis**: Learns and mimics your communication patterns
- **MCP Integration**: Compatible with Claude Desktop MCP for enhanced AI interactions

## Prerequisites

- Node.js 18+ 
- Python 3.10+ (for ChromaDB)
- Claude API key from Anthropic
- ChromaDB server (local or remote)

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
npm install screenshot-desktop @anthropic-ai/sdk chromadb dotenv date-fns

# Install ChromaDB (if running locally)
pip install chromadb
```

### 3. Environment Configuration

Create a `.env` file in the `digital-surface` directory:

```env
# Required: Your Anthropic API key
ANTHROPIC_API_KEY=your_claude_api_key_here

# Optional: ChromaDB server URL (defaults to localhost:8000)
CHROMA_SERVER_URL=http://localhost:8000

# Optional: Vector store type (defaults to simple-chroma)
VECTOR_STORE_TYPE=simple-chroma
```

### 4. Start ChromaDB Server

#### Option A: Local ChromaDB Server
```bash
# Start ChromaDB server locally
chroma run --host localhost --port 8000
```

#### Option B: Docker ChromaDB
```bash
docker run -p 8000:8000 chromadb/chroma
```

#### Option C: Remote ChromaDB
If using a remote ChromaDB server, update your `.env` file:
```env
CHROMA_SERVER_URL=https://your-chroma-server.com
```

## Usage

### 1. Start Screen Tracking

```bash
cd digital-surface
node chroma-track.js
```

The script will:
- Initialize ChromaDB connection
- Load existing screen history (if any)
- Start taking screenshots every 60 seconds
- Open a query interface for natural language queries

### 2. Query Your Screen History

Once running, you can ask questions like:
- "What was I working on yesterday?"
- "Show me all the coding sessions from last week"
- "What applications did I use today?"
- "Find all emails I wrote about project X"

### 3. MCP Integration with Claude Desktop

To connect with Claude Desktop via MCP:

1. Install `uvx`:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Add to Claude Desktop settings (`~/Library/Application Support/Claude/claude_desktop_config.json`):
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
        "http://localhost:8000"
      ]
    }
  }
}
```

3. Restart Claude Desktop and look for the 🔨 icon to access Chroma tools.

## File Structure

```
digital-surface/
├── chroma-track.js          # Main tracking script
├── chroma-vector-store.js   # ChromaDB integration
├── screenshots/             # Captured screenshots
├── screenhistory/           # JSON analysis files
├── hourly-summaries/        # Generated hourly summaries
├── daily-summaries/         # Generated daily summaries
├── automations/             # Communication style analysis
└── .env                     # Environment configuration
```

## Configuration Options

### Screenshot Interval
Modify the `waitTimeSeconds` variable in `chroma-track.js` to change capture frequency.

### Claude Model
Change the model in `processScreenshotWithClaude()` function:
- `claude-3-7-sonnet-20250219` (default)
- `claude-3-5-sonnet-20240620`
- `claude-3-opus-20240229`

### Batch Processing
Adjust `batchSize` in `loadExistingHistorySimple()` for optimal performance.

## Troubleshooting

### Common Issues

1. **ChromaDB Connection Error**
   - Ensure ChromaDB server is running
   - Check `CHROMA_SERVER_URL` in `.env`
   - Verify network connectivity

2. **Screenshot Permission Error**
   - On macOS: Grant screen recording permission to Terminal/VS Code
   - On Linux: May need additional setup for screenshot capture

3. **API Rate Limits**
   - Claude API has rate limits; consider increasing screenshot interval
   - Monitor API usage in Anthropic dashboard

4. **Memory Issues**
   - Large datasets may require more memory
   - Consider using remote ChromaDB for production

### Logs

Check logs for debugging:
- Application logs: Console output
- ChromaDB logs: Server console output
- Claude API errors: Check API response details

## Performance Optimization

### For Large Datasets

1. **Batch Processing**: Already implemented for efficient loading
2. **Deduplication**: Script automatically skips existing files
3. **Remote ChromaDB**: Use cloud-hosted ChromaDB for better performance
4. **SSD Storage**: Store data on SSD for faster I/O

### Memory Management

- Monitor memory usage during initial load
- Consider splitting large datasets across multiple collections
- Use `collection.count()` to monitor collection size

## Security Considerations

1. **API Keys**: Never commit `.env` files to version control
2. **Screenshots**: Contains sensitive information; secure storage recommended
3. **Network**: Use HTTPS for remote ChromaDB connections
4. **Permissions**: Limit access to screenshot and analysis data

## Development

### Adding New Features

1. **New Analysis Fields**: Modify the Claude prompt in `processScreenshotWithClaude()`
2. **Custom Queries**: Extend the query routing in `routeQuery()`
3. **Additional Summaries**: Add new summary types in the main loop

### Testing

```bash
# Test ChromaDB connection
node -e "const { createSimpleChromaStore } = require('./chroma-track.js'); createSimpleChromaStore().then(console.log)"

# Test screenshot capture
node -e "const screenshot = require('screenshot-desktop'); screenshot().then(console.log)"
```

## License

[Your License Here]

## Contributing

[Your Contributing Guidelines Here] 