# Markdown-Only Pages Update

## Summary

Updated the website tool to create **only** markdown files (`.md`), not HTML files. Servers now render markdown on-the-fly.

## Changes Made

### File: `mcp-server/tools/website.py`

#### 1. `create_page()` Method
**Before:**
- Converted markdown to HTML
- Rendered Jinja2 template
- Saved both `.md` and `.html` files
- Complex HTML generation logic

**After:**
- Saves only `.md` file
- Prepends title as H1 if needed
- Search results appended as markdown
- Server renders on-the-fly

**Code simplified from ~40 lines to ~30 lines**

#### 2. `list_pages()` Method
**Before:** `self.pages_dir.glob("*.html")`  
**After:** `self.pages_dir.glob("*.md")`

#### 3. `delete_page()` Method  
**Before:** Deleted `.html` files  
**After:** Deletes `.md` files

#### 4. `get_page_url()` Method
**Before:** Checked for `.html` files  
**After:** Checks for `.md` files

## Benefits

### ✅ Simpler
- No HTML generation in tool
- No Jinja2 template rendering
- Just save raw markdown

### ✅ Single Source of Truth
- Markdown is the source
- No duplicate HTML files
- Easy to edit pages manually

### ✅ On-the-Fly Rendering
- Servers render when requested
- Changes to styling apply to all pages
- No need to regenerate HTML

### ✅ Cleaner Storage
- Only `.md` files in `website-builder/pages/`
- No redundant `.html` files
- Smaller disk usage

## How It Works Now

```
User creates page via MCP tool
          ↓
Tool saves markdown to .md file
          ↓
Server (http_server.py or website-builder/server.py)
          ↓
Renders markdown on-the-fly when requested
          ↓
Returns beautiful HTML to browser
```

## Example

### Creating a Page
```
In Claude/Cursor:
"Create a webpage called 'standup-notes' with title 'Monday Standup' 
containing notes from this morning"
```

### What Gets Saved
```markdown
# Monday Standup

Notes from this morning's meeting...

- Project X is on track
- Need to review API designs
- Deploy scheduled for Friday
```

**File:** `website-builder/pages/standup-notes.md`

### What Gets Rendered
When you visit `http://localhost:8082/page/standup-notes`, the server:
1. Reads `standup-notes.md`
2. Converts markdown to HTML
3. Applies CSS styling
4. Returns beautiful webpage

## Servers Still Work

Both servers render markdown on-the-fly:

### HTTP MCP Server
```python
# mcp-server/http_server.py
async def serve_markdown_page(md_path: Path, page_name: str):
    md_content = md_path.read_text()
    html_content = markdown.Markdown(...).convert(md_content)
    return HTMLResponse(content=html)
```

### Website Builder Server
```python
# website-builder/server.py
def _serve_markdown(self, md_path: Path, page_name: str):
    md_content = md_path.read_text()
    html_content = md.convert(md_content)
    return html_response
```

## Backward Compatibility

**Existing HTML files:**
- Still work if they exist
- Servers check for `.md` first, then `.html` fallback
- Can delete old `.html` files manually

**Migration:**
```bash
# Optional: Remove old HTML files
cd website-builder/pages
rm *.html

# Markdown files will be served automatically
```

## Tool Response

**Old response:**
```json
{
  "success": true,
  "message": "Page 'my-page' created successfully (saved as .md and .html)",
  "md_file": "/.../my-page.md",
  "html_file": "/.../my-page.html"
}
```

**New response:**
```json
{
  "success": true,
  "message": "Page 'my-page' created successfully as markdown",
  "md_file": "/.../my-page.md"
}
```

## Testing

```bash
# 1. Create a page via MCP tool
"Create a webpage called 'test-page' with content 'Hello World'"

# 2. Check only .md file exists
ls website-builder/pages/
# test-page.md ✅ (no .html)

# 3. View in browser
open http://localhost:8082/page/test-page
# Renders beautifully! ✨
```

## Code Removed

Since we're not generating HTML anymore, these are now unused:
- Jinja2 template rendering logic
- `_create_simple_html()` fallback (kept for potential future use)
- HTML conversion in create_page

The code is cleaner and more maintainable! 🎉

