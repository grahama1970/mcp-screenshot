"""
Module: playwright_capture.py
Description: Functions for playwright capture operations

External Dependencies:
- base64: [Documentation URL]
- playwright: [Documentation URL]
- loguru: [Documentation URL]
- PIL: [Documentation URL]
- mcp_screenshot: [Documentation URL]

Sample Input:
>>> # Add specific examples based on module functionality

Expected Output:
>>> # Add expected output examples

Example Usage:
>>> # Add usage examples
"""

#!/usr/bin/env python3
"""
Playwright-based screenshot capture with full-page support.

This module provides browser screenshot capabilities using Playwright,
including full-page scrolling screenshots.
"""

import os
import time
import base64
from typing import Dict, Any, Optional, Tuple
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

from loguru import logger
from PIL import Image

from mcp_screenshot.core.constants import IMAGE_SETTINGS, BROWSER_SETTINGS
from mcp_screenshot.core.utils import (
    validate_quality,
    ensure_directory
)


def capture_browser_screenshot_playwright(
    url: str,
    output_dir: str = "./screenshots",
    wait_time: int = 3,
    quality: int = IMAGE_SETTINGS["DEFAULT_QUALITY"],
    width: int = 1920,
    height: int = 1080,
    full_page: bool = True
) -> Dict[str, Any]:
    """
    Capture a screenshot of a webpage using Playwright with full-page support.
    
    Args:
        url: URL to capture
        output_dir: Directory to save the screenshot
        wait_time: Seconds to wait for page load
        quality: JPEG compression quality (30-90)
        width: Browser viewport width
        height: Browser viewport height
        full_page: Whether to capture the full scrollable page
        
    Returns:
        dict: Screenshot result with file path, dimensions, and base64 content
    """
    if not PLAYWRIGHT_AVAILABLE:
        return {"error": "Playwright not available - install with 'pip install playwright'"}
    
    logger.info(f"Playwright screenshot requested for URL: {url}, full_page: {full_page}")
    
    try:
        # Validate parameters
        quality = validate_quality(quality)
        ensure_directory(output_dir)
        
        with sync_playwright() as p:
            # Launch browser
            browser = p.chromium.launch(
                headless=BROWSER_SETTINGS.get("HEADLESS", True),
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            
            # Create context with viewport
            context = browser.new_context(
                viewport={'width': width, 'height': height}
            )
            
            # Create page
            page = context.new_page()
            
            # Navigate to URL
            logger.info(f"Loading page: {url}")
            page.goto(url, wait_until='networkidle')
            
            # Additional wait for dynamic content
            page.wait_for_timeout(wait_time * 1000)
            
            # Take screenshot
            timestamp = int(time.time() * 1000)
            filename = f"browser_{timestamp}.png"
            temp_path = os.path.join(output_dir, filename)
            
            # Capture with full_page option
            page.screenshot(
                path=temp_path,
                full_page=full_page
            )
            
            logger.info(f"Playwright screenshot saved to {temp_path}")
            
            # Convert to JPEG with quality
            img = Image.open(temp_path)
            jpeg_filename = f"browser_{timestamp}.jpeg"
            jpeg_path = os.path.join(output_dir, jpeg_filename)
            
            # Get original dimensions before any resizing
            original_size = img.size
            logger.info(f"Original screenshot size: {original_size}")
            
            # For full-page screenshots, we might have very large images
            # Only resize if it exceeds max dimensions
            if img.width > IMAGE_SETTINGS["MAX_WIDTH"] or img.height > IMAGE_SETTINGS["MAX_HEIGHT"]:
                # Calculate scaling factor to fit within max dimensions
                scale_factor = min(
                    IMAGE_SETTINGS["MAX_WIDTH"] / img.width,
                    IMAGE_SETTINGS["MAX_HEIGHT"] / img.height
                )
                new_width = int(img.width * scale_factor)
                new_height = int(img.height * scale_factor)
                
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                logger.info(f"Resized image from {original_size} to {img.size}")
            
            # Save as JPEG
            img.save(jpeg_path, format="JPEG", quality=quality, optimize=True)
            
            # Remove temp PNG
            os.remove(temp_path)
            
            # Encode to base64
            with open(jpeg_path, "rb") as f:
                img_bytes = f.read()
                img_b64 = base64.b64encode(img_bytes).decode("utf-8")
            
            # Create response
            response = {
                "content": [
                    {
                        "type": "image",
                        "data": img_b64,
                        "mimeType": "image/jpeg"
                    }
                ],
                "file": jpeg_path,
                "url": url,
                "dimensions": {"width": img.width, "height": img.height},
                "original_dimensions": {"width": original_size[0], "height": original_size[1]},
                "full_page": full_page,
                "quality": quality
            }
            
            logger.info(f"Playwright screenshot captured successfully: {jpeg_path}")
            
            # Clean up
            browser.close()
            
            return response
            
    except Exception as e:
        logger.error(f"Playwright screenshot failed: {str(e)}", exc_info=True)
        return {"error": f"Playwright screenshot failed: {str(e)}"}


if __name__ == "__main__":
    """Self-validation tests for Playwright capture."""
    if PLAYWRIGHT_AVAILABLE:
        # Test basic capture
        result = capture_browser_screenshot_playwright(
            "https://example.com",
            full_page=True
        )
        print(f"Test capture: {'success' if 'file' in result else 'failed'}")
        
        # Test with custom dimensions
        result = capture_browser_screenshot_playwright(
            "https://example.com",
            width=1280,
            height=720,
            full_page=False
        )
        print(f"Custom dimensions test: {'success' if 'file' in result else 'failed'}")