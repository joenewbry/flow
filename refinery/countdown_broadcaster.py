"""
Countdown broadcaster for screen capture system.
Sends countdown updates to the dashboard via WebSocket.
"""

import asyncio
import json
import time
from typing import Optional
import aiohttp


class CountdownBroadcaster:
    """Broadcasts countdown to dashboard WebSocket."""
    
    def __init__(self, dashboard_url: str = "http://localhost:8081", interval: int = 60):
        self.dashboard_url = dashboard_url
        self.interval = interval
        self.last_capture_time = time.time()
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
    
    def get_seconds_remaining(self) -> int:
        """Calculate seconds remaining until next capture."""
        if not self.is_running:
            return 0
        
        elapsed = time.time() - self.last_capture_time
        remaining = self.interval - elapsed
        return max(0, int(remaining))
    
    async def broadcast_loop(self):
        """Continuously broadcast countdown via HTTP to dashboard."""
        session = aiohttp.ClientSession()
        
        try:
            while self.is_running:
                try:
                    seconds_remaining = self.get_seconds_remaining()
                    
                    # Send to dashboard API (dashboard will broadcast via WebSocket)
                    await session.post(
                        f"{self.dashboard_url}/api/broadcast-countdown",
                        json={
                            "seconds_remaining": seconds_remaining,
                            "timestamp": time.time()
                        }
                    )
                except Exception as e:
                    print(f"Error broadcasting countdown: {e}")
                
                await asyncio.sleep(1)
        finally:
            await session.close()
    
    def reset(self):
        """Reset countdown after a screenshot is taken."""
        self.last_capture_time = time.time()
    
    def start(self):
        """Start the countdown broadcaster."""
        if not self.is_running:
            self.is_running = True
            self.last_capture_time = time.time()
            self._task = asyncio.create_task(self.broadcast_loop())
    
    def stop(self):
        """Stop the countdown broadcaster."""
        self.is_running = False
        if self._task:
            self._task.cancel()


# Example usage in your screen capture script:
"""
# In refinery/run.py:

from countdown_broadcaster import CountdownBroadcaster

# Create broadcaster
countdown = CountdownBroadcaster(dashboard_url="http://localhost:8081", interval=60)

async def main():
    # Start countdown
    countdown.start()
    
    while True:
        # Take screenshot
        screenshot = take_screenshot()
        process_ocr(screenshot)
        
        # Reset countdown after capture
        countdown.reset()
        
        # Wait for next capture
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
"""

