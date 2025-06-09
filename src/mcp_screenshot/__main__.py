"""
Module: __main__.py
Description: Module for   main   functionality

External Dependencies:
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
Entry point for running the MCP Screenshot tool as a module.
This prevents import warnings when using python -m mcp_screenshot
"""

from mcp_screenshot.cli.main import app

if __name__ == "__main__":
    app()