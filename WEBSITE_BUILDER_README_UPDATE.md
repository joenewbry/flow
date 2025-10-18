# Website Builder Server Documentation Added

## Summary

Added comprehensive documentation for the website-builder Python server to the main README under Optional Setup → Website Builder & Ngrok Sharing.

## What Was Added

### Section: 🌐 Website Builder & Ngrok Sharing

The section now includes:

1. **Creating Webpages** - How to use the MCP tool
2. **Option 1: HTTP MCP Server** (Recommended)
   - Serves both MCP tools AND webpages
   - Use for remote MCP access + page sharing
3. **Option 2: Website Builder Server** (Simpler) ← NEW!
   - Standalone server just for webpages
   - Use for simple page sharing

## Website Builder Server Details

### What It Does
- Serves static webpages from `website-builder/pages/`
- Renders markdown files on-the-fly
- No MCP functionality (simpler alternative)
- Beautiful BearBlog-inspired styling

### How to Use

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

### Features Listed
- 📝 Renders markdown files on-the-fly
- 🎨 Beautiful BearBlog-inspired styling
- 📱 Responsive mobile design
- 🌓 Automatic dark/light theme
- 🔗 Simple, shareable URLs

### Page Management
```bash
# List all pages
curl http://localhost:8084/

# View specific page
open http://localhost:8084/page/my-summary

# Pages are stored as .md files
ls website-builder/pages/
```

## Two Server Options Explained

### Option 1: HTTP MCP Server (port 8082)
**Use when:**
- You want remote MCP access (via ngrok)
- You need both MCP tools AND webpage serving
- Team collaboration with multiple Flow instances

**Capabilities:**
- ✅ MCP tools (search-screenshots, get-stats, etc.)
- ✅ Webpage serving
- ✅ Remote Claude/Cursor access via ngrok

### Option 2: Website Builder Server (port 8084)
**Use when:**
- You just want to share webpages
- Don't need MCP functionality
- Want a simpler setup

**Capabilities:**
- ❌ No MCP tools
- ✅ Webpage serving
- ✅ Markdown rendering
- ✅ Ngrok sharing

## Benefits of Documentation

1. **Clear Choice** - Users understand which server to use
2. **Simple Alternative** - Website builder server is easier for just page sharing
3. **Complete Setup** - All commands provided
4. **Feature Clarity** - Lists what each server does
5. **Located Properly** - Under Optional Setup where it belongs

## File Structure

```
flow/
├── mcp-server/
│   └── http_server.py      # Option 1: Full-featured (MCP + pages)
└── website-builder/
    ├── server.py            # Option 2: Simple (pages only)
    ├── pages/              # Markdown and HTML pages
    ├── static/             # CSS, JS, assets
    └── templates/          # HTML templates
```

## Workflow

```
1. Create pages via MCP tool in Claude/Cursor
   ↓
2. Pages saved as .md in website-builder/pages/
   ↓
3. Choose server option:
   
   Option 1 (Full):              Option 2 (Simple):
   http_server.py                server.py
   port 8082                     port 8084
   MCP + Pages                   Pages only
   ↓                            ↓
4. Expose via ngrok
   ↓
5. Share public URL
```

## Example Usage

### Create a Page
```
In Claude/Cursor:
"Create a webpage called 'team-standup' with title 'Monday Standup Notes' 
containing screenshots from this morning's meeting"
```

### Serve It (Option 2 - Simple)
```bash
cd website-builder
python3 server.py --port 8084
```

### Share It
```bash
# In another terminal
ngrok http 8084

# Share the URL
https://abc123.ngrok-free.app/page/team-standup
```

## Where in README

**Location:** Optional Setup → Website Builder & Ngrok Sharing
**Line:** ~156
**Section Structure:**
```
## 🎛️ Optional Setup
  ├── 📊 Flow Dashboard (Web UI)
  ├── 🎙️ Audio Recording & Transcription
  └── 🌐 Website Builder & Ngrok Sharing  ← Updated!
      ├── Creating Webpages
      ├── Option 1: HTTP MCP Server
      └── Option 2: Website Builder Server  ← New!
```

## Notes

- Both servers serve the same pages from `website-builder/pages/`
- HTTP MCP Server is more powerful but requires MCP setup
- Website Builder Server is simpler for basic page sharing
- Both support ngrok for public access
- Both render markdown on-the-fly with beautiful styling

