"""
MCP Screenshot Tool for AI-Powered Image Analysis
Module: __init__.py
Description: Package initialization and exports

This package provides screenshot capture and AI-powered image analysis
with customizable expert modes for verification and insights.
"""

__version__ = "0.1.0"
__author__ = "Graham Anderson"

from .core import (
    capture_screenshot,
    describe_image_content,
    verify_d3_visualization
)

__all__ = ["capture_screenshot", "describe_image_content", "verify_d3_visualization"]