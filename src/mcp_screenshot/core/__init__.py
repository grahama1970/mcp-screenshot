"""Core functionality for MCP Screenshot tool."""

from typing import Any, Dict, List, Optional, Tuple, Union
import base64
import io
from pathlib import Path

# Try to import screenshot libraries
try:
    from PIL import ImageGrab, Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import pyautogui
    HAS_PYAUTOGUI = True
except ImportError:
    HAS_PYAUTOGUI = False


class ScreenshotTool:
    """Tool for capturing screenshots."""
    
    def __init__(self, backend: str = "auto"):
        """Initialize screenshot tool.
        
        Args:
            backend: Screenshot backend to use ("pil", "pyautogui", or "auto")
        """
        self.backend = self._select_backend(backend)
        
    def _select_backend(self, backend: str) -> str:
        """Select the screenshot backend."""
        if backend == "auto":
            if HAS_PIL:
                return "pil"
            elif HAS_PYAUTOGUI:
                return "pyautogui"
            else:
                raise ImportError("No screenshot backend available. Install pillow or pyautogui.")
        elif backend == "pil" and not HAS_PIL:
            raise ImportError("PIL not available. Install pillow.")
        elif backend == "pyautogui" and not HAS_PYAUTOGUI:
            raise ImportError("pyautogui not available. Install pyautogui.")
        return backend
    
    def capture(self, region: Optional[Tuple[int, int, int, int]] = None) -> bytes:
        """Capture a screenshot.
        
        Args:
            region: Optional (x, y, width, height) tuple for region capture
            
        Returns:
            Screenshot as PNG bytes
        """
        if self.backend == "pil":
            img = ImageGrab.grab(bbox=region)
        else:  # pyautogui
            if region:
                img = pyautogui.screenshot(region=region)
            else:
                img = pyautogui.screenshot()
        
        # Convert to PNG bytes
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()
    
    def capture_base64(self, region: Optional[Tuple[int, int, int, int]] = None) -> str:
        """Capture a screenshot and return as base64 string."""
        png_bytes = self.capture(region)
        return base64.b64encode(png_bytes).decode('utf-8')


class ScreenshotProcessor:
    """Process and analyze screenshots."""
    
    def __init__(self):
        """Initialize processor."""
        self.tool = ScreenshotTool()
    
    def capture_and_save(self, filepath: Union[str, Path], 
                        region: Optional[Tuple[int, int, int, int]] = None) -> Path:
        """Capture screenshot and save to file."""
        filepath = Path(filepath)
        png_bytes = self.tool.capture(region)
        filepath.write_bytes(png_bytes)
        return filepath
    
    def get_screen_info(self) -> Dict[str, Any]:
        """Get information about the screen."""
        info = {
            "backend": self.tool.backend,
            "has_pil": HAS_PIL,
            "has_pyautogui": HAS_PYAUTOGUI
        }
        
        if HAS_PYAUTOGUI:
            size = pyautogui.size()
            info["screen_width"] = size.width
            info["screen_height"] = size.height
        
        return info


# For backward compatibility
screenshot_tool = ScreenshotTool()
capture_screenshot = screenshot_tool.capture
capture_screenshot_base64 = screenshot_tool.capture_base64

__all__ = [
    "ScreenshotTool",
    "ScreenshotProcessor", 
    "screenshot_tool",
    "capture_screenshot",
    "capture_screenshot_base64",
]
