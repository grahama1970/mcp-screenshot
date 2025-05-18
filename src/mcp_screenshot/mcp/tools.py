#!/usr/bin/env python3
"""
MCP Tool Definitions

This module defines the MCP tools that expose screenshot functionality
to AI agents through the Model Context Protocol.

This module is part of the MCP Layer and depends on the Core Layer.
"""

from typing import Dict, Any, List, Optional, Union

from mcp.server.fastmcp import FastMCP
from loguru import logger

from mcp_screenshot.core.constants import DEFAULT_MODEL, IMAGE_SETTINGS, D3_PROMPTS
from mcp_screenshot.core.capture import capture_screenshot, capture_browser_screenshot, get_screen_regions
from mcp_screenshot.core.description import describe_image_content
from mcp_screenshot.core.d3_verification import verify_d3_visualization
from mcp_screenshot.core.utils import parse_coordinates


def register_tools(mcp: FastMCP) -> None:
    """
    Register all screenshot tools with the MCP server.
    
    Args:
        mcp: MCP server instance
    """
    logger.info("Registering MCP tools")
    
    @mcp.tool()
    def capture_screen(
        quality: int = IMAGE_SETTINGS["DEFAULT_QUALITY"],
        region: Optional[Union[List[int], str]] = None,
        include_raw: bool = False
    ) -> Dict[str, Any]:
        """
        Capture a screenshot of the screen or a specific region.
        
        Args:
            quality: JPEG compression quality (1-100)
            region: Screen region to capture - preset name or [x,y,width,height]
            include_raw: Whether to also save raw PNG
            
        Returns:
            dict: Capture result with file path and base64 image data
        """
        logger.info(f"MCP: capture_screen called with quality={quality}, region={region}")
        
        try:
            result = capture_screenshot(
                quality=quality,
                region=region,
                include_raw=include_raw
            )
            
            # Remove base64 data for MCP response (too large)
            if "content" in result:
                result["content_available"] = True
                del result["content"]
            
            result["success"] = "error" not in result
            return result
            
        except Exception as e:
            logger.error(f"MCP capture_screen error: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    @mcp.tool()
    def capture_webpage(
        url: str,
        quality: int = IMAGE_SETTINGS["DEFAULT_QUALITY"],
        wait_time: int = 3,
        width: int = 1920,
        height: int = 1080
    ) -> Dict[str, Any]:
        """
        Capture a screenshot of a webpage using headless browser.
        
        Args:
            url: URL to capture
            quality: JPEG compression quality (1-100)
            wait_time: Seconds to wait for page load
            width: Browser window width
            height: Browser window height
            
        Returns:
            dict: Capture result with file path and metadata
        """
        logger.info(f"MCP: capture_webpage called for URL: {url}")
        
        try:
            result = capture_browser_screenshot(
                url=url,
                quality=quality,
                wait_time=wait_time,
                width=width,
                height=height
            )
            
            # Remove base64 data for MCP response
            if "content" in result:
                result["content_available"] = True
                del result["content"]
            
            result["success"] = "error" not in result
            return result
            
        except Exception as e:
            logger.error(f"MCP capture_webpage error: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    @mcp.tool()
    def describe_image(
        image_path: str,
        prompt: str = "Describe this image in detail",
        model: str = DEFAULT_MODEL
    ) -> Dict[str, Any]:
        """
        Describe an image using AI vision model.
        
        Args:
            image_path: Path to the image file
            prompt: Custom prompt for image description
            model: AI model to use
            
        Returns:
            dict: Description result with text and confidence
        """
        logger.info(f"MCP: describe_image called for: {image_path}")
        
        try:
            result = describe_image_content(
                image_path=image_path,
                prompt=prompt,
                model=model
            )
            
            result["success"] = "error" not in result
            return result
            
        except Exception as e:
            logger.error(f"MCP describe_image error: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    @mcp.tool()
    def capture_and_describe(
        url: Optional[str] = None,
        file_path: Optional[str] = None,
        prompt: str = "Describe this image in detail",
        model: str = DEFAULT_MODEL,
        quality: int = IMAGE_SETTINGS["DEFAULT_QUALITY"]
    ) -> Dict[str, Any]:
        """
        Capture a screenshot and describe it in one operation.
        
        Args:
            url: URL to capture (if capturing from web)
            file_path: Existing image file to describe
            prompt: Custom prompt for image description
            model: AI model to use
            quality: Screenshot quality (for URL capture)
            
        Returns:
            dict: Combined capture and description result
        """
        logger.info(f"MCP: capture_and_describe called")
        
        try:
            # Capture if URL provided
            if url:
                capture_result = capture_browser_screenshot(
                    url=url,
                    quality=quality
                )
                
                if "error" in capture_result:
                    return {
                        "success": False,
                        "error": f"Capture failed: {capture_result['error']}"
                    }
                
                image_path = capture_result["file"]
            elif not file_path:
                return {
                    "success": False,
                    "error": "Either url or file_path must be provided"
                }
            else:
                image_path = file_path
            
            # Describe the image
            description_result = describe_image_content(
                image_path=image_path,
                prompt=prompt,
                model=model
            )
            
            # Combine results
            result = {
                "success": "error" not in description_result,
                "image_path": image_path,
                "description": description_result.get("description", ""),
                "confidence": description_result.get("confidence", 0),
                "model": description_result.get("model", model)
            }
            
            if url:
                result["url"] = url
            
            if "error" in description_result:
                result["error"] = description_result["error"]
                result["success"] = False
            
            return result
            
        except Exception as e:
            logger.error(f"MCP capture_and_describe error: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    @mcp.tool()
    def verify_d3(
        url: str,
        chart_type: str = "auto",
        expected_features: Optional[List[str]] = None,
        model: str = DEFAULT_MODEL,
        quality: int = IMAGE_SETTINGS["DEFAULT_QUALITY"],
        wait_time: int = 3
    ) -> Dict[str, Any]:
        """
        Verify a D3.js visualization meets expectations.
        
        Args:
            url: URL of D3.js visualization
            chart_type: Type of chart (bar-chart, line-chart, etc.)
            expected_features: List of features that should be present
            model: AI model to use
            quality: Screenshot quality
            wait_time: Seconds to wait for page load
            
        Returns:
            dict: Verification result with success status and analysis
        """
        logger.info(f"MCP: verify_d3 called for URL: {url}")
        
        try:
            result = verify_d3_visualization(
                url=url,
                chart_type=chart_type,
                expected_features=expected_features,
                model=model,
                quality=quality,
                wait_time=wait_time
            )
            
            return result
            
        except Exception as e:
            logger.error(f"MCP verify_d3 error: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    @mcp.tool()
    def list_screen_regions() -> Dict[str, Any]:
        """
        Get available screen regions and their dimensions.
        
        Returns:
            dict: Available regions with coordinates
        """
        logger.info("MCP: list_screen_regions called")
        
        try:
            regions = get_screen_regions()
            
            return {
                "success": True,
                "regions": regions
            }
            
        except Exception as e:
            logger.error(f"MCP list_screen_regions error: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    @mcp.tool()
    def get_chart_prompts() -> Dict[str, str]:
        """
        Get available D3.js chart type prompts.
        
        Returns:
            dict: Chart types and their specialized prompts
        """
        logger.info("MCP: get_chart_prompts called")
        
        return {
            "success": True,
            "prompts": D3_PROMPTS
        }
    
    logger.info("Successfully registered MCP tools")