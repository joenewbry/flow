# ChromaDB Segmentation Fault Fix

## Problem

When loading large amounts of JSON screenshot data (24,000+ files) into ChromaDB, the ChromaDB server may crash with a segmentation fault. This typically happens when:

1. Too many documents are loaded at once
2. ChromaDB server is overwhelmed by bulk insert operations
3. Memory issues when processing large batches

## Solution

The loading function has been improved with the following changes:

1. **Reduced batch size**: Changed from 50 to 10 documents per batch
2. **Added delays**: 500ms delay between batches to avoid overwhelming ChromaDB
3. **Retry logic**: Automatic retries with exponential backoff on failures
4. **Health checks**: ChromaDB heartbeat checks before each batch
5. **Per-document ID checking**: Instead of loading all IDs into memory, check each document individually

## Usage

### Option 1: Automatic Loading (Improved)

The improved loading function will automatically run when you start `run.py`, but with safer defaults:

```bash
cd refinery
source .venv/bin/activate
python run.py
```

The loading will now:
- Process files in smaller batches (10 at a time)
- Add delays between batches
- Retry on failures
- Skip existing documents

### Option 2: Standalone Loading Script (Recommended for Large Datasets)

For very large datasets (10,000+ files), use the standalone script:

```bash
cd refinery
source .venv/bin/activate

# Make sure ChromaDB is running first
# In another terminal: chroma run --host localhost --port 8000

# Load data with custom settings
python load_ocr_data.py --batch-size 5 --delay 1.0
```

**Recommended settings for large datasets:**
- `--batch-size 5`: Smaller batches for very large datasets
- `--delay 1.0`: Longer delay between batches
- `--no-skip-existing`: Only if you want to reload existing data

### Option 3: Disable Auto-Loading

If you want to disable automatic loading on startup, you can modify `run.py` to skip the `load_existing_ocr_data()` call, or use the standalone script when needed.

## Troubleshooting

### ChromaDB Server Crashes

If ChromaDB server still crashes:

1. **Reduce batch size further**:
   ```bash
   python load_ocr_data.py --batch-size 5 --delay 1.0
   ```

2. **Increase delay between batches**:
   ```bash
   python load_ocr_data.py --batch-size 10 --delay 2.0
   ```

3. **Load in smaller chunks**: Process files in date ranges or manually split the data

### Check ChromaDB Server Status

```bash
# Check if ChromaDB is running
curl http://localhost:8000/api/v1/heartbeat

# Check ChromaDB logs
# Look for errors in the terminal where ChromaDB is running
```

### Restart ChromaDB

If ChromaDB crashes, restart it:

```bash
cd refinery
source .venv/bin/activate
chroma run --host localhost --port 8000
```

Then resume loading with the standalone script (it will skip already-loaded documents).

## Performance Tips

1. **For 10,000+ files**: Use `--batch-size 5 --delay 1.0`
2. **For 5,000-10,000 files**: Use `--batch-size 10 --delay 0.5` (default)
3. **For <5,000 files**: Default settings should work fine

## Monitoring Progress

The script logs progress every 100 files:
```
INFO - Loaded batch of 10 documents (progress: 100/24826, total loaded: 95, skipped: 5)
```

Watch for:
- Steady progress (numbers increasing)
- Error messages (will show retry attempts)
- "Loading complete" message at the end

## Recovery

If loading is interrupted:

1. The script automatically skips documents that already exist
2. Simply restart the script - it will continue from where it left off
3. No data is lost - JSON files remain intact

## Technical Details

The segmentation fault was caused by:
- ChromaDB server trying to process too many embeddings at once
- Memory pressure when creating embeddings for large batches
- Lack of backpressure/throttling in the original implementation

The fix addresses these by:
- Processing smaller batches (10 documents vs 50)
- Adding delays to allow ChromaDB to process each batch
- Checking server health before each operation
- Implementing retry logic for transient failures

