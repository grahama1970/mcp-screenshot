"""Core functionality for MCP Screenshot tool."""

# Import actual implementations from the modules
from .capture import capture_screenshot, capture_screenshot_base64
from .description import describe_image_content
from .d3_verification import verify_d3_visualization
from .compare import compare_screenshots
from .history import ScreenshotHistory
from .utils import get_screenshot_tool, save_screenshot, load_screenshot
from .annotate import annotate_screenshot
from .batch import BatchScreenshotProcessor

# Re-export commonly used functions
__all__ = [
    "capture_screenshot",
    "capture_screenshot_base64", 
    "describe_image_content",
    "verify_d3_visualization",
    "compare_screenshots",
    "ScreenshotHistory",
    "get_screenshot_tool",
    "save_screenshot",
    "load_screenshot",
    "annotate_screenshot",
    "BatchScreenshotProcessor",
]
