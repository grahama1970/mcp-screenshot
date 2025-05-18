#!/usr/bin/env python3
"""
Input Validators for CLI

This module provides validation functions for CLI parameters,
ensuring inputs are valid before processing.

This module is part of the CLI Layer.
"""

import os
import re
from typing import Optional, Union, List
from urllib.parse import urlparse

import typer
from loguru import logger

from mcp_screenshot.core.constants import IMAGE_SETTINGS, REGION_PRESETS
from mcp_screenshot.core.utils import parse_coordinates


def validate_quality_option(ctx: typer.Context, value: int) -> int:
    """
    Validate quality parameter for CLI.
    
    Args:
        ctx: Typer context
        value: Quality value to validate
        
    Returns:
        int: Validated quality value
        
    Raises:
        typer.BadParameter: If quality is invalid
    """
    if value < 1 or value > 100:
        raise typer.BadParameter(
            f"Quality must be between 1 and 100, got {value}"
        )
    
    # Warn if outside recommended range
    if value < IMAGE_SETTINGS["MIN_QUALITY"]:
        logger.warning(
            f"Quality {value} is below recommended minimum {IMAGE_SETTINGS['MIN_QUALITY']}"
        )
    elif value > IMAGE_SETTINGS["MAX_QUALITY"]:
        logger.warning(
            f"Quality {value} is above recommended maximum {IMAGE_SETTINGS['MAX_QUALITY']}"
        )
    
    return value


def validate_region_option(ctx: typer.Context, value: Optional[str]) -> Optional[Union[str, List[int]]]:
    """
    Validate region parameter for CLI.
    
    Args:
        ctx: Typer context
        value: Region value to validate
        
    Returns:
        Validated region (preset name or coordinates)
        
    Raises:
        typer.BadParameter: If region is invalid
    """
    if value is None:
        return None
    
    # Check if it's a preset
    if value in REGION_PRESETS:
        return value
    
    # Try to parse as coordinates
    try:
        coords = parse_coordinates(value)
        
        # Validate coordinates
        for i, coord in enumerate(coords):
            if coord < 0:
                raise typer.BadParameter(
                    f"Coordinate {i+1} must be non-negative, got {coord}"
                )
        
        # Validate width and height
        if coords[2] <= 0 or coords[3] <= 0:
            raise typer.BadParameter(
                "Width and height must be positive"
            )
        
        return coords
        
    except ValueError as e:
        # Not valid coordinates, check if it might be a typo
        close_matches = []
        for preset in REGION_PRESETS:
            if value.lower() in preset.lower() or preset.lower() in value.lower():
                close_matches.append(preset)
        
        error_msg = f"Invalid region: {value}"
        if close_matches:
            error_msg += f". Did you mean one of: {', '.join(close_matches)}?"
        else:
            error_msg += f". Valid presets: {', '.join(REGION_PRESETS.keys())}"
            error_msg += " or coordinates as 'x,y,width,height'"
        
        raise typer.BadParameter(error_msg)


def validate_file_exists(ctx: typer.Context, value: Optional[str]) -> Optional[str]:
    """
    Validate that a file exists.
    
    Args:
        ctx: Typer context
        value: File path to validate
        
    Returns:
        str: Validated file path
        
    Raises:
        typer.BadParameter: If file doesn't exist
    """
    if value is None:
        return None
    
    if not os.path.exists(value):
        raise typer.BadParameter(f"File not found: {value}")
    
    if not os.path.isfile(value):
        raise typer.BadParameter(f"Not a file: {value}")
    
    return value


def validate_url(ctx: typer.Context, value: Optional[str]) -> Optional[str]:
    """
    Validate URL format.
    
    Args:
        ctx: Typer context
        value: URL to validate
        
    Returns:
        str: Validated URL
        
    Raises:
        typer.BadParameter: If URL is invalid
    """
    if value is None:
        return None
    
    # Basic URL validation
    try:
        result = urlparse(value)
        
        # Check for scheme
        if not result.scheme:
            # Try adding http:// if no scheme
            if value.startswith("localhost") or re.match(r"^\d+\.\d+\.\d+\.\d+", value):
                value = f"http://{value}"
                result = urlparse(value)
            else:
                raise typer.BadParameter(
                    f"Invalid URL: {value}. Must include scheme (http:// or https://)"
                )
        
        # Check for valid scheme
        if result.scheme not in ["http", "https", "file"]:
            raise typer.BadParameter(
                f"Invalid URL scheme: {result.scheme}. Must be http, https, or file"
            )
        
        # Check for netloc or path
        if not result.netloc and not result.path:
            raise typer.BadParameter(
                f"Invalid URL: {value}. Missing host or path"
            )
        
        return value
        
    except Exception as e:
        raise typer.BadParameter(f"Invalid URL: {value}. Error: {str(e)}")


def validate_model_option(ctx: typer.Context, value: str) -> str:
    """
    Validate AI model name.
    
    Args:
        ctx: Typer context
        value: Model name to validate
        
    Returns:
        str: Validated model name
    """
    # Basic validation - just check format
    if not value or not isinstance(value, str):
        raise typer.BadParameter("Model name must be a non-empty string")
    
    # Warn if not using expected format
    if not value.startswith("vertex_ai/"):
        logger.warning(
            f"Model '{value}' doesn't follow expected format 'vertex_ai/model-name'"
        )
    
    return value


def validate_output_dir(ctx: typer.Context, value: Optional[str]) -> Optional[str]:
    """
    Validate output directory or file path.
    
    Args:
        ctx: Typer context
        value: Output path to validate
        
    Returns:
        str: Validated output path
    """
    if value is None:
        return None
    
    # Check if it's a directory or file path
    dir_path = os.path.dirname(value) if os.path.basename(value) else value
    
    # Create directory if it doesn't exist
    if dir_path and not os.path.exists(dir_path):
        try:
            os.makedirs(dir_path, exist_ok=True)
            logger.info(f"Created output directory: {dir_path}")
        except Exception as e:
            raise typer.BadParameter(
                f"Cannot create output directory {dir_path}: {str(e)}"
            )
    
    return value


if __name__ == "__main__":
    """Test validators with sample inputs"""
    import sys
    
    # Mock context
    ctx = typer.Context(command=None)
    
    # List to track validation tests
    all_validation_failures = []
    total_tests = 0
    
    # Test 1: Quality validation
    total_tests += 1
    try:
        # Valid quality
        assert validate_quality_option(ctx, 50) == 50
        
        # Invalid quality
        try:
            validate_quality_option(ctx, 150)
            all_validation_failures.append("Quality validation: Should reject value > 100")
        except typer.BadParameter:
            pass  # Expected
            
    except Exception as e:
        all_validation_failures.append(f"Quality validation error: {str(e)}")
    
    # Test 2: Region validation
    total_tests += 1
    try:
        # Valid preset
        assert validate_region_option(ctx, "center") == "center"
        
        # Valid coordinates
        assert validate_region_option(ctx, "100,200,300,400") == [100, 200, 300, 400]
        
        # Invalid region
        try:
            validate_region_option(ctx, "invalid")
            all_validation_failures.append("Region validation: Should reject invalid region")
        except typer.BadParameter:
            pass  # Expected
            
    except Exception as e:
        all_validation_failures.append(f"Region validation error: {str(e)}")
    
    # Test 3: File validation
    total_tests += 1
    try:
        # Create temp file
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        # Valid file
        assert validate_file_exists(ctx, tmp_path) == tmp_path
        
        # Cleanup
        os.unlink(tmp_path)
        
        # Non-existent file
        try:
            validate_file_exists(ctx, "/nonexistent/file.jpg")
            all_validation_failures.append("File validation: Should reject non-existent file")
        except typer.BadParameter:
            pass  # Expected
            
    except Exception as e:
        all_validation_failures.append(f"File validation error: {str(e)}")
    
    # Test 4: URL validation
    total_tests += 1
    try:
        # Valid URLs
        assert validate_url(ctx, "http://localhost:3000") == "http://localhost:3000"
        assert validate_url(ctx, "https://example.com") == "https://example.com"
        
        # URL without scheme
        assert validate_url(ctx, "localhost:3000") == "http://localhost:3000"
        
        # Invalid URL
        try:
            validate_url(ctx, "not-a-url")
            all_validation_failures.append("URL validation: Should reject invalid URL")
        except typer.BadParameter:
            pass  # Expected
            
    except Exception as e:
        all_validation_failures.append(f"URL validation error: {str(e)}")
    
    # Test 5: Model validation
    total_tests += 1
    try:
        # Valid model
        assert validate_model_option(ctx, "vertex_ai/gemini-2.5-flash-preview-04-17")
        
        # Empty model
        try:
            validate_model_option(ctx, "")
            all_validation_failures.append("Model validation: Should reject empty model")
        except typer.BadParameter:
            pass  # Expected
            
    except Exception as e:
        all_validation_failures.append(f"Model validation error: {str(e)}")
    
    # Final validation result
    if all_validation_failures:
        print(f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("Validators are ready for use")
        sys.exit(0)