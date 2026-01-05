#!/usr/bin/env python3
"""
Standalone script to load existing OCR JSON files into ChromaDB.

This script can be run separately to load data without starting the full Flow runner.
Useful for bulk loading large amounts of data or recovering from crashes.

Usage:
    python load_ocr_data.py [--batch-size N] [--delay D] [--skip-existing]
"""

import asyncio
import logging
import json
import glob
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def load_ocr_data(
    ocr_data_dir: Path,
    batch_size: int = 10,
    delay_between_batches: float = 0.5,
    skip_existing: bool = True
):
    """Load existing OCR data from JSON files into ChromaDB."""
    try:
        logger.info("Starting OCR data loading...")
        
        # Get all JSON files from the OCR data directory
        ocr_files = glob.glob(str(ocr_data_dir / "*.json"))
        
        if not ocr_files:
            logger.info("No existing OCR data found")
            return
        
        logger.info(f"Found {len(ocr_files)} existing OCR files to process")
        
        # Try to initialize ChromaDB client
        try:
            import chromadb
            import requests.exceptions
            
            client = chromadb.HttpClient(host="localhost", port=8000)
            
            # Test connection with heartbeat
            try:
                client.heartbeat()
                logger.info("ChromaDB server is running and accessible")
            except Exception as hb_error:
                logger.error(f"ChromaDB heartbeat failed: {hb_error}")
                logger.error("Please ensure ChromaDB server is running: chroma run --host localhost --port 8000")
                return
            
            # Get or create the screen_ocr_history collection
            collection = client.get_or_create_collection(
                name="screen_ocr_history",
                metadata={"description": "Screenshot OCR data"}
            )
            logger.info("Connected to ChromaDB collection 'screen_ocr_history'")
            
        except requests.exceptions.ConnectionError as conn_error:
            logger.error(f"ChromaDB server not available (is server running on localhost:8000?): {conn_error}")
            logger.error("Start ChromaDB with: chroma run --host localhost --port 8000")
            return
        except Exception as chroma_error:
            logger.error(f"ChromaDB initialization failed: {chroma_error}")
            return
        
        # Process files in batches
        total_loaded = 0
        total_skipped = 0
        total_errors = 0
        max_retries = 3
        retry_delay = 2  # seconds
        
        for i in range(0, len(ocr_files), batch_size):
            batch_files = ocr_files[i:i + batch_size]
            
            documents = []
            metadatas = []
            ids = []
            
            # Process files in this batch
            for file_path in batch_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        ocr_data = json.load(f)
                    
                    # Create document ID
                    doc_id = ocr_data["timestamp"] + "_" + ocr_data["screen_name"]
                    
                    # Check if already exists (if skip_existing is enabled)
                    if skip_existing:
                        try:
                            existing = collection.get(ids=[doc_id])
                            if existing and existing.get('ids') and len(existing['ids']) > 0:
                                total_skipped += 1
                                continue
                        except Exception:
                            # If check fails, proceed with adding (might be a new document)
                            pass
                    
                    # Prepare content for embedding
                    content = f"Screen: {ocr_data['screen_name']} Text: {ocr_data['text']}"
                    
                    # Prepare metadata
                    # Convert timestamp to Unix timestamp for ChromaDB filtering
                    timestamp_dt = datetime.fromisoformat(ocr_data["timestamp"])
                    
                    metadata = {
                        "timestamp": timestamp_dt.timestamp(),  # Unix timestamp (float) for filtering
                        "timestamp_iso": ocr_data["timestamp"],  # ISO string for display
                        "screen_name": ocr_data["screen_name"],
                        "text_length": ocr_data["text_length"],
                        "word_count": ocr_data["word_count"],
                        "source": ocr_data["source"],
                        "extracted_text": ocr_data["text"],
                        "data_type": "ocr",
                        "task_category": "screenshot_ocr"
                    }
                    
                    documents.append(content)
                    metadatas.append(metadata)
                    ids.append(doc_id)
                    
                except Exception as error:
                    logger.error(f"Error processing file {file_path}: {error}")
                    total_errors += 1
                    continue
            
            # Bulk add documents to ChromaDB with retry logic
            if documents:
                retry_count = 0
                success = False
                
                while retry_count < max_retries and not success:
                    try:
                        # Check ChromaDB server health before adding
                        try:
                            client.heartbeat()
                        except Exception as hb_error:
                            logger.warning(f"ChromaDB heartbeat failed, waiting {retry_delay}s before retry: {hb_error}")
                            await asyncio.sleep(retry_delay)
                            retry_count += 1
                            continue
                        
                        collection.add(
                            documents=documents,
                            metadatas=metadatas,
                            ids=ids
                        )
                        total_loaded += len(documents)
                        success = True
                        
                        # Log progress every 100 files or at end
                        progress = i + len(batch_files)
                        if progress % 100 == 0 or progress >= len(ocr_files):
                            logger.info(f"Loaded batch of {len(documents)} documents (progress: {progress}/{len(ocr_files)}, total loaded: {total_loaded}, skipped: {total_skipped})")
                        
                    except Exception as error:
                        retry_count += 1
                        if retry_count < max_retries:
                            logger.warning(f"Error adding batch to ChromaDB (attempt {retry_count}/{max_retries}): {error}")
                            logger.info(f"Waiting {retry_delay * retry_count}s before retry...")
                            await asyncio.sleep(retry_delay * retry_count)  # Exponential backoff
                        else:
                            logger.error(f"Failed to add batch after {max_retries} attempts: {error}")
                            total_errors += len(documents)
                
                # Small delay between batches to avoid overwhelming ChromaDB
                if i + batch_size < len(ocr_files):
                    await asyncio.sleep(delay_between_batches)
        
        logger.info(f"Loading complete: {total_loaded} documents loaded, {total_skipped} skipped (already existed), {total_errors} errors")
        
    except Exception as error:
        logger.error(f"Error in bulk loading OCR data: {error}")
        raise


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Load OCR JSON files into ChromaDB")
    parser.add_argument(
        "--data-dir",
        type=str,
        default="data/ocr",
        help="Directory containing OCR JSON files (default: data/ocr)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Number of files to process per batch (default: 10, recommended: 5-20)"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.5,
        help="Delay in seconds between batches (default: 0.5)"
    )
    parser.add_argument(
        "--no-skip-existing",
        action="store_true",
        help="Don't skip documents that already exist in ChromaDB"
    )
    
    args = parser.parse_args()
    
    ocr_data_dir = Path(args.data_dir)
    
    if not ocr_data_dir.exists():
        logger.error(f"OCR data directory not found: {ocr_data_dir}")
        return 1
    
    await load_ocr_data(
        ocr_data_dir=ocr_data_dir,
        batch_size=args.batch_size,
        delay_between_batches=args.delay,
        skip_existing=not args.no_skip_existing
    )
    
    return 0


if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

