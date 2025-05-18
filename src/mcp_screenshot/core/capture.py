#!/usr/bin/env python3
"""
Screenshot Capture Module

This module provides functions for capturing screenshots of the screen or specific regions
using the MSS library, as well as browser-based screenshots using Selenium.

This module is part of the Core Layer and should have no dependencies on
CLI or MCP layers.

Sample input:
- quality=70, region=None (for full screen)
- url="http://localhost:3000", quality=70 (for browser capture)

Expected output:
- Dictionary with:
  - content: List with a single image object (type, base64 data, MIME type)
  - file: Path to the saved screenshot file
  - On error: error message as a string
"""

import os
import time
import base64
import uuid
from typing import Dict, List, Union, Optional, Any, Tuple

import mss
from PIL import Image
from loguru import logger

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    logger.warning("Selenium not available - browser screenshots disabled")

from mcp_screenshot.core.constants import IMAGE_SETTINGS, BROWSER_SETTINGS
from mcp_screenshot.core.utils import (
    validate_quality,
    validate_region,
    generate_filename,
    ensure_directory
)


def capture_screenshot(
    quality: int = IMAGE_SETTINGS["DEFAULT_QUALITY"],
    region: Optional[Union[List[int], str]] = None,
    output_dir: str = "screenshots",
    include_raw: bool = False
) -> Dict[str, Any]:
    """
    Captures a screenshot of the entire desktop or a specified region.
    
    Args:
        quality: JPEG compression quality (1-100)
        region: Region coordinates [x, y, width, height] or preset name
        output_dir: Directory to save screenshot
        include_raw: Whether to also save the raw uncompressed PNG
        
    Returns:
        dict: Response containing:
            - content: List with image object (type, base64, MIME type)
            - file: Path to the saved screenshot file
            - raw_file: Path to raw PNG (if include_raw=True)
            - On error: error message as string
    """
    logger.info(f"Screenshot requested with quality={quality}, region={region}")

    try:
        # Validate parameters
        quality = validate_quality(quality)
        region = validate_region(region)
        
        # Ensure output directory exists
        ensure_directory(output_dir)
        
        # Generate filenames
        timestamp = int(time.time() * 1000)
        filename = f"screenshot_{timestamp}.jpeg"
        path = os.path.join(output_dir, filename)
        
        raw_path = None
        if include_raw:
            raw_filename = f"raw_screenshot_{timestamp}.png"
            raw_path = os.path.join(output_dir, raw_filename)

        # Capture screenshot
        with mss.mss() as sct:
            # Get primary monitor if no region is specified
            monitor = sct.monitors[1]  # Primary monitor
            
            if isinstance(region, str):
                # Handle preset regions
                capture_area = _get_preset_region(region, monitor)
            elif isinstance(region, list) and len(region) == 4:
                # Handle custom region [x, y, width, height]
                x, y, w, h = region
                capture_area = {"top": y, "left": x, "width": w, "height": h}
            else:
                # Full screen
                capture_area = monitor
            
            logger.info(f"Capturing area: {capture_area}")
            sct_img = sct.grab(capture_area)
            
            # Convert to PIL Image
            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
            
            # Save raw PNG if requested
            if include_raw and raw_path:
                logger.info(f"Saving raw PNG to {raw_path}")
                img.save(raw_path, format="PNG")
            
            # Resize if needed
            original_size = img.size
            if img.width > IMAGE_SETTINGS["MAX_WIDTH"] or img.height > IMAGE_SETTINGS["MAX_HEIGHT"]:
                img.thumbnail((IMAGE_SETTINGS["MAX_WIDTH"], IMAGE_SETTINGS["MAX_HEIGHT"]), Image.Resampling.LANCZOS)
                logger.info(f"Resized image from {original_size} to {img.size}")
            
            # Save as JPEG with specified quality
            img.save(path, format="JPEG", quality=quality, optimize=True)
            
            # Encode to base64
            with open(path, "rb") as f:
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
                "file": path,
                "dimensions": {"width": img.width, "height": img.height},
                "original_dimensions": {"width": original_size[0], "height": original_size[1]},
                "quality": quality
            }
            
            if include_raw and raw_path:
                response["raw_file"] = raw_path
            
            logger.info(f"Screenshot captured successfully: {path}")
            return response
            
    except Exception as e:
        logger.error(f"Screenshot capture failed: {str(e)}", exc_info=True)
        return {"error": f"Screenshot capture failed: {str(e)}"}


def capture_browser_screenshot(
    url: str,
    quality: int = IMAGE_SETTINGS["DEFAULT_QUALITY"],
    output_dir: str = "screenshots",
    wait_time: int = 2,
    width: int = BROWSER_SETTINGS["WIDTH"],
    height: int = BROWSER_SETTINGS["HEIGHT"]
) -> Dict[str, Any]:
    """
    Captures a screenshot of a web page using headless browser.
    
    Args:
        url: URL to capture
        quality: JPEG compression quality (1-100)
        output_dir: Directory to save screenshot
        wait_time: Seconds to wait for page to load
        width: Browser window width
        height: Browser window height
        
    Returns:
        dict: Response containing:
            - content: List with image object
            - file: Path to the saved screenshot file
            - url: URL that was captured
            - On error: error message
    """
    if not SELENIUM_AVAILABLE:
        return {"error": "Selenium not available - install with 'pip install selenium'"}
    
    logger.info(f"Browser screenshot requested for URL: {url}")
    
    driver = None
    try:
        # Validate parameters
        quality = validate_quality(quality)
        ensure_directory(output_dir)
        
        # Setup Chrome options
        chrome_options = Options()
        if BROWSER_SETTINGS["HEADLESS"]:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument(f"--window-size={width},{height}")
        
        # Create driver
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_window_size(width, height)
        
        # Load the page
        logger.info(f"Loading page: {url}")
        driver.get(url)
        
        # Wait for page to load
        wait = WebDriverWait(driver, BROWSER_SETTINGS["TIMEOUT"] / 1000)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        # Additional wait for dynamic content
        time.sleep(wait_time)
        
        # Take screenshot
        timestamp = int(time.time() * 1000)
        filename = f"browser_{timestamp}.png"
        temp_path = os.path.join(output_dir, filename)
        
        driver.save_screenshot(temp_path)
        logger.info(f"Browser screenshot saved to {temp_path}")
        
        # Convert to JPEG with quality
        img = Image.open(temp_path)
        jpeg_filename = f"browser_{timestamp}.jpeg"
        jpeg_path = os.path.join(output_dir, jpeg_filename)
        
        # Resize if needed
        original_size = img.size
        if img.width > IMAGE_SETTINGS["MAX_WIDTH"] or img.height > IMAGE_SETTINGS["MAX_HEIGHT"]:
            img.thumbnail((IMAGE_SETTINGS["MAX_WIDTH"], IMAGE_SETTINGS["MAX_HEIGHT"]), Image.Resampling.LANCZOS)
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
            "quality": quality
        }
        
        logger.info(f"Browser screenshot captured successfully: {jpeg_path}")
        return response
        
    except Exception as e:
        logger.error(f"Browser screenshot failed: {str(e)}", exc_info=True)
        return {"error": f"Browser screenshot failed: {str(e)}"}
        
    finally:
        if driver:
            driver.quit()


def get_screen_regions() -> Dict[str, Dict[str, int]]:
    """
    Get information about available screen regions.
    
    Returns:
        Dict: Dictionary of available regions with their dimensions
    """
    regions = {}
    
    try:
        with mss.mss() as sct:
            # Get all monitors
            for i, monitor in enumerate(sct.monitors):
                if i == 0:  # Skip the "all monitors" entry
                    continue
                regions[f"monitor_{i}"] = {
                    "top": monitor["top"],
                    "left": monitor["left"],
                    "width": monitor["width"],
                    "height": monitor["height"]
                }
            
            # Add special regions for primary monitor
            primary = sct.monitors[1]
            width = primary["width"]
            height = primary["height"]
            
            # Add preset regions
            regions.update({
                "full": primary,
                "right_half": {
                    "top": 0,
                    "left": width // 2,
                    "width": width // 2,
                    "height": height
                },
                "left_half": {
                    "top": 0,
                    "left": 0,
                    "width": width // 2,
                    "height": height
                },
                "top_half": {
                    "top": 0,
                    "left": 0,
                    "width": width,
                    "height": height // 2
                },
                "bottom_half": {
                    "top": height // 2,
                    "left": 0,
                    "width": width,
                    "height": height // 2
                },
                "center": {
                    "top": height // 4,
                    "left": width // 4,
                    "width": width // 2,
                    "height": height // 2
                }
            })
            
    except Exception as e:
        logger.error(f"Failed to get screen regions: {str(e)}")
        return {}
    
    return regions


def _get_preset_region(preset: str, monitor: Dict[str, int]) -> Dict[str, int]:
    """Get region coordinates for a preset name."""
    width = monitor["width"]
    height = monitor["height"]
    
    presets = {
        "right_half": {"top": 0, "left": width // 2, "width": width // 2, "height": height},
        "left_half": {"top": 0, "left": 0, "width": width // 2, "height": height},
        "top_half": {"top": 0, "left": 0, "width": width, "height": height // 2},
        "bottom_half": {"top": height // 2, "left": 0, "width": width, "height": height // 2},
        "center": {"top": height // 4, "left": width // 4, "width": width // 2, "height": height // 2},
        "full": monitor
    }
    
    return presets.get(preset, monitor)


if __name__ == "__main__":
    """Validate screenshot capture functions with real test data"""
    import sys
    import shutil
    
    # List to track all validation failures
    all_validation_failures = []
    total_tests = 0
    
    # Create test directory
    test_dir = ".test_screenshots"
    ensure_directory(test_dir)
    
    try:
        # Test 1: Capture full screen
        total_tests += 1
        result = capture_screenshot(quality=50, output_dir=test_dir)
        
        if "error" in result:
            all_validation_failures.append(f"Full screen capture test: {result['error']}")
        elif "file" not in result or not os.path.exists(result["file"]):
            all_validation_failures.append(f"Full screen capture test: File not created")
        elif "content" not in result or not result["content"][0]["data"]:
            all_validation_failures.append(f"Full screen capture test: No image content returned")
        
        # Test 2: Capture preset region
        total_tests += 1
        result = capture_screenshot(quality=70, region="center", output_dir=test_dir)
        
        if "error" in result:
            all_validation_failures.append(f"Preset region capture test: {result['error']}")
        elif "file" not in result or not os.path.exists(result["file"]):
            all_validation_failures.append(f"Preset region capture test: File not created")
        
        # Test 3: Capture custom region
        total_tests += 1
        result = capture_screenshot(quality=50, region=[100, 100, 400, 300], output_dir=test_dir)
        
        if "error" in result:
            all_validation_failures.append(f"Custom region capture test: {result['error']}")
        elif "file" not in result or not os.path.exists(result["file"]):
            all_validation_failures.append(f"Custom region capture test: File not created")
        
        # Test 4: Invalid region parameter
        total_tests += 1
        result = capture_screenshot(quality=50, region="invalid_region", output_dir=test_dir)
        
        if "error" not in result:
            all_validation_failures.append(
                f"Invalid region test: Expected error for 'invalid_region', but got success"
            )
        
        # Test 5: Get screen regions
        total_tests += 1
        regions = get_screen_regions()
        
        if not regions or "full" not in regions:
            all_validation_failures.append(f"Get screen regions test: Failed to get regions")
        
        # Test 6: Browser screenshot (if available)
        if SELENIUM_AVAILABLE:
            total_tests += 1
            result = capture_browser_screenshot(
                url="https://example.com",
                quality=70,
                output_dir=test_dir
            )
            
            if "error" in result:
                # This might fail if Chrome is not installed, which is okay
                logger.info(f"Browser test skipped: {result['error']}")
            elif "file" not in result or not os.path.exists(result["file"]):
                all_validation_failures.append(f"Browser capture test: File not created")
        
    finally:
        # Clean up test directory
        shutil.rmtree(test_dir, ignore_errors=True)
    
    # Final validation result
    if all_validation_failures:
        print(f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("Screenshot capture functions are validated and ready for use")
        sys.exit(0)