"""
MCP Layer for Screenshot Tool
Module: __init__.py
Description: Package initialization and exports

This package provides the Model Context Protocol integration,
exposing the screenshot functionality to AI agents through MCP.
"""

from mcp_screenshot.mcp.server import create_mcp_server

__all__ = ["create_mcp_server"]