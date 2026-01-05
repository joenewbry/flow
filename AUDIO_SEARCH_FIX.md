# Audio Search Filter Fix

**Date:** October 18, 2025  
**Status:** ✅ Fixed

## Problem

The MCP `search-screenshots` tool had a `data_type` parameter to filter by `"audio"` or `"ocr"`, but it wasn't working properly:

- **ChromaDB Search**: Supported audio filtering correctly ✅
- **File-based Fallback**: Did NOT support audio filtering ❌
  - Always returned `"data_type_filter": "ocr_only"`
  - Only searched OCR files in `refinery/data/ocr`
  - Ignored audio files completely

## Root Cause

The `_search_files()` fallback method in `mcp-server/tools/search.py` had two issues:

1. **Didn't accept `data_type` parameter** - The method signature was missing this parameter
2. **Only searched OCR directory** - Hard-coded to only look at OCR JSON files
3. **Audio JSON files are empty** - Transcript text is stored in `.md` files, not `.json` files

## Solution

Updated `mcp-server/tools/search.py` with the following changes:

### 1. Added `data_type` parameter to `_search_files()`
```python
async def _search_files(
    self,
    query: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 10,
    data_type: Optional[str] = None  # ← Added
) -> Dict[str, Any]:
```

### 2. Added support for searching audio files
```python
# Get files based on data_type filter
all_files = []

# Get OCR files if requested
if data_type is None or data_type == "ocr":
    ocr_files = list(self.ocr_data_dir.glob("*.json"))
    all_files.extend([(f, "ocr") for f in ocr_files])

# Get audio files if requested
if data_type is None or data_type == "audio":
    audio_dir = self.workspace_root / "refinery" / "data" / "audio"
    if audio_dir.exists():
        audio_files = list(audio_dir.glob("*.json"))
        all_files.extend([(f, "audio") for f in audio_files])
```

### 3. Added helper methods
- `_read_audio_file()` - Reads both JSON and markdown files for audio transcripts
- `_parse_audio_filename_timestamp()` - Parses audio file timestamps (`auto_YYYYMMDD_HHMMSS.json`)

### 4. Audio file reading reads markdown
Since audio JSON files have empty `transcript` arrays, the method now:
1. Reads the JSON file for metadata
2. Reads the corresponding `.md` file for actual transcript text
3. Extracts transcript text from markdown (skips headers/metadata)

## Testing

### Before Fix:
```json
{
  "query": "audio conversation",
  "data_type": "audio",
  "search_method": "file_based_text_search",
  "data_type_filter": "ocr_only",  // ← WRONG!
  "total_found": 0
}
```

### After Fix:
```json
{
  "query": "working",
  "data_type": "audio",
  "search_method": "file_based_text_search",
  "data_type_filter": "audio",  // ← CORRECT!
  "total_found": 1,
  "results": [
    {
      "timestamp": "2025-10-18T10:34:35.127932",
      "data_type": "audio",
      "text_preview": "alright, so let's see if this is working..."
    }
  ]
}
```

## How to Use

### In Claude Desktop (MCP Tool):

**Search only audio:**
```json
{
  "query": "technical discussion",
  "data_type": "audio"
}
```

**Search only OCR:**
```json
{
  "query": "github repository",
  "data_type": "ocr"
}
```

**Search both (default):**
```json
{
  "query": "Flow project"
}
```

## Notes

### ChromaDB Date Filter Issue
There's a separate issue with ChromaDB date filtering:
```
Error in ChromaDB search: Expected operand value to be an int or a float for operator $gte, got 2025-10-18T00:00:00
```

When this error occurs, the search automatically falls back to file-based search, which now works correctly with audio filtering.

### Restart Required
For Claude Desktop to use the updated MCP server code, you need to restart Claude Desktop.

## Files Modified

- `mcp-server/tools/search.py` - Added audio support to file-based search fallback

## Verification

Run this to test audio search:
```python
python -c "
import asyncio
from pathlib import Path
import sys
sys.path.insert(0, 'mcp-server')
from tools.search import SearchTool

async def test():
    tool = SearchTool(Path('.'))
    results = await tool.search_screenshots(
        query='working',
        data_type='audio',
        limit=10
    )
    print(f'Found: {results.get(\"total_found\")} audio results')
    print(f'Filter: {results.get(\"data_type_filter\")}')
    
asyncio.run(test())
"
```

Expected output:
```
Found: 1 audio results
Filter: audio
```

## Status

✅ **Fixed and Tested**
- File-based search now supports audio filtering
- Audio transcript text is properly extracted from markdown files
- Both `data_type="audio"` and `data_type="ocr"` work correctly
- Fallback search now respects the data_type parameter




