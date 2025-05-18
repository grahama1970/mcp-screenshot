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
from mcp_screenshot.core.annotate import annotate_screenshot
from mcp_screenshot.core.compare import compare_screenshots


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
        include_raw: bool = False,
        zoom_center: Optional[List[int]] = None,
        zoom_factor: float = 1.0
    ) -> Dict[str, Any]:
        """
        Capture a screenshot of the screen or a specific region.
        
        Args:
            quality: JPEG compression quality (1-100)
            region: Screen region to capture - preset name or [x,y,width,height]
            include_raw: Whether to also save raw PNG
            zoom_center: Center point [x, y] for zoom operation
            zoom_factor: Zoom multiplication factor (e.g., 2.0 for 2x zoom)
            
        Returns:
            dict: Capture result with file path and base64 image data
        """
        logger.info(f"MCP: capture_screen called with quality={quality}, region={region}, zoom_center={zoom_center}, zoom_factor={zoom_factor}")
        
        try:
            # Convert zoom_center to tuple if provided
            zoom_center_tuple = None
            if zoom_center and len(zoom_center) >= 2:
                zoom_center_tuple = (zoom_center[0], zoom_center[1])
            
            result = capture_screenshot(
                quality=quality,
                region=region,
                include_raw=include_raw,
                zoom_center=zoom_center_tuple,
                zoom_factor=zoom_factor
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
    
    @mcp.tool()
    def annotate_image(
        image_path: str,
        annotations: List[Dict[str, Any]],
        output_path: Optional[str] = None,
        font_size: int = 16
    ) -> Dict[str, Any]:
        """
        Annotate a screenshot with visual markers and text labels.
        
        Args:
            image_path: Path to the image to annotate
            annotations: List of annotation objects with:
                - type: 'rectangle', 'circle', 'arrow', or 'text'
                - coordinates: [x1,y1,x2,y2] for rectangles, [x,y] for text, etc.
                - text: Optional text label
                - color: 'highlight', 'error', 'success', 'info' or RGBA tuple
                - thickness: Line thickness (default 3)
            output_path: Optional path to save annotated image
            font_size: Font size for text labels
            
        Returns:
            dict: Result with path to annotated image
        """
        logger.info(f"MCP: annotate_image called for: {image_path}")
        
        try:
            result = annotate_screenshot(
                image_path=image_path,
                annotations=annotations,
                output_path=output_path,
                font_size=font_size
            )
            
            return result
            
        except Exception as e:
            logger.error(f"MCP annotate_image error: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    @mcp.tool()
    def compare_images(
        image1_path: str,
        image2_path: str,
        threshold: float = 0.95,
        highlight_color: tuple = (255, 0, 0)
    ) -> Dict[str, Any]:
        """
        Compare two screenshots and detect differences.
        
        Args:
            image1_path: Path to first image
            image2_path: Path to second image
            threshold: Similarity threshold (0.0-1.0)
            highlight_color: RGB color for highlighting differences
            
        Returns:
            dict: Comparison result with similarity score and diff image
        """
        logger.info(f"MCP: compare_images called for: {image1_path} vs {image2_path}")
        
        try:
            result = compare_screenshots(
                image1_path=image1_path,
                image2_path=image2_path,
                threshold=threshold,
                highlight_color=highlight_color
            )
            
            return result
            
        except Exception as e:
            logger.error(f"MCP compare_images error: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    logger.info("Successfully registered MCP tools")