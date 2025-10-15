# Markdown Page Rendering - Implementation Summary

## What Was Fixed

The Flow MCP HTTP server now serves **both** MCP tools and beautiful markdown-rendered webpages from a single unified server.

## Changes Made

### 1. MCP Server Tools (`mcp-server/tools/website.py`)
- **Saves both `.md` and `.html` files** when creating pages
- Markdown source is preserved in `.md` files
- HTML is generated for backward compatibility
- Updated all URLs to point to port `8082` (HTTP MCP server)

### 2. HTTP MCP Server (`mcp-server/http_server.py`)
- Added webpage serving endpoints:
  - `GET /pages` - List all available pages (both .md and .html)
  - `GET /page/{page_name}` - Serve a specific page
- **Renders markdown on-the-fly** with beautiful styling
- Serves static assets (CSS, JS, images) from `/static`
- Markdown features supported:
  - Fenced code blocks
  - Tables
  - Lists (ordered and unordered)
  - Blockquotes
  - Images
  - Links with hover effects

### 3. Beautiful Markdown Styling (`website-builder/static/css/styles.css`)
Inspired by BearBlog, the styling includes:
- **Responsive typography** with proper line heights
- **Clean spacing** using logical properties (margin-block, padding-inline)
- **Code highlighting** with syntax-aware coloring
- **Link styling** with underlines and hover effects
- **Table styling** with alternating row colors
- **Blockquote styling** with left border and background
- **Dark mode support** via CSS variables
- **Mobile responsive** design

### 4. Dependencies Added
Added to `mcp-server/pyproject.toml` via uv:
- `markdown>=3.9` - For rendering markdown to HTML
- `jinja2>=3.1.6` - Template engine (already used)
- `fastapi>=0.119.0` - Web framework for HTTP server
- `uvicorn` - ASGI server

## How It Works

### Page Creation Flow
1. **MCP tool called**: `create-webpage` with markdown content
2. **Files saved**: 
   - `website-builder/pages/{page-name}.md` (source)
   - `website-builder/pages/{page-name}.html` (rendered)
3. **Access URL**: `http://localhost:8082/page/{page-name}`

### Page Serving Flow
1. **Request received**: `GET /page/{page-name}`
2. **Markdown check**: Looks for `.md` file first
3. **Render on-the-fly**: Converts markdown to HTML with styling
4. **Fallback**: If no `.md`, serves `.html` file
5. **Response**: Beautiful HTML page with proper styling

## Server Architecture

```
HTTP MCP Server (port 8082)
├── MCP Tools (/tools/*)
│   ├── search-screenshots
│   ├── get-stats
│   ├── activity-graph
│   ├── time-range-summary
│   ├── create-webpage  ← Creates .md + .html
│   └── ... other tools
│
└── Webpage Serving
    ├── /pages - List all pages
    ├── /page/{name} - Render markdown or serve HTML
    └── /static/* - CSS, JS, images
```

## Usage Examples

### Creating a Page (via MCP tool)
```json
{
  "tool": "create-webpage",
  "arguments": {
    "page_name": "my-summary",
    "title": "My Work Summary",
    "content": "# My Work Summary\n\nThis is **markdown** content..."
  }
}
```

### Accessing Pages
- **Local**: `http://localhost:8082/page/my-summary`
- **Via ngrok**: `https://your-ngrok-url.ngrok.io/page/my-summary`
- **List all**: `http://localhost:8082/pages`

### Starting the Server
```bash
cd /Users/joe/dev/flow/mcp-server
.venv/bin/python3 http_server.py --port 8082
```

### With ngrok (for sharing)
```bash
ngrok http 8082
```

## Benefits

1. **Single Server** - No need for separate website builder server
2. **Markdown Source** - Edit-friendly `.md` files preserved
3. **Beautiful Rendering** - BearBlog-inspired clean design
4. **On-the-Fly** - Markdown rendered when requested (no rebuild needed)
5. **Dark Mode** - Automatic dark mode support
6. **Mobile Friendly** - Responsive design
7. **Fast** - Static assets cached, markdown cached by browser

## File Locations

- **Pages**: `/Users/joe/dev/flow/website-builder/pages/*.md`
- **Static Assets**: `/Users/joe/dev/flow/website-builder/static/`
- **CSS**: `/Users/joe/dev/flow/website-builder/static/css/styles.css`
- **Server**: `/Users/joe/dev/flow/mcp-server/http_server.py`
- **Tool**: `/Users/joe/dev/flow/mcp-server/tools/website.py`

## Markdown Features Supported

- ✅ **Headings** (H1-H6) with proper sizing
- ✅ **Paragraphs** with comfortable line height
- ✅ **Links** with underline and hover effects  
- ✅ **Bold** and *italic* text
- ✅ **Code blocks** with syntax highlighting support
- ✅ **Inline code** with accent color
- ✅ **Lists** (ordered and unordered)
- ✅ **Tables** with alternating row colors
- ✅ **Blockquotes** with left border
- ✅ **Images** (responsive and centered)
- ✅ **Horizontal rules**
- ✅ **HTML entities** (proper escaping)

## Troubleshooting

### Server won't start
```bash
# Check if port is in use
lsof -i :8082

# View server logs
tail -f /tmp/flow-http-server.log

# Verify dependencies
cd /Users/joe/dev/flow/mcp-server
.venv/bin/python3 -c "import fastapi, markdown, uvicorn; print('OK')"
```

### Page not found
```bash
# List all pages
curl http://localhost:8082/pages

# Check file exists
ls -la /Users/joe/dev/flow/website-builder/pages/
```

### CSS not loading
- Ensure static files are mounted: Check `STATIC_DIR` exists
- Check browser console for 404 errors
- Verify path: Should be `/static/css/styles.css`

## Next Steps

The system is now ready to:
1. ✅ Create markdown pages via MCP tools
2. ✅ Serve them with beautiful styling
3. ✅ Share via ngrok
4. ✅ Use in Claude Desktop or Cursor

Both the MCP server and webpage serving are unified in one server on port 8082!

