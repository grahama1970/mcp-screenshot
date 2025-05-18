#!/usr/bin/env python3
"""
Main CLI Application for MCP Screenshot Tool

This module provides the main CLI interface using Typer, organizing commands
for screenshot capture, image description, and visualization verification.

This module is part of the CLI Layer and depends on the Core Layer only.
"""

import os
import json
from typing import Optional, List

import typer
from rich.console import Console
from loguru import logger

from mcp_screenshot.core.constants import IMAGE_SETTINGS, DEFAULT_MODEL
from mcp_screenshot.core.capture import capture_screenshot, capture_browser_screenshot, get_screen_regions
from mcp_screenshot.core.description import describe_image_content
from mcp_screenshot.core.d3_verification import verify_d3_visualization
from mcp_screenshot.cli.formatters import (
    print_screenshot_result,
    print_description_result,
    print_verification_result,
    print_regions_table,
    print_error,
    print_info,
    print_success,
    print_warning,
    print_json
)
from mcp_screenshot.cli.validators import (
    validate_quality_option,
    validate_region_option,
    validate_file_exists,
    validate_url,
    validate_zoom_factor
)
from mcp_screenshot.core.utils import parse_coordinates

# Initialize Typer app
app = typer.Typer(
    name="mcp-screenshot",
    help="MCP Screenshot Tool for AI-powered image analysis and verification",
    add_completion=False
)

# Console for rich output
console = Console()


class GlobalContext:
    """Global context for all commands."""
    def __init__(self):
        self.json_output = False
        self.debug = False


@app.callback()
def main(
    ctx: typer.Context,
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output results as JSON"
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        help="Enable debug logging"
    )
):
    """Initialize global context for all commands."""
    ctx.ensure_object(dict)
    ctx.obj["json_output"] = json_output
    ctx.obj["debug"] = debug
    
    if debug:
        logger.enable("mcp_screenshot")
    else:
        logger.disable("mcp_screenshot")


@app.command()
def capture(
    ctx: typer.Context,
    url: Optional[str] = typer.Option(
        None,
        "--url", "-u",
        help="URL to capture with browser",
        callback=validate_url
    ),
    quality: int = typer.Option(
        IMAGE_SETTINGS["DEFAULT_QUALITY"],
        "--quality", "-q",
        help="Image quality (30-90)",
        callback=validate_quality_option
    ),
    region: Optional[str] = typer.Option(
        None,
        "--region", "-r",
        help="Screen region to capture",
        callback=validate_region_option
    ),
    output: Optional[str] = typer.Option(
        None,
        "--output", "-o",
        help="Output filename (default: timestamped)"
    ),
    output_dir: str = typer.Option(
        "./",
        "--output-dir", "-d",
        help="Output directory"
    ),
    wait_time: int = typer.Option(
        3,
        "--wait", "-w",
        help="Seconds to wait before browser capture"
    ),
    zoom_center: Optional[str] = typer.Option(
        None,
        "--zoom-center", "-z",
        help="Center point for zoom as 'x,y' coordinates"
    ),
    zoom_factor: float = typer.Option(
        1.0,
        "--zoom-factor", "-zf",
        help="Zoom multiplication factor (e.g., 2.0 for 2x zoom)",
        callback=validate_zoom_factor
    )
):
    """
    Capture a screenshot of the screen or a specific region.
    
    Can capture entire screen, specific regions, or web pages via URL.
    Supports zooming in on a specific point with a zoom factor.
    """
    json_output = ctx.obj.get("json_output", False)
    
    try:
        # Parse zoom center if provided
        zoom_center_tuple = None
        if zoom_center:
            try:
                parts = zoom_center.split(",")
                if len(parts) != 2:
                    raise ValueError("Expected 2 coordinates")
                x = int(parts[0].strip())
                y = int(parts[1].strip())
                zoom_center_tuple = (x, y)
            except (ValueError, IndexError):
                raise typer.BadParameter("Invalid zoom center format. Use 'x,y' (e.g., '640,480')")
        
        if url:
            # Browser capture (zoom not supported for URL captures)
            if zoom_center_tuple or zoom_factor > 1.0:
                print_warning("Zoom is not supported for URL captures")
            result = capture_browser_screenshot(
                url=url,
                output_dir=output_dir,
                wait_time=wait_time,
                quality=quality
            )
        else:
            # Screen capture
            result = capture_screenshot(
                quality=quality,
                region=region,
                output_dir=output_dir,
                zoom_center=zoom_center_tuple,
                zoom_factor=zoom_factor
            )
        
        if json_output:
            print_json(result)
        else:
            print_screenshot_result(result)
            
    except Exception as e:
        error_result = {"error": str(e)}
        if json_output:
            print_json(error_result)
        else:
            print_error(f"Capture failed: {str(e)}")
        raise typer.Exit(code=1)


@app.command()
def describe(
    ctx: typer.Context,
    url: Optional[str] = typer.Option(
        None,
        "--url", "-u",
        help="URL to capture and describe"
    ),
    file: Optional[str] = typer.Option(
        None,
        "--file", "-f",
        help="Image file to describe",
        callback=validate_file_exists
    ),
    prompt: str = typer.Option(
        "Describe this image in detail",
        "--prompt", "-p",
        help="Custom prompt for image description"
    ),
    model: str = typer.Option(
        DEFAULT_MODEL,
        "--model", "-m",
        help="AI model to use"
    ),
    quality: int = typer.Option(
        IMAGE_SETTINGS["DEFAULT_QUALITY"],
        "--quality", "-q",
        help="Screenshot quality (for URL capture)",
        callback=validate_quality_option
    )
):
    """
    Describe an image using AI vision model.
    
    Can capture from URL or analyze existing file.
    """
    json_output = ctx.obj.get("json_output", False)
    
    try:
        if not url and not file:
            raise typer.BadParameter("Must provide either --url or --file")
        
        if url and file:
            raise typer.BadParameter("Cannot use both --url and --file")
        
        # Capture if URL provided
        if url:
            print_info(f"Capturing screenshot from {url}...")
            capture_result = capture_browser_screenshot(
                url=url,
                output_dir="./tmp",
                quality=quality
            )
            
            if capture_result.get("error"):
                raise Exception(capture_result["error"])
                
            image_path = capture_result["file"]
        else:
            image_path = file
        
        # Describe the image
        result = describe_image_content(
            image_path=image_path,
            prompt=prompt,
            model=model
        )
        
        result["filename"] = os.path.basename(image_path)
        
        if json_output:
            print_json(result)
        else:
            print_description_result(result, image_path)
            
    except Exception as e:
        error_result = {"error": str(e)}
        if json_output:
            print_json(error_result)
        else:
            print_error(f"Description failed: {str(e)}")
        raise typer.Exit(code=1)


@app.command()
def verify(
    ctx: typer.Context,
    target: str = typer.Argument(
        ...,
        help="URL or file path of visualization to verify"
    ),
    expert_mode: Optional[str] = typer.Option(
        None,
        "--expert", "-e",
        help="Expert mode: d3, chart, graph, data-viz, or custom prompt"
    ),
    expected_features: Optional[str] = typer.Option(
        None,
        "--features", "-f",
        help="Comma-separated list of expected features"
    ),
    custom_prompt: Optional[str] = typer.Option(
        None,
        "--prompt", "-p",
        help="Custom verification prompt (overrides expert mode)"
    ),
    model: str = typer.Option(
        DEFAULT_MODEL,
        "--model", "-m",
        help="AI model to use"
    ),
    quality: int = typer.Option(
        IMAGE_SETTINGS["DEFAULT_QUALITY"],
        "--quality", "-q",
        help="Screenshot quality",
        callback=validate_quality_option
    ),
    wait_time: int = typer.Option(
        3,
        "--wait", "-w",
        help="Seconds to wait for page load"
    )
):
    """
    Verify a visualization against expectations using AI analysis.
    
    Can be used in expert modes (d3, chart, graph) or with custom prompts.
    Captures image, analyzes with AI, and optionally checks for expected features.
    """
    json_output = ctx.obj.get("json_output", False)
    
    try:
        # Determine if target is URL or file
        is_url = target.startswith(('http://', 'https://'))
        
        # Capture or use existing image
        if is_url:
            print_info(f"Capturing screenshot from {target}...")
            capture_result = capture_browser_screenshot(
                url=target,
                output_dir="./tmp",
                quality=quality,
                wait_time=wait_time
            )
            
            if capture_result.get("error"):
                raise Exception(capture_result["error"])
                
            image_path = capture_result["file"]
        else:
            if not os.path.exists(target):
                raise typer.BadParameter(f"File not found: {target}")
            image_path = target
        
        # Determine prompt based on expert mode or custom prompt
        if custom_prompt:
            prompt = custom_prompt
        elif expert_mode:
            expert_prompts = {
                "d3": "You are a D3.js visualization expert. Analyze this visualization and describe the D3.js components, data representation, and interactive features you can identify.",
                "chart": "You are a data visualization expert. Analyze this chart and describe the chart type, data series, axes, legends, and any patterns or insights visible.",
                "graph": "You are a graph analysis expert. Analyze this graph visualization and describe the nodes, edges, layout algorithm, and any network patterns visible.",
                "data-viz": "You are a data visualization expert. Analyze this visualization and provide insights about the data representation, visual encoding, and effectiveness of the design.",
            }
            
            prompt = expert_prompts.get(expert_mode, 
                f"You are a {expert_mode} expert. Analyze this image and provide detailed insights based on your expertise.")
        else:
            prompt = "Analyze this visualization and describe its components, data representation, and any notable features."
        
        # Get AI analysis
        result = describe_image_content(
            image_path=image_path,
            prompt=prompt,
            model=model
        )
        
        # Check expected features if provided
        verification_result = {
            "description": result["description"],
            "confidence": result["confidence"],
            "model": result["model"],
            "expert_mode": expert_mode,
            "image_path": image_path
        }
        
        if expected_features:
            features_list = [f.strip() for f in expected_features.split(",")]
            
            found_features = []
            missing_features = []
            
            description_lower = result["description"].lower()
            for feature in features_list:
                if feature.lower() in description_lower:
                    found_features.append(feature)
                else:
                    missing_features.append(feature)
            
            verification_result["features"] = {
                "expected": features_list,
                "found": found_features,
                "missing": missing_features,
                "success": len(missing_features) == 0
            }
        
        if json_output:
            print_json(verification_result)
        else:
            print_verification_result(verification_result)
            
    except Exception as e:
        error_result = {"error": str(e)}
        if json_output:
            print_json(error_result)
        else:
            print_error(f"Verification failed: {str(e)}")
        raise typer.Exit(code=1)


@app.command()
def regions(
    ctx: typer.Context
):
    """Show available screen regions and their dimensions."""
    json_output = ctx.obj.get("json_output", False)
    
    try:
        regions = get_screen_regions()
        
        if json_output:
            print_json({"regions": regions})
        else:
            print_regions_table(regions)
            
    except Exception as e:
        error_result = {"error": str(e)}
        if json_output:
            print_json(error_result)
        else:
            print_error(f"Failed to get regions: {str(e)}")
        raise typer.Exit(code=1)


@app.command()
def version():
    """Show version information."""
    from mcp_screenshot import __version__
    print_info(f"mcp-screenshot version {__version__}")


@app.command()
def zoom(
    ctx: typer.Context,
    center: str = typer.Argument(
        ...,
        help="Center point for zoom as 'x,y' coordinates"
    ),
    zoom_factor: float = typer.Argument(
        2.0,
        help="Zoom multiplication factor (default: 2.0)",
        callback=validate_zoom_factor
    ),
    quality: int = typer.Option(
        IMAGE_SETTINGS["DEFAULT_QUALITY"],
        "--quality", "-q",
        help="Image quality (30-90)",
        callback=validate_quality_option
    ),
    output_dir: str = typer.Option(
        "./",
        "--output-dir", "-d",
        help="Output directory"
    ),
    region: Optional[str] = typer.Option(
        None,
        "--region", "-r",
        help="Limit zoom to a specific screen region",
        callback=validate_region_option
    )
):
    """
    Capture a zoomed screenshot centered on specific coordinates.
    
    This is a convenience command for quickly zooming in on a point of interest.
    Example: mcp-screenshot zoom 100,200 3.0
    """
    json_output = ctx.obj.get("json_output", False)
    
    try:
        # Parse center coordinates
        try:
            coords = parse_coordinates(center.strip())
            if len(coords) >= 2:
                zoom_center_tuple = (coords[0], coords[1])
            else:
                raise typer.BadParameter("Center must be 'x,y' format")
        except ValueError:
            raise typer.BadParameter("Invalid center format. Use 'x,y'")
        
        # Capture with zoom
        result = capture_screenshot(
            quality=quality,
            region=region,
            output_dir=output_dir,
            zoom_center=zoom_center_tuple,
            zoom_factor=zoom_factor
        )
        
        if json_output:
            print_json(result)
        else:
            print_screenshot_result(result)
            
    except Exception as e:
        error_result = {"error": str(e)}
        if json_output:
            print_json(error_result)
        else:
            print_error(f"Zoom capture failed: {str(e)}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()