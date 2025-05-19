#!/usr/bin/env python3
"""
Entry point for running the MCP Screenshot tool as a module.
This prevents import warnings when using python -m mcp_screenshot
"""

from mcp_screenshot.cli.main import app

if __name__ == "__main__":
    app()