# Flow MCP

[![GitHub stars](https://img.shields.io/github/stars/yourusername/flow.svg?style=social&label=Star)](https://github.com/yourusername/flow)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://python.org)

## Simple Vector-Based Screen History Search

![Example Usage](images/Example%20Usage.png)
I wanted to have a simple history of what I've worked on. A year from now I'd like to be able to know what things I've been doing and at work people ask me for details on how to setup things I've long since forgotten about. 

Now I can quickly remind myself of the context. :)

This is a [vector search](https://en.wikipedia.org/wiki/Vector_database) system. So queries searching for specific terms may or may not be handled as well as queries for general terms.

Ex of unsupported query: Find the last time the word *Banana* showed up on my screen.
Ex of supported query: I drafted an email to Emily Smith about a month ago about dog sitting. Can you remind me what we talked about?

A quick note on security: The OCR process happens on your machine and ChromaDB runs locally. But when you use an MCP client to interact with flow the returned results may be processed off your machine. So at that point it's up to you to decide what frontend client you want to use and what data you want to share with them.

RetellAI 

If you have feedback or comments please email joenewbry+flow@gmail.com

## Installation

### Prerequisites
- **Python 3.10+** (tested with Python 3.13.7)
- **Node.js 16+** (for MCP server)
- **Tesseract OCR** (install via system package manager)
- **ChromaDB server** (running on localhost:8000)
- **Screen capture permissions** (macOS: System Preferences > Security & Privacy > Privacy > Screen Recording)

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/flow.git
   cd flow
   ```

2. **Set up Python environment for screen tracking**
   ```bash
   cd refinery
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r flow-requirements.txt
   cd ..
   ```

3. **Set up MCP server environment**
   ```bash
   cd mcp-flow-node
   npm install
   cd ..
   ```

4. **Start ChromaDB server in /refinery folder** (in a separate terminal)
   ```bash
   cd refinery && chroma run --host localhost --port 8000
   ```

5. **Run the Flow tracker**
   ```bash
   cd refinery
   python run.py
   ```

### Claude Desktop MCP Configuration

To integrate Flow with Claude Desktop, add the following configuration to your Claude Desktop config file:

```json
{
  "mcpServers": {
    "flow": {
      "command": "node",
      "args": [
        "/Users/joe/dev/flow/mcp-flow-node/server.js"
      ],
      "cwd": "/Users/joe/dev/flow"
    }
  }
}
```

^^ You'll need to update the paths above with your paths.

For detailed MCP setup instructions, see the [Claude Desktop MCP guide](https://modelcontextprotocol.io/docs/develop/connect-local-servers).

## Architecture Guide
**Screen Tracking Process:**
- Flow automatically detects all available monitors/displays
- Screen naming convention: `screen_0` (primary), `screen_1` (secondary), `screen_N` (additional)
- Screenshots captured every 60 seconds. This balances usefulness later with space and CPU processing constraints. 
- OCR text extraction via Tesseract happens in background threads
- Data stored as `{timestamp}_{screen_name}.json` files

**ChromaDB Integration:**
- All OCR text content stored in "screen_ocr_history" collection
- Semantic embeddings enable intelligent search across captured content
- Both new captures and existing OCR files are automatically indexed
- HTTP client connects to ChromaDB server on localhost:8000

**MCP Server Features:**
- Provides `search-screenshots` tool for semantic text search
- Integrates with Claude Desktop for natural language queries. Feel free to use it with other MCP clients

**Data Flow:**
1. Screenshots captured → OCR processed → JSON saved → ChromaDB indexed
2. Claude queries → MCP server → ChromaDB search → Results returned
3. All processing happens automatically in the background

![Dataflow Diagram](images/Dataflow%20Diagram.png)
![Example Usage](images/Example%20Usage.png)
![Dataflow Diagram](images/Example%20Usage.png)


## Feature List
- [ ] Add audio recording via audio to text saving and search
- [ ] Add support for creating sharable pages with markdown information. This will be flow.digitalsurface.com/{your-unique-page-id}.md. This makes sharing quick and easy and doesn't require someone to use a specific frontend client
- [ ] Standup update tool added
- [ ] Support for Visual Studio Code MCP Client (if possible)
- [ ] Clearer / simpler install script

If you'd like specific features email joenewbry+flow@gmail.com
---

⭐ **Star this repository** if you find it helpful! And when I reach 100 stars I'll add a fun graph that shows # of stars... yes this is a vanity metric :)
