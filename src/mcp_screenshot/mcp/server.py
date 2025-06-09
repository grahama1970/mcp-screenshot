"""
Module: server.py
Description: Functions for server operations

External Dependencies:
- asyncio: [Documentation URL]
- mcp: [Documentation URL]
- loguru: [Documentation URL]
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
MCP Server for Screenshot Tool

This module provides the main MCP server implementation,
exposing screenshot functionality to AI agents.

This module is part of the MCP Layer and depends on the Core Layer.
"""

import sys
import asyncio
from typing import Dict, Any, List, Optional

from mcp.server.fastmcp import FastMCP
from loguru import logger

from mcp_screenshot.core.constants import DEFAULT_MODEL, IMAGE_SETTINGS
from mcp_screenshot.mcp.tools import register_tools
from mcp_screenshot.mcp.prompts import register_prompts


def create_mcp_server(
    name: str = "MCP Screenshot Tool",
    host: str = "localhost",
    port: int = 3000
) -> FastMCP:
    """
    Create and configure the MCP server.
    
    Args:
        name: Server name
        host: Host to bind to
        port: Port to listen on
        
    Returns:
        FastMCP: Configured MCP server instance
    """
    logger.info(f"Creating MCP server: {name} on {host}:{port}")
    
    # Create server instance
    mcp = FastMCP(name, host=host, port=port)
    
    # Register all tools
    register_tools(mcp)
    
    # Register all prompts
    register_prompts(mcp)
    
    logger.info("MCP server created successfully")
    return mcp


async def main():
    """Main entry point for the MCP server."""
    import argparse
    
    parser = argparse.ArgumentParser(description="MCP Screenshot Server")
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument("--port", type=int, default=3000, help="Port to listen on")
    parser.add_argument("--name", default="MCP Screenshot Tool", help="Server name")
    
    args = parser.parse_args()
    
    # Configure logging
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    
    # Create and run server
    mcp = create_mcp_server(name=args.name, host=args.host, port=args.port)
    
    try:
        logger.info(f"Starting MCP server on {args.host}:{args.port}")
        await mcp.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {str(e)}", exc_info=True)
        sys.exit(1)



async def validate():
    """Validate server configuration"""
    result = await capabilities()
    assert "mcp-screenshot" in result.lower()
    print(" Server validation passed")


if __name__ == "__main__":
    asyncio.run(main())