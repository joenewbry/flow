# ✅ MCP Search Tool Updated - Data Type Filtering

## What Changed

The MCP `search-screenshots` tool now supports filtering by data type and always returns the `data_type` tag in results.

## New Features

### 1. **Data Type Filter Parameter**

The `search-screenshots` tool now accepts a `data_type` parameter:

```json
{
  "query": "meeting notes",
  "data_type": "audio"  // Optional: "ocr", "audio", or omit for both
}
```

### 2. **Default Behavior: Search Both**

- **Without `data_type`**: Searches both OCR and audio data (default)
- **With `data_type: "ocr"`**: Only searches screen OCR data
- **With `data_type: "audio"`**: Only searches audio transcripts

### 3. **Data Type Tag in Results**

Every result now includes the `data_type` field:

```json
{
  "timestamp": "2024-10-15T14:30:00",
  "screen_name": "screen_0",
  "data_type": "ocr",  // or "audio"
  "text_preview": "...",
  "relevance": 0.85
}
```

## Usage Examples

### Search Everything (Default)
```
"Search for project deadline"
```
Returns both OCR and audio results.

### Search Only Audio Transcripts
```json
{
  "query": "what did we discuss in the meeting",
  "data_type": "audio"
}
```

### Search Only Screen OCR
```json
{
  "query": "github repository",
  "data_type": "ocr"
}
```

### With Date Range and Filter
```json
{
  "query": "design review",
  "start_date": "2024-10-10",
  "end_date": "2024-10-15",
  "data_type": "audio",
  "limit": 20
}
```

## Response Format

```json
{
  "query": "meeting notes",
  "results": [
    {
      "timestamp": "2024-10-15T14:30:22",
      "screen_name": "N/A",
      "data_type": "audio",       // <-- Always included
      "text_length": 245,
      "word_count": 42,
      "text_preview": "Welcome everyone to today's standup...",
      "relevance": 0.892,
      "source": "background_audio_recording"
    },
    {
      "timestamp": "2024-10-15T15:45:00",
      "screen_name": "screen_0",
      "data_type": "ocr",          // <-- Always included
      "text_length": 1024,
      "word_count": 156,
      "text_preview": "Meeting notes from project review...",
      "relevance": 0.765,
      "source": "flow-runner"
    }
  ],
  "total_found": 2,
  "search_method": "vector_search_chromadb",
  "data_type_filter": "all",     // Shows what filter was applied
  "date_range": {
    "start_date": null,
    "end_date": null
  }
}
```

## Tool Schema Update

The MCP tool now has this schema:

```python
Tool(
    name="search-screenshots",
    description="Search OCR and audio data with optional filtering by data type. Searches both screen OCR text and audio transcripts by default.",
    inputSchema={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query for the OCR text or audio transcript content"},
            "start_date": {"type": "string", "description": "Start date (YYYY-MM-DD, optional)"},
            "end_date": {"type": "string", "description": "End date (YYYY-MM-DD, optional)"},
            "limit": {"type": "integer", "default": 10},
            "data_type": {
                "type": "string",
                "enum": ["ocr", "audio"],
                "description": "Filter by data type: 'ocr' for screen OCR only, 'audio' for audio transcripts only. Omit to search both types (default)."
            }
        },
        "required": ["query"]
    }
)
```

## Technical Implementation

### 1. ChromaDB Integration
- Uses vector search when ChromaDB is available
- Applies `data_type` filter using ChromaDB's `where` clause
- Falls back to file-based search if ChromaDB unavailable

### 2. Filter Logic
```python
# Build where clause
where_filters = []

# Add data_type filter
if data_type and data_type in ["ocr", "audio"]:
    where_filters.append({"data_type": data_type})

# Query with filter
collection.query(
    query_texts=[query],
    where={"$and": where_filters} if len(where_filters) > 1 else where_filters[0]
)
```

### 3. Response Includes Tag
```python
result = {
    "timestamp": metadata.get("timestamp"),
    "data_type": metadata.get("data_type", "unknown"),  // Always included
    "text_preview": ...,
    ...
}
```

## Files Modified

- ✅ `/mcp-server/tools/search.py` - Added ChromaDB support and data_type filtering
- ✅ `/mcp-server/server.py` - Updated tool schema and parameter passing

## Benefits

1. **Flexible Filtering**: Search both types or filter by specific type
2. **Clear Attribution**: Every result shows whether it's from OCR or audio
3. **Backward Compatible**: Existing queries work (default to searching both)
4. **Better Context**: Users can see the source of information

## Testing

Test the new functionality:

```bash
# From Claude Desktop or MCP client:
search_screenshots("meeting discussion", data_type="audio")
search_screenshots("github code", data_type="ocr")
search_screenshots("project deadline")  # Searches both
```

---

**Now you can filter by OCR or audio, and always see which type each result is! 🎉**

