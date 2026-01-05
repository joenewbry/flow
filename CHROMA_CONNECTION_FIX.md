# ChromaDB Connection Fix - Summary

## Problem Identified

The Claude MCP server was unable to properly query ChromaDB and was falling back to file-based search. The error was:

```
Error in ChromaDB search: Expected operand value to be an int or a float for operator $gte, got 2025-10-18T00:00:00 in query.
```

**Root Cause:** ChromaDB's comparison operators (`$gte`, `$lte`, `$lt`) only work with numeric values (integers or floats), but the system was:
1. Storing timestamps as ISO format strings in ChromaDB metadata
2. Trying to query with ISO format strings

This caused all ChromaDB queries with date filters to fail, forcing the system to use the slower file-based search fallback.

## Files Modified

### 1. MCP Server Search Tools
Updated to convert datetime objects to Unix timestamps (floats) for ChromaDB queries:

- **`mcp-server/tools/search.py`** (lines 254, 257)
  - Changed `start_dt.isoformat()` → `start_dt.timestamp()`
  - Changed `end_dt.isoformat()` → `end_dt.timestamp()`
  - Updated result formatting to use `timestamp_iso` field for display

- **`mcp-server/tools/vector_search.py`** (lines 125-126)
  - Changed window timestamp comparisons to use `.timestamp()`
  - Updated result formatting to use `timestamp_iso` field

- **`mcp-server/tools/recent_search.py`** (line 148)
  - Changed start_time query to use `.timestamp()`
  - Updated to read `timestamp_iso` for display

### 2. Data Storage - OCR Capture
Updated to store timestamps as Unix timestamps with ISO string for display:

- **`refinery/run.py`** (3 locations: lines 157-171, 196-210, 307-321)
  - Added conversion: `timestamp_dt = datetime.fromisoformat(ocr_data["timestamp"])`
  - Changed metadata to store:
    - `"timestamp": timestamp_dt.timestamp()` (float for filtering)
    - `"timestamp_iso": ocr_data["timestamp"]` (ISO string for display)

### 3. Data Storage - Audio Transcription
Updated audio background recorder with same timestamp fix:

- **`audio_background_recorder.py`** (lines 501-515)
  - Added timestamp conversion
  - Stores both `timestamp` (float) and `timestamp_iso` (string)

## Solution Details

The fix implements a dual-field approach:
- **`timestamp`**: Unix timestamp (float) - used for ChromaDB filtering/comparison
- **`timestamp_iso`**: ISO format string - used for display and human readability

This ensures:
✅ ChromaDB queries work with comparison operators
✅ Timestamps remain human-readable in results
✅ Backward compatibility (falls back to `timestamp` if `timestamp_iso` not present)

## Next Steps to Apply the Fix

### Important: The existing data in ChromaDB still has ISO string timestamps!

To fully fix the issue, you have two options:

### Option 1: Reload All Data (Recommended)
This will re-import all OCR data files into ChromaDB with the correct timestamp format:

```bash
# 1. Stop the Flow capture system if running
# Check for running processes
ps aux | grep "python.*refinery/run.py"

# Kill if found (replace PID with actual process ID)
kill <PID>

# 2. Delete the existing ChromaDB collection to start fresh
# Connect to ChromaDB and delete collection (or delete the chroma directory)
rm -rf refinery/chroma/*

# 3. Restart the Flow capture system
# It will automatically reload all OCR data with correct timestamps
cd refinery
python run.py
```

### Option 2: Manual ChromaDB Collection Update (Advanced)
If you want to preserve the existing ChromaDB data and update it in place, you would need to:
1. Query all documents from the collection
2. Update each document's metadata to include the timestamp as float
3. Re-add with updated metadata

This is more complex and not recommended unless you have specific reasons to preserve the current ChromaDB state.

## Testing the Fix

After reloading the data, test that ChromaDB queries work:

1. Restart the MCP server (Claude will do this automatically, or you can restart Claude Desktop)

2. Try a search query with date filtering through Claude:
   ```
   "Search for work activities from today"
   ```

3. Check the MCP server logs to verify ChromaDB is being used:
   ```bash
   tail -f logs/mcp-server.log
   ```

You should see:
- ✅ `ChromaDB search completed: X results`
- ❌ No more "Error in ChromaDB search" messages
- ❌ No more "File-based search (fallback)" messages

## Why This Happened

The issue was related to how Claude Desktop launches the MCP server - it runs in its own process context, and when ChromaDB queries failed due to the timestamp format issue, it silently fell back to file-based search. The root cause wasn't the MCP server launch mechanism itself, but rather the data format incompatibility between what was stored in ChromaDB and what ChromaDB's query operators expect.

## Summary

✅ **Fixed**: All search tools now use Unix timestamps for ChromaDB queries
✅ **Fixed**: All data storage now saves timestamps in both formats
✅ **Next**: Reload existing ChromaDB data to apply the fix to historical data
✅ **Result**: Full ChromaDB vector search functionality restored for the MCP server

The system will now properly use ChromaDB's powerful vector search instead of falling back to slower file-based search.


