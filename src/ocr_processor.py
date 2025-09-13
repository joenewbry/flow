"""
OCR-based screen processing for Flow CLI
Handles screenshot capture and OCR text extraction
"""

import asyncio
import logging
import json
import platform
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from PIL import Image
import pytesseract
from io import BytesIO

from lib.screen_detection import screen_detector
from lib.chroma_client import chroma_client

logger = logging.getLogger(__name__)


class OCRProcessor:
    def __init__(self, capture_interval: int = 60, max_concurrent_ocr: int = 4):
        self.capture_interval = capture_interval  # seconds
        self.max_concurrent_ocr = max_concurrent_ocr
        self.screenshots_dir = Path("data/screenshots")
        
        self.is_running = False
        self.processing_queue: List[Dict[str, Any]] = []
        self._semaphore = asyncio.Semaphore(max_concurrent_ocr)
        
        self.last_hourly_check = None
        
        # Ensure tesseract is available
        self._configure_tesseract()
    
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
        for directory in [self.summaries_dir, self.daily_dir, self.screenshots_dir]:
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory exists: {directory}")
    
    async def process_screen_ocr(self, image: Image.Image, screen_name: str, timestamp: str) -> Dict[str, Any]:
        """Process OCR for a single screen image."""
        async with self._semaphore:
            try:
                logger.info(f"Starting OCR for {screen_name}...")
                
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
                    "source": "ocr-processor"
                }
                
                logger.info(f"OCR completed for {screen_name}: {len(text)} chars, {result['word_count']} words")
                return result
                
            except Exception as error:
                logger.error(f"OCR error for {screen_name}: {error}")
                raise Exception(f"OCR processing failed for {screen_name}: {error}")
    
    async def handle_ocr_result(self, ocr_result: Dict[str, Any]):
        """Handle and save OCR result."""
        try:
            timestamp = ocr_result["timestamp"]
            screen_name = ocr_result["screen_name"]
            text = ocr_result["text"]
            
            if not text:
                logger.info(f"[{timestamp}] No text detected from {screen_name}")
                return
            
            # Create filename
            timestamp_str = timestamp.replace(':', '-').replace('.', '-')
            filename = f"{timestamp_str}_{screen_name}.json"
            filepath = self.summaries_dir / filename
            
            # Save OCR data
            await self._save_json_file(filepath, ocr_result)
            
            logger.info(f"[{timestamp}] ✅ OCR result saved to {filename}")
            logger.info(f"[{timestamp}] 📊 Screen: {screen_name}, Text: {len(text)} chars, Words: {ocr_result['word_count']}")
            
            # Update daily summary
            date_str = timestamp.split('T')[0]
            await self.update_daily_summary(date_str, ocr_result)
            
            # Store in ChromaDB
            await self.store_in_chroma(ocr_result)
            
        except Exception as error:
            logger.error(f"Error handling OCR result for {ocr_result.get('screen_name', 'unknown')}: {error}")
    
    async def _save_json_file(self, filepath: Path, data: Dict[str, Any]):
        """Save data to JSON file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    async def update_daily_summary(self, date_str: str, ocr_data: Dict[str, Any]):
        """Update the daily summary file."""
        try:
            daily_file = self.daily_dir / f"{date_str}.txt"
            
            # Read existing content or start fresh
            if daily_file.exists():
                with open(daily_file, 'r', encoding='utf-8') as f:
                    daily_content = f.read()
            else:
                daily_content = f"DAILY SUMMARY - {date_str}\n{'=' * 50}\n\n"
            
            # Add new entry
            time_str = datetime.fromisoformat(ocr_data["timestamp"].replace('Z', '+00:00')).strftime('%H:%M:%S')
            preview_text = ocr_data["text"][:100]
            if len(ocr_data["text"]) > 100:
                preview_text += "..."
            
            entry = (
                f"[{time_str}] {ocr_data['screen_name']} OCR Capture\n"
                f"Text: {preview_text}\n"
                f"Words: {ocr_data['word_count']}\n"
                f"{'-' * 40}\n"
            )
            
            daily_content += entry
            
            # Save updated content
            with open(daily_file, 'w', encoding='utf-8') as f:
                f.write(daily_content)
            
            logger.debug(f"Daily summary updated for {date_str} ({ocr_data['screen_name']})")
            
        except Exception as error:
            logger.error(f"Error updating daily summary: {error}")
    
    async def store_in_chroma(self, ocr_data: Dict[str, Any]):
        """Store OCR data in ChromaDB."""
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
                "active_app": "OCR Mode",
                "summary": f"OCR extracted {ocr_data['text_length']} characters",
                "extracted_text": ocr_data["text"],
                "task_category": "text_extraction",
                "productivity_score": 0,
                "user_generated_text": ocr_data["text"]
            }
            
            # Store in ChromaDB
            await chroma_client.add_document(
                collection_name="screenshots",
                doc_id=ocr_data["timestamp"] + "_" + ocr_data["screen_name"],
                content=content,
                metadata=metadata
            )
            
            logger.debug(f"Stored OCR data in ChromaDB: {ocr_data['timestamp']}")
            
        except Exception as error:
            logger.error(f"Error storing in ChromaDB: {error}")
    
    async def capture_all_screens(self):
        """Capture screenshots from all available screens."""
        try:
            # Detect screens if not already done
            if not screen_detector.screens:
                await screen_detector.detect_screens()
            
            if not screen_detector.screens:
                logger.warning("No screens detected")
                return
            
            timestamp = datetime.now().isoformat()
            logger.info(f"[{timestamp}] 📸 Capturing from {len(screen_detector.screens)} screen(s)...")
            
            # Capture each screen separately
            screen_captures = await screen_detector.capture_all_screens_separately()
            
            # Process each capture
            for screen_info, image in screen_captures:
                try:
                    # Save screenshot
                    timestamp_str = timestamp.replace(':', '-').replace('.', '-')
                    screenshot_path = self.screenshots_dir / f"{timestamp_str}_{screen_info.name}.png"
                    image.save(screenshot_path, "PNG")
                    logger.debug(f"Screenshot saved: {screenshot_path}")
                    
                    # Add to processing queue
                    self.processing_queue.append({
                        "image": image,
                        "screen_name": screen_info.name,
                        "timestamp": timestamp,
                        "processing": False
                    })
                    
                except Exception as error:
                    logger.error(f"Error processing {screen_info.name}: {error}")
                    continue
            
            # Process the OCR queue
            await self.process_ocr_queue()
            
        except Exception as error:
            logger.error(f"Error in capture_all_screens: {error}")
    
    async def process_ocr_queue(self):
        """Process pending OCR tasks."""
        # Get unprocessed items
        pending_items = [item for item in self.processing_queue if not item.get("processing", False)]
        
        # Process items concurrently
        tasks = []
        for item in pending_items:
            item["processing"] = True
            task = asyncio.create_task(self._process_queue_item(item))
            tasks.append(task)
        
        # Wait for all tasks to complete
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _process_queue_item(self, item: Dict[str, Any]):
        """Process a single queue item."""
        screenshot_path = None
        try:
            # Generate screenshot path for potential cleanup
            timestamp_str = item["timestamp"].replace(':', '-').replace('.', '-')
            screenshot_path = self.screenshots_dir / f"{timestamp_str}_{item['screen_name']}.png"
            
            # Perform OCR
            ocr_result = await self.process_screen_ocr(
                item["image"],
                item["screen_name"],
                item["timestamp"]
            )
            
            # Handle the result
            await self.handle_ocr_result(ocr_result)
            
            # Delete screenshot after successful OCR processing
            if screenshot_path and screenshot_path.exists():
                try:
                    screenshot_path.unlink()
                    logger.debug(f"Deleted screenshot: {screenshot_path}")
                except Exception as delete_error:
                    logger.warning(f"Could not delete screenshot {screenshot_path}: {delete_error}")
            
            # Remove from queue
            if item in self.processing_queue:
                self.processing_queue.remove(item)
                
        except Exception as error:
            logger.error(f"Error processing queue item for {item.get('screen_name', 'unknown')}: {error}")
            # Remove failed item from queue
            if item in self.processing_queue:
                self.processing_queue.remove(item)
            # Don't delete screenshot if OCR failed - might be useful for debugging
    
    async def start(self):
        """Start the OCR service."""
        try:
            logger.info("Starting Multi-Screen OCR service...")
            logger.info(f"Capture interval: {self.capture_interval} seconds")
            logger.info(f"Output directory: {self.summaries_dir}")
            logger.info(f"Max concurrent OCR: {self.max_concurrent_ocr}")
            
            await self.ensure_directories()
            
            # Initialize ChromaDB
            await chroma_client.init()
            
            
            # Detect screens
            await screen_detector.detect_screens()
            if not screen_detector.screens:
                raise Exception("No screens detected. Please check your display setup.")
            
            logger.info(f"Detected {len(screen_detector.screens)} screen(s): {[s.name for s in screen_detector.screens]}")
            
            # Initial capture
            await self.capture_all_screens()
            
            # Start continuous capture
            self.is_running = True
            logger.info("Multi-Screen OCR service started successfully")
            
            # Main loop
            while self.is_running:
                await asyncio.sleep(self.capture_interval)
                if self.is_running:  # Check again in case we were stopped
                    await self.capture_all_screens()
                    
            
        except Exception as error:
            logger.error(f"Error starting OCR service: {error}")
            raise
    
    async def stop(self):
        """Stop the OCR service."""
        logger.info("Stopping Multi-Screen OCR service...")
        
        self.is_running = False
        
        # Wait for current OCR operations to complete
        logger.info(f"Waiting for {len(self.processing_queue)} OCR operations to complete...")
        while self.processing_queue:
            await asyncio.sleep(0.1)
        
        logger.info("Multi-Screen OCR service stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of the OCR service."""
        return {
            "running": self.is_running,
            "last_capture": datetime.now().isoformat(),
            "interval": self.capture_interval,
            "summaries_dir": str(self.summaries_dir),
            "queued_ocr": len(self.processing_queue),
            "processing_ocr": len([item for item in self.processing_queue if item.get("processing", False)]),
            "available_screens": len(screen_detector.screens) if screen_detector.screens else 0
        }


# Global instance
ocr_processor = OCRProcessor()


async def main():
    """Main entry point for running the OCR processor."""
    import signal
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Handle shutdown signals
    def signal_handler(signum, frame):
        logger.info("Received shutdown signal")
        asyncio.create_task(ocr_processor.stop())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await ocr_processor.start()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as error:
        logger.error(f"Fatal error: {error}")
        return 1
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))
