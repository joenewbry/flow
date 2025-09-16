#!/usr/bin/env python3
"""
Flow Run Script - Multi-Screen Screenshot Capture and OCR Processing

This script captures screen_ocr_history from all available screens every minute,
processes them with OCR, and saves the data to ChromaDB.

Screen Naming Convention:
- Screen 0: "screen_0" (primary display)
- Screen 1: "screen_1" (secondary display)
- Screen N: "screen_N" (additional displays)

Screenshot files are saved as: {timestamp}_{screen_name}.png
OCR data files are saved as: {timestamp}_{screen_name}.json

All data is stored in ChromaDB collection "screen_ocr_history" for search and analysis.
"""

import asyncio
import logging
import json
import platform
import threading
import time
import requests
import glob
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from PIL import Image
import pytesseract
from io import BytesIO

# Import screen detection and chroma client
from lib.screen_detection import screen_detector
from lib.chroma_client import chroma_client

logger = logging.getLogger(__name__)


class FlowRunner:
    def __init__(self, capture_interval: int = 60, max_concurrent_ocr: int = 4):
        self.capture_interval = capture_interval  # seconds
        self.max_concurrent_ocr = max_concurrent_ocr
        self.ocr_data_dir = Path("data/ocr")
        
        self.is_running = False
        self.processing_queue: List[Dict[str, Any]] = []
        self._semaphore = asyncio.Semaphore(max_concurrent_ocr)
        
        # Ensure tesseract is available
        self._configure_tesseract()
        
        # Initialize threading for background OCR processing
        self.ocr_thread = None
        self.ocr_queue = []
        self.ocr_lock = threading.Lock()
    
    def _configure_tesseract(self):
        """Configure tesseract executable path if needed."""
        system = platform.system().lower()
        
        if system == "windows":
            # Common Windows installation paths
            possible_paths = [
                r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"
            ]
            
            for path in possible_paths:
                if Path(path).exists():
                    pytesseract.pytesseract.tesseract_cmd = path
                    break
        
        # Test tesseract availability
        try:
            pytesseract.get_tesseract_version()
            logger.info(f"Tesseract version: {pytesseract.get_tesseract_version()}")
        except Exception as error:
            logger.error(f"Tesseract not available: {error}")
            raise Exception("Tesseract OCR not installed or not in PATH")
    
    async def ensure_directories(self):
        """Ensure output directories exist."""
        self.ocr_data_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured directory exists: {self.ocr_data_dir}")
    
    def process_ocr_background(self, image: Image.Image, screen_name: str, timestamp: str):
        """Process OCR in background thread."""
        ocr_success = False
        result = None
        
        try:
            logger.info(f"[{timestamp}] Processing OCR on thread {threading.current_thread().ident}")
            
            # Convert PIL image to format suitable for tesseract
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Perform OCR
            text = pytesseract.image_to_string(image, lang='eng')
            text = text.strip().replace('\n+', '\n')
            
            result = {
                "screen_name": screen_name,
                "timestamp": timestamp,
                "text": text,
                "text_length": len(text),
                "word_count": len([word for word in text.split() if word.strip()]),
                "source": "flow-runner"
            }
            
            # Save OCR data to JSON file
            timestamp_str = timestamp.replace(':', '-').replace('.', '-')
            ocr_filename = f"{timestamp_str}_{screen_name}.json"
            ocr_filepath = self.ocr_data_dir / ocr_filename
            
            with open(ocr_filepath, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            logger.info(f"[{timestamp}] OCR data saved as {ocr_filename}")
            logger.info(f"[{timestamp}] Screen: {screen_name}, Text: {len(text)} chars, Words: {result['word_count']}")
            
            ocr_success = True
            
        except Exception as error:
            logger.error(f"OCR error for {screen_name}: {error}")
            return  # Exit early if OCR fails
            
        # Try to store in ChromaDB only if OCR was successful
        # This is separate from OCR processing so ChromaDB failures don't affect OCR
        if ocr_success and result:
            try:
                self.store_in_chroma_sync(result)
            except Exception as chroma_error:
                logger.warning(f"[{timestamp}] ChromaDB storage failed for {screen_name}, but OCR data was saved: {chroma_error}")
    
    def store_in_chroma_sync(self, ocr_data: Dict[str, Any]):
        """Store OCR data in ChromaDB collection 'screen_ocr_history' (synchronous version for background threads)."""
        try:
            import chromadb
            from chromadb.errors import ChromaError
            import requests.exceptions
            
            # Initialize ChromaDB client
            client = chromadb.HttpClient(host="localhost", port=8000)
            
            # Get or create the screen_ocr_history collection
            collection = client.get_or_create_collection(
                name="screen_ocr_history",
                metadata={"description": "Screenshot OCR data"}
            )
            
            # Prepare content for embedding
            content = f"Screen: {ocr_data['screen_name']} Text: {ocr_data['text']}"
            
            # Prepare metadata
            metadata = {
                "timestamp": ocr_data["timestamp"],
                "screen_name": ocr_data["screen_name"],
                "text_length": ocr_data["text_length"],
                "word_count": ocr_data["word_count"],
                "source": ocr_data["source"],
                "extracted_text": ocr_data["text"],
                "task_category": "screenshot_ocr"
            }
            
            # Store in ChromaDB
            doc_id = ocr_data["timestamp"] + "_" + ocr_data["screen_name"]
            
            collection.add(
                documents=[content],
                metadatas=[metadata],
                ids=[doc_id]
            )
            
            logger.debug(f"Stored OCR data in ChromaDB screen_ocr_history collection: {ocr_data['timestamp']}")
            
        except requests.exceptions.ConnectionError as conn_error:
            # ChromaDB server is not running or not accessible
            raise Exception(f"ChromaDB server connection failed (is server running on localhost:8000?): {conn_error}")
        except ChromaError as chroma_error:
            # ChromaDB-specific errors
            raise Exception(f"ChromaDB operation failed: {chroma_error}")
        except Exception as error:
            # General errors
            raise Exception(f"Unexpected error storing in ChromaDB: {error}")
    
    async def store_in_chroma(self, ocr_data: Dict[str, Any]):
        """Store OCR data in ChromaDB collection 'screen_ocr_history'."""
        try:
            # Prepare content for embedding
            content = f"Screen: {ocr_data['screen_name']} Text: {ocr_data['text']}"
            
            # Prepare metadata
            metadata = {
                "timestamp": ocr_data["timestamp"],
                "screen_name": ocr_data["screen_name"],
                "text_length": ocr_data["text_length"],
                "word_count": ocr_data["word_count"],
                "source": ocr_data["source"],
                "extracted_text": ocr_data["text"],
                "task_category": "screenshot_ocr"
            }
            
            # Store in ChromaDB collection 'screen_ocr_history'
            await chroma_client.add_document(
                collection_name="screen_ocr_history",
                doc_id=ocr_data["timestamp"] + "_" + ocr_data["screen_name"],
                content=content,
                metadata=metadata
            )
            
            logger.debug(f"Stored OCR data in ChromaDB screen_ocr_history collection: {ocr_data['timestamp']}")
            
        except Exception as error:
            logger.warning(f"ChromaDB storage failed, but OCR data was already saved: {error}")
            # Don't re-raise the exception - OCR data is safely stored in JSON files
    
    async def load_existing_ocr_data(self):
        """Load existing OCR data from refinery/data/ocr directory into ChromaDB."""
        try:
            logger.info("Checking for existing OCR data to load...")
            
            # Get all JSON files from the OCR data directory
            ocr_files = glob.glob(str(self.ocr_data_dir / "*.json"))
            
            if not ocr_files:
                logger.info("No existing OCR data found")
                return
            
            logger.info(f"Found {len(ocr_files)} existing OCR files to process")
            
            # Try to initialize ChromaDB client for bulk operations
            try:
                import chromadb
                from chromadb.errors import ChromaError
                import requests.exceptions
                
                client = chromadb.HttpClient(host="localhost", port=8000)
                
                # Get or create the screen_ocr_history collection
                collection = client.get_or_create_collection(
                    name="screen_ocr_history",
                    metadata={"description": "Screenshot OCR data"}
                )
                
            except requests.exceptions.ConnectionError as conn_error:
                logger.warning(f"ChromaDB server not available for bulk loading (is server running on localhost:8000?): {conn_error}")
                logger.info("OCR files are safely stored as JSON files and can be loaded when ChromaDB is available")
                return
            except Exception as chroma_error:
                logger.warning(f"ChromaDB initialization failed for bulk loading: {chroma_error}")
                logger.info("OCR files are safely stored as JSON files and can be loaded when ChromaDB is available")
                return
            
            # Get existing document IDs to avoid duplicates
            try:
                existing_ids = set()
                # Try to get existing documents (this may fail if collection is empty)
                try:
                    result = collection.get()
                    if result and result.get('ids'):
                        existing_ids = set(result['ids'])
                        logger.info(f"Found {len(existing_ids)} existing documents in ChromaDB")
                except Exception:
                    # Collection might be empty, which is fine
                    logger.info("ChromaDB collection is empty or new")
            except Exception as error:
                logger.warning(f"Could not check existing documents: {error}")
                existing_ids = set()
            
            # Process files in batches to avoid memory issues
            batch_size = 50
            total_loaded = 0
            total_skipped = 0
            
            for i in range(0, len(ocr_files), batch_size):
                batch_files = ocr_files[i:i + batch_size]
                
                documents = []
                metadatas = []
                ids = []
                
                for file_path in batch_files:
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            ocr_data = json.load(f)
                        
                        # Create document ID
                        doc_id = ocr_data["timestamp"] + "_" + ocr_data["screen_name"]
                        
                        # Skip if already exists
                        if doc_id in existing_ids:
                            total_skipped += 1
                            continue
                        
                        # Prepare content for embedding
                        content = f"Screen: {ocr_data['screen_name']} Text: {ocr_data['text']}"
                        
                        # Prepare metadata
                        metadata = {
                            "timestamp": ocr_data["timestamp"],
                            "screen_name": ocr_data["screen_name"],
                            "text_length": ocr_data["text_length"],
                            "word_count": ocr_data["word_count"],
                            "source": ocr_data["source"],
                            "extracted_text": ocr_data["text"],
                            "task_category": "screenshot_ocr"
                        }
                        
                        documents.append(content)
                        metadatas.append(metadata)
                        ids.append(doc_id)
                        
                    except Exception as error:
                        logger.error(f"Error processing file {file_path}: {error}")
                        continue
                
                # Bulk add documents to ChromaDB
                if documents:
                    try:
                        collection.add(
                            documents=documents,
                            metadatas=metadatas,
                            ids=ids
                        )
                        total_loaded += len(documents)
                        logger.info(f"Loaded batch of {len(documents)} documents (progress: {i + len(batch_files)}/{len(ocr_files)})")
                    except Exception as error:
                        logger.error(f"Error adding batch to ChromaDB: {error}")
            
            logger.info(f"Bulk loading complete: {total_loaded} documents loaded, {total_skipped} skipped (already existed)")
            
        except Exception as error:
            logger.warning(f"Error in bulk loading existing OCR data: {error}")
            logger.info("OCR files are safely stored as JSON files and can be processed individually or loaded later when ChromaDB is available")
    
    async def capture_all_screens(self):
        """Capture screen_ocr_history from all available screens."""
        try:
            # Detect screens if not already done
            if not screen_detector.screens:
                await screen_detector.detect_screens()
            
            if not screen_detector.screens:
                logger.warning("No screens detected")
                return
            
            timestamp = datetime.now().isoformat()
            logger.info(f"[{timestamp}] Screenshot taken from {len(screen_detector.screens)} screen(s)")
            
            # Capture each screen separately
            screen_captures = await screen_detector.capture_all_screens_separately()
            
            # Process each capture
            for screen_info, image in screen_captures:
                try:
                    # Start background OCR processing (no screenshot saving)
                    ocr_thread = threading.Thread(
                        target=self.process_ocr_background,
                        args=(image, screen_info.name, timestamp)
                    )
                    ocr_thread.daemon = True
                    ocr_thread.start()
                    
                except Exception as error:
                    logger.error(f"Error processing {screen_info.name}: {error}")
                    continue
            
        except Exception as error:
            logger.error(f"Error in capture_all_screens: {error}")
    
    async def start(self):
        """Start the Flow runner service."""
        try:
            logger.info("Starting Flow Runner service...")
            logger.info(f"Capture interval: {self.capture_interval} seconds")
            logger.info(f"OCR data directory: {self.ocr_data_dir}")
            logger.info(f"Max concurrent OCR: {self.max_concurrent_ocr}")
            
            await self.ensure_directories()
            
            # Initialize ChromaDB
            await chroma_client.init()
            
            # Load existing OCR data into ChromaDB
            await self.load_existing_ocr_data()
            
            # Detect screens
            await screen_detector.detect_screens()
            if not screen_detector.screens:
                raise Exception("No screens detected. Please check your display setup.")
            
            logger.info(f"Detected {len(screen_detector.screens)} screen(s): {[s.name for s in screen_detector.screens]}")
            
            # Initial capture
            await self.capture_all_screens()
            
            # Start continuous capture
            self.is_running = True
            logger.info("Flow Runner service started successfully")
            
            # Main loop
            while self.is_running:
                await asyncio.sleep(self.capture_interval)
                if self.is_running:  # Check again in case we were stopped
                    await self.capture_all_screens()
            
        except Exception as error:
            logger.error(f"Error starting Flow Runner service: {error}")
            raise
    
    async def stop(self):
        """Stop the Flow runner service."""
        logger.info("Stopping Flow Runner service...")
        
        self.is_running = False
        
        logger.info("Flow Runner service stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of the Flow runner service."""
        return {
            "running": self.is_running,
            "last_capture": datetime.now().isoformat(),
            "interval": self.capture_interval,
            "ocr_data_dir": str(self.ocr_data_dir),
            "available_screens": len(screen_detector.screens) if screen_detector.screens else 0
        }


# Global instance
flow_runner = FlowRunner()


async def main():
    """Main entry point for running the Flow runner."""
    import signal
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Handle shutdown signals
    def signal_handler(signum, frame):
        logger.info("Received shutdown signal")
        asyncio.create_task(flow_runner.stop())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await flow_runner.start()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as error:
        logger.error(f"Fatal error: {error}")
        return 1
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))
