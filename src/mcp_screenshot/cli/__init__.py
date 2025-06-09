"""
CLI Layer for MCP Screenshot Tool
Module: __init__.py
Description: Package initialization and exports

This package provides the command-line interface for the screenshot tool,
including commands for capturing screenshots, analyzing images, and verifying
D3.js visualizations.
"""

from mcp_screenshot.cli.main import app

__all__ = ["app"]