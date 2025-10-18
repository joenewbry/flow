#!/usr/bin/env python3
"""Test screenshot capture and OCR to debug the issue."""

import asyncio
from pathlib import Path
from datetime import datetime
from PIL import Image
import pytesseract
from lib.screen_detection import screen_detector

async def test_screenshot_and_ocr():
    """Test screenshot capture and OCR."""
    
    # Create test directory
    test_dir = Path("data/test_images")
    test_dir.mkdir(parents=True, exist_ok=True)
    
    print("Detecting screens...")
    screens = await screen_detector.detect_screens()
    print(f"Found {len(screens)} screen(s)")
    
    for screen in screens:
        print(f"\nScreen: {screen.name}")
        print(f"  Resolution: {screen.width}x{screen.height}")
        print(f"  Position: ({screen.x}, {screen.y})")
        print(f"  Is main: {screen.is_main}")
    
    print("\nCapturing screenshots...")
    screen_captures = await screen_detector.capture_all_screens_separately()
    
    for screen_info, image in screen_captures:
        timestamp = datetime.now().isoformat().replace(':', '-').replace('.', '-')
        
        # Save the image
        image_path = test_dir / f"{timestamp}_{screen_info.name}.png"
        image.save(image_path)
        print(f"\nSaved screenshot to: {image_path}")
        print(f"  Image size: {image.size}")
        print(f"  Image mode: {image.mode}")
        
        # Test OCR
        print(f"  Running OCR on {screen_info.name}...")
        try:
            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            text = pytesseract.image_to_string(image, lang='eng')
            text = text.strip()
            
            print(f"  OCR Text length: {len(text)} characters")
            print(f"  Word count: {len([w for w in text.split() if w.strip()])}")
            
            if text:
                # Show first 200 chars of text
                preview = text[:200].replace('\n', ' ')
                print(f"  Text preview: {preview}...")
            else:
                print(f"  WARNING: No text detected!")
                
        except Exception as e:
            print(f"  OCR Error: {e}")
    
    print("\nTest complete! Check the data/test_images directory for screenshots.")

if __name__ == "__main__":
    asyncio.run(test_screenshot_and_ocr())



