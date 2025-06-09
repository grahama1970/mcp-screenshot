"""
Module: utils.py
Description: Utility functions and helpers for utils

External Dependencies:
- loguru: [Documentation URL]
- mcp_screenshot: [Documentation URL]
- tempfile: [Documentation URL]

Sample Input:
>>> # Add specific examples based on module functionality

Expected Output:
>>> # Add expected output examples

Example Usage:
>>> # Add usage examples
"""

#!/usr/bin/env python3
"""
Utility Functions for MCP Screenshot Tool

This module provides utility functions used throughout the screenshot functionality,
including validation, file operations, and credential management.

This module is part of the Core Layer and should have no dependencies on
CLI or MCP layers.

Sample input:
- Various utility function inputs

Expected output:
- Validated/processed values or error responses
"""

import os
import json
import time
import uuid
from typing import Dict, List, Union, Optional, Any
from loguru import logger

from mcp_screenshot.core.constants import IMAGE_SETTINGS, REGION_PRESETS


def validate_quality(quality: int) -> int:
    """
    Validate and clamp quality parameter within acceptable range.
    
    Args:
        quality: JPEG compression quality (1-100)
        
    Returns:
        int: Validated quality value
    """
    original = quality
    quality = max(IMAGE_SETTINGS["MIN_QUALITY"], 
                  min(quality, IMAGE_SETTINGS["MAX_QUALITY"]))
    
    if quality != original:
        logger.info(
            f"Adjusted quality from {original} to {quality} "
            f"(min={IMAGE_SETTINGS['MIN_QUALITY']}, max={IMAGE_SETTINGS['MAX_QUALITY']})"
        )
    
    return quality


def validate_region(region: Optional[Union[List[int], str]]) -> Optional[Union[List[int], str]]:
    """
    Validate region parameter.
    
    Args:
        region: Region specification (coordinates, preset name, or None)
        
    Returns:
        Validated region or None
        
    Raises:
        ValueError: If region is invalid
    """
    if region is None:
        return None
    
    if isinstance(region, str):
        if region not in REGION_PRESETS:
            raise ValueError(f"Invalid region preset: {region}. Valid presets: {list(REGION_PRESETS.keys())}")
        return region
    
    if isinstance(region, list):
        if len(region) != 4:
            raise ValueError(f"Region coordinates must have 4 values [x, y, width, height], got {len(region)}")
        
        # Ensure all values are non-negative integers
        for i, value in enumerate(region):
            if not isinstance(value, int) or value < 0:
                raise ValueError(f"Region coordinate {i} must be a non-negative integer, got {value}")
        
        # Ensure width and height are positive
        if region[2] <= 0 or region[3] <= 0:
            raise ValueError("Region width and height must be positive")
        
        return region
    
    raise ValueError(f"Invalid region type: {type(region)}. Must be string preset or list of coordinates.")


def generate_filename(prefix: str = "screenshot", extension: str = "jpeg") -> str:
    """
    Generate a unique filename with timestamp.
    
    Args:
        prefix: Filename prefix
        extension: File extension
        
    Returns:
        str: Generated filename
    """
    timestamp = int(time.time() * 1000)
    unique_id = str(uuid.uuid4())[:8]
    return f"{prefix}_{timestamp}_{unique_id}.{extension}"


def ensure_directory(directory: str) -> None:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        directory: Directory path to ensure exists
    """
    os.makedirs(directory, exist_ok=True)
    logger.debug(f"Ensured directory exists: {directory}")


def format_error_response(error: str, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Format a standardized error response.
    
    Args:
        error: Error message
        details: Additional error details
        
    Returns:
        dict: Formatted error response
    """
    response = {
        "success": False,
        "error": error
    }
    
    if details:
        response["details"] = details
    
    return response


def get_vertex_credentials(credentials_file: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Get Vertex AI credentials from file or environment.
    
    Args:
        credentials_file: Optional path to credentials file
        
    Returns:
        dict: Credentials dictionary or None
    """
    # If specific file provided, use it
    if credentials_file:
        if os.path.exists(credentials_file):
            try:
                with open(credentials_file, "r") as file:
                    return json.load(file)
            except Exception as e:
                logger.error(f"Failed to load credentials from {credentials_file}: {str(e)}")
        else:
            logger.warning(f"Credentials file not found: {credentials_file}")
    
    # Check environment variable
    env_creds_file = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if env_creds_file and os.path.exists(env_creds_file):
        try:
            with open(env_creds_file, "r") as file:
                return json.load(file)
        except Exception as e:
            logger.error(f"Failed to load credentials from environment: {str(e)}")
    
    # Check common locations
    common_paths = [
        "vertex_ai_service_account.json",
        os.path.expanduser("~/.vertex_ai_service_account.json"),
        "/etc/vertex_ai_service_account.json"
    ]
    
    for path in common_paths:
        if os.path.exists(path):
            try:
                with open(path, "r") as file:
                    logger.info(f"Found credentials at: {path}")
                    return json.load(file)
            except Exception as e:
                logger.error(f"Failed to load credentials from {path}: {str(e)}")
    
    logger.warning("No Vertex AI credentials found")
    return None


def parse_coordinates(coords_str: str) -> List[int]:
    """
    Parse coordinate string into list of integers.
    
    Args:
        coords_str: Coordinate string like "100,200,300,400"
        
    Returns:
        list: List of integer coordinates [x, y, width, height]
        
    Raises:
        ValueError: If parsing fails
    """
    try:
        coords = [int(x.strip()) for x in coords_str.split(",")]
        if len(coords) != 4:
            raise ValueError(f"Expected 4 coordinates, got {len(coords)}")
        return coords
    except Exception as e:
        raise ValueError(f"Invalid coordinate string '{coords_str}': {str(e)}")


def safe_json_parse(json_str: str, default: Any = None) -> Any:
    """
    Safely parse JSON string with fallback.
    
    Args:
        json_str: JSON string to parse
        default: Default value if parsing fails
        
    Returns:
        Parsed JSON or default value
    """
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.warning(f"JSON parse error: {str(e)}")
        return default


if __name__ == "__main__":
    """Validate utility functions"""
    import sys
    import tempfile
    
    # List to track all validation failures
    all_validation_failures = []
    total_tests = 0
    
    # Test 1: Quality validation
    total_tests += 1
    test_qualities = [0, 50, 100, 150]
    expected_qualities = [
        IMAGE_SETTINGS["MIN_QUALITY"],
        50,
        IMAGE_SETTINGS["MAX_QUALITY"],
        IMAGE_SETTINGS["MAX_QUALITY"]
    ]
    
    for test, expected in zip(test_qualities, expected_qualities):
        result = validate_quality(test)
        if result != expected:
            all_validation_failures.append(
                f"Quality validation: Input {test} expected {expected}, got {result}"
            )
    
    # Test 2: Region validation
    total_tests += 1
    try:
        # Valid regions
        assert validate_region(None) is None
        assert validate_region("center") == "center"
        assert validate_region([100, 200, 300, 400]) == [100, 200, 300, 400]
        
        # Invalid regions should raise
        try:
            validate_region("invalid_preset")
            all_validation_failures.append("Region validation: Should reject invalid preset")
        except ValueError:
            pass  # Expected
        
        try:
            validate_region([1, 2, 3])  # Wrong length
            all_validation_failures.append("Region validation: Should reject wrong length")
        except ValueError:
            pass  # Expected
            
    except Exception as e:
        all_validation_failures.append(f"Region validation error: {str(e)}")
    
    # Test 3: Filename generation
    total_tests += 1
    filename1 = generate_filename()
    filename2 = generate_filename()
    
    if filename1 == filename2:
        all_validation_failures.append("Filename generation: Should generate unique names")
    if not filename1.startswith("screenshot_"):
        all_validation_failures.append("Filename generation: Should use correct prefix")
    if not filename1.endswith(".jpeg"):
        all_validation_failures.append("Filename generation: Should use correct extension")
    
    # Test 4: Directory creation
    total_tests += 1
    with tempfile.TemporaryDirectory() as temp_dir:
        test_dir = os.path.join(temp_dir, "test", "nested", "dir")
        ensure_directory(test_dir)
        
        if not os.path.exists(test_dir):
            all_validation_failures.append("Directory creation: Failed to create nested directory")
    
    # Test 5: Error formatting
    total_tests += 1
    error_response = format_error_response("Test error", {"code": 123})
    
    if error_response["success"] is not False:
        all_validation_failures.append("Error formatting: Should set success to False")
    if error_response["error"] != "Test error":
        all_validation_failures.append("Error formatting: Should preserve error message")
    if error_response.get("details", {}).get("code") != 123:
        all_validation_failures.append("Error formatting: Should include details")
    
    # Test 6: Coordinate parsing
    total_tests += 1
    try:
        coords = parse_coordinates("100,200,300,400")
        if coords != [100, 200, 300, 400]:
            all_validation_failures.append(f"Coordinate parsing: Expected [100,200,300,400], got {coords}")
        
        # Invalid coordinates
        try:
            parse_coordinates("100,200")
            all_validation_failures.append("Coordinate parsing: Should reject invalid count")
        except ValueError:
            pass  # Expected
            
    except Exception as e:
        all_validation_failures.append(f"Coordinate parsing error: {str(e)}")
    
    # Test 7: JSON parsing
    total_tests += 1
    valid_json = '{"key": "value"}'
    invalid_json = '{invalid}'
    
    result = safe_json_parse(valid_json, {})
    if result != {"key": "value"}:
        all_validation_failures.append("JSON parsing: Failed to parse valid JSON")
    
    result = safe_json_parse(invalid_json, {"default": True})
    if result != {"default": True}:
        all_validation_failures.append("JSON parsing: Failed to return default for invalid JSON")
    
    # Test 8: Credentials loading (mock test)
    total_tests += 1
    creds = get_vertex_credentials("nonexistent.json")
    if creds is not None:
        all_validation_failures.append("Credentials test: Should return None for nonexistent file")
    
    # Final validation result
    if all_validation_failures:
        print(f" VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f" VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("Utility functions are validated and ready for use")
        sys.exit(0)