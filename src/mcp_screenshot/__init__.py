"""
MCP Screenshot Tool for AI-Powered Image Analysis

This package provides screenshot capture and AI-powered image analysis
with customizable expert modes for verification and insights.
"""

__version__ = "0.1.0"
__author__ = "Graham Anderson"

from mcp_screenshot.core import (
    capture_screenshot,
    describe_image_content,
    verify_d3_visualization
)

__all__ = ["capture_screenshot", "describe_image_content", "verify_d3_visualization"]