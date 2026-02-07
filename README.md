# Flow

Searchable screen history for your entire computer. Flow takes a screenshot every minute, extracts the text, and makes it all searchable through AI.

> Built for Claude Desktop, Cursor, or any MCP-compatible client. Works great from the terminal too.

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/joenewbry/flow/main/install.sh | sh
```

Then add to your PATH and start:

```bash
export PATH="$HOME/.local/bin:$PATH"  # add to ~/.zshrc or ~/.bashrc
memex start
```

**macOS:** Requires Tesseract (`brew install tesseract`) and Screen Recording permission for your terminal in System Settings > Privacy & Security.

## Use Cases

- **Meeting recall** — "What did we discuss in the standup this morning?"
- **Link recovery** — "Find the Hacker News post about Anthropic I was reading yesterday"
- **Work summaries** — "Summarize what I worked on this week"
- **Onboarding docs** — "Create documentation for the Centurion project based on my screen history from March"
- **Context switching** — "What was I doing before lunch? Help me pick up where I left off"
- **Debug archaeology** — "Find that error message I saw in the terminal two days ago"

## How It Works

1. **Capture** — screenshots every 60 seconds, all displays
2. **Extract** — Tesseract OCR pulls text from each screenshot
3. **Index** — ChromaDB stores text as vector embeddings
4. **Search** — semantic search via MCP tools or the CLI

Everything stays local on your machine.

## CLI

```bash
memex status          # health check
memex doctor          # full diagnostics
memex ask "query"     # AI-powered natural language search
memex chat            # interactive chat
memex search "query"  # direct text search
memex stats           # activity statistics
memex start / stop    # control the capture daemon
memex watch           # live view of captures
memex auth login      # configure API keys (Anthropic/OpenAI)
```

## MCP Integration

### Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

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

Replace `YOUR_USERNAME` with your macOS username and restart Claude Desktop.

### Cursor

Start the HTTP server and expose via NGROK, then add to `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "Memex": {
      "url": "https://YOUR_NGROK_URL.ngrok-free.dev/sse"
    }
  }
}
```

## License

MIT — see [LICENSE](LICENSE) for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/joenewbry/flow/issues)
- **Email**: joenewbry+flow@gmail.com
