"""
Core Layer for MCP Screenshot Tool

This package contains the core business logic for screenshot functionality.
It provides pure functions for screenshot capture, image processing, and description.

The core layer is designed to be:
1. Independent of UI or integration concerns
2. Fully testable in isolation
3. Focused on business logic only
4. Self-validating through unit tests

Usage:
    from mcp_screenshot.core import capture_screenshot, describe_image_content
    result = capture_screenshot(quality=70, region="full")
    description = describe_image_content(image_path=result["file"])
"""

# Core constants and settings
from mcp_screenshot.core.constants import (
    IMAGE_SETTINGS, 
    REGION_PRESETS,
    DEFAULT_MODEL,
    DEFAULT_PROMPT,
    D3_PROMPTS
)

# Screenshot capture
from mcp_screenshot.core.capture import (
    capture_screenshot, 
    capture_browser_screenshot,
    get_screen_regions
)

# Image description
from mcp_screenshot.core.description import (
    describe_image_content,
    generate_image_embedding,
    prepare_image_for_multimodal
)

# D3.js verification
from mcp_screenshot.core.d3_verification import (
    verify_d3_visualization,
    get_d3_prompt,
    check_expected_features
)

# Utility functions
from mcp_screenshot.core.utils import (
    validate_quality,
    validate_region,
    generate_filename,
    ensure_directory,
    format_error_response,
    get_vertex_credentials
)

__all__ = [
    # Constants
    'IMAGE_SETTINGS',
    'REGION_PRESETS',
    'DEFAULT_MODEL',
    'DEFAULT_PROMPT',
    'D3_PROMPTS',
    
    # Capture functions
    'capture_screenshot',
    'capture_browser_screenshot',
    'get_screen_regions',
    
    # Description functions
    'describe_image_content',
    'generate_image_embedding',
    'prepare_image_for_multimodal',
    
    # D3.js verification
    'verify_d3_visualization',
    'get_d3_prompt',
    'check_expected_features',
    
    # Utilities
    'validate_quality',
    'validate_region',
    'generate_filename',
    'ensure_directory',
    'format_error_response',
    'get_vertex_credentials'
]