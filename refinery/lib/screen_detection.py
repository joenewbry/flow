"""
Screen detection and screenshot capture for Flow CLI
Handles multi-monitor setups and screenshot collection
"""

import logging
import platform
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image
import pyscreenshot as ImageGrab
import pyautogui

logger = logging.getLogger(__name__)


class ScreenInfo:
    def __init__(self, index: int, name: str, width: int, height: int, 
                 x: int = 0, y: int = 0, is_main: bool = False):
        self.index = index
        self.name = name
        self.width = width
        self.height = height
        self.x = x
        self.y = y
        self.is_main = is_main
        self.resolution = f"{width}x{height}"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "name": self.name,
            "width": self.width,
            "height": self.height,
            "x": self.x,
            "y": self.y,
            "is_main": self.is_main,
            "resolution": self.resolution
        }


class ScreenDetector:
    def __init__(self):
        self.screens: List[ScreenInfo] = []
        self.main_screen: Optional[ScreenInfo] = None
        self.screen_count = 0
        self._platform = platform.system().lower()
        
        # Disable PyAutoGUI fail-safe
        pyautogui.FAILSAFE = False
    
    async def detect_screens(self) -> List[ScreenInfo]:
        """Detect all available screens/monitors."""
        try:
            self.screens = []
            
            if self._platform == "darwin":  # macOS
                self._detect_screens_macos()
            elif self._platform == "windows":
                self._detect_screens_windows()
            elif self._platform == "linux":
                self._detect_screens_linux()
            else:
                # Fallback to single screen
                self._detect_single_screen()
            
            self.screen_count = len(self.screens)
            
            # Set main screen (first one or the one at 0,0)
            if self.screens:
                self.main_screen = self.screens[0]
                for screen in self.screens:
                    if screen.x == 0 and screen.y == 0:
                        self.main_screen = screen
                        screen.is_main = True
                        break
                else:
                    self.screens[0].is_main = True
                    self.main_screen = self.screens[0]
            
            logger.info(f"Detected {self.screen_count} screen(s)")
            return self.screens
            
        except Exception as error:
            logger.error(f"Error detecting screens: {error}")
            # Fallback to single screen
            self._detect_single_screen()
            return self.screens
    
    def _detect_screens_macos(self):
        """Detect screens on macOS."""
        try:
            import Quartz
            
            # Get online displays
            online_displays = Quartz.CGGetOnlineDisplayList(10, None, None)[1]
            
            for i, display_id in enumerate(online_displays):
                bounds = Quartz.CGDisplayBounds(display_id)
                
                screen = ScreenInfo(
                    index=i,
                    name=f"Display_{i + 1}",
                    width=int(bounds.size.width),
                    height=int(bounds.size.height),
                    x=int(bounds.origin.x),
                    y=int(bounds.origin.y),
                    is_main=(Quartz.CGDisplayIsMain(display_id) == 1)
                )
                
                self.screens.append(screen)
                
        except ImportError:
            logger.warning("Quartz not available, falling back to PyAutoGUI")
            self._detect_with_pyautogui()
        except Exception as error:
            logger.error(f"Error detecting macOS screens: {error}")
            self._detect_single_screen()
    
    def _detect_screens_windows(self):
        """Detect screens on Windows."""
        try:
            import win32api
            import win32con
            
            monitors = win32api.EnumDisplayMonitors()
            
            for i, (monitor, dc, rect) in enumerate(monitors):
                x, y, right, bottom = rect
                width = right - x
                height = bottom - y
                
                # Get monitor info
                monitor_info = win32api.GetMonitorInfo(monitor)
                is_primary = monitor_info['Flags'] & win32con.MONITORINFOF_PRIMARY
                
                screen = ScreenInfo(
                    index=i,
                    name=f"Monitor_{i + 1}",
                    width=width,
                    height=height,
                    x=x,
                    y=y,
                    is_main=bool(is_primary)
                )
                
                self.screens.append(screen)
                
        except ImportError:
            logger.warning("win32api not available, falling back to PyAutoGUI")
            self._detect_with_pyautogui()
        except Exception as error:
            logger.error(f"Error detecting Windows screens: {error}")
            self._detect_single_screen()
    
    def _detect_screens_linux(self):
        """Detect screens on Linux."""
        try:
            # Try using Xlib
            from Xlib import display
            
            d = display.Display()
            screen = d.screen()
            
            # For simplicity, just get the main screen
            # Linux multi-monitor detection is complex and varies by DE
            screen_info = ScreenInfo(
                index=0,
                name="Screen_1",
                width=screen.width_in_pixels,
                height=screen.height_in_pixels,
                x=0,
                y=0,
                is_main=True
            )
            
            self.screens.append(screen_info)
            
        except ImportError:
            logger.warning("Xlib not available, falling back to PyAutoGUI")
            self._detect_with_pyautogui()
        except Exception as error:
            logger.error(f"Error detecting Linux screens: {error}")
            self._detect_single_screen()
    
    def _detect_with_pyautogui(self):
        """Fallback detection using PyAutoGUI."""
        try:
            width, height = pyautogui.size()
            
            screen = ScreenInfo(
                index=0,
                name="Primary_Screen",
                width=width,
                height=height,
                x=0,
                y=0,
                is_main=True
            )
            
            self.screens.append(screen)
            
        except Exception as error:
            logger.error(f"Error with PyAutoGUI detection: {error}")
            self._detect_single_screen()
    
    def _detect_single_screen(self):
        """Fallback to single screen detection."""
        # Default screen size - will be updated on first screenshot
        screen = ScreenInfo(
            index=0,
            name="Default_Screen",
            width=1920,
            height=1080,
            x=0,
            y=0,
            is_main=True
        )
        
        self.screens = [screen]
        self.main_screen = screen
        logger.warning("Using fallback single screen detection")
    
    def get_screen_info(self) -> Dict[str, Any]:
        """Get screen information summary."""
        return {
            "screen_count": self.screen_count,
            "screens": [screen.to_dict() for screen in self.screens],
            "main_screen": self.main_screen.to_dict() if self.main_screen else None,
            "platform": self._platform
        }
    
    def get_main_screen(self) -> Optional[ScreenInfo]:
        """Get the main screen."""
        return self.main_screen
    
    async def capture_screenshot(self, screen_index: Optional[int] = None, 
                                main_screen_only: bool = False) -> Image.Image:
        """Capture screenshot from specified screen or all screens."""
        try:
            if main_screen_only or screen_index is not None:
                # Capture specific screen
                target_screen = self.main_screen if main_screen_only else self.screens[screen_index]
                
                if target_screen:
                    bbox = (
                        target_screen.x,
                        target_screen.y,
                        target_screen.x + target_screen.width,
                        target_screen.y + target_screen.height
                    )
                    
                    screenshot = ImageGrab.grab(bbox=bbox)
                    logger.debug(f"Captured screenshot from {target_screen.name}")
                    return screenshot
            
            # Capture all screens (default)
            screenshot = ImageGrab.grab()
            logger.debug("Captured screenshot from all screens")
            return screenshot
            
        except Exception as error:
            logger.error(f"Error capturing screenshot: {error}")
            # Try fallback capture
            try:
                screenshot = pyautogui.screenshot()
                logger.debug("Used PyAutoGUI fallback for screenshot")
                return screenshot
            except Exception as fallback_error:
                logger.error(f"Fallback screenshot failed: {fallback_error}")
                raise Exception(f"Screenshot capture failed: {error}")
    
    async def capture_all_screens_separately(self) -> List[Tuple[ScreenInfo, Image.Image]]:
        """Capture screenshots from each screen separately."""
        screenshots = []
        
        for screen in self.screens:
            try:
                bbox = (
                    screen.x,
                    screen.y,
                    screen.x + screen.width,
                    screen.y + screen.height
                )
                
                screenshot = ImageGrab.grab(bbox=bbox)
                screenshots.append((screen, screenshot))
                logger.debug(f"Captured screenshot from {screen.name}")
                
            except Exception as error:
                logger.error(f"Error capturing from {screen.name}: {error}")
                continue
        
        return screenshots


# Global instance
screen_detector = ScreenDetector()
