"""MCP Screenshot - Model Context Protocol screenshot tool."""

from .core import (
    ScreenshotTool,
    ScreenshotProcessor,
    screenshot_tool,
    capture_screenshot,
    capture_screenshot_base64,
    describe_image_content,
    analyze_screenshot,
    get_screenshot_tool,
    capture_region,
)

__version__ = "0.1.0"

# Compatibility alias
def verify_d3_visualization(screenshot_data: bytes) -> dict:
    """Verify D3 visualization (placeholder for backward compatibility)."""
    return analyze_screenshot(screenshot_data)

__all__ = [
    "ScreenshotTool",
    "ScreenshotProcessor", 
    "screenshot_tool",
    "capture_screenshot",
    "capture_screenshot_base64",
    "describe_image_content",
    "analyze_screenshot",
    "verify_d3_visualization",
    "get_screenshot_tool",
    "capture_region",
]
