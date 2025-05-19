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
from mcp_screenshot.core.playwright_capture import capture_browser_screenshot_playwright
from mcp_screenshot.core.chunked_capture_fixed import capture_page_chunks_async, capture_and_describe_chunks
from mcp_screenshot.core.description import describe_image_content
from mcp_screenshot.core.d3_verification import verify_d3_visualization
from mcp_screenshot.core.compare import compare_screenshots
from mcp_screenshot.core.annotate import annotate_screenshot
from mcp_screenshot.core.litellm_cache import ensure_cache_initialized
from mcp_screenshot.core.batch import batch_capture, batch_describe, BatchProcessor
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
    help="""MCP Screenshot Tool for AI-powered image analysis and verification

AGENT USAGE: Always use --json for machine-readable output

QUICK START:
  mcp-screenshot --json capture                    # Capture full screen
  mcp-screenshot --json capture --url https://...  # Capture webpage
  mcp-screenshot --json describe --file img.jpg    # Describe image
  mcp-screenshot --json compare img1.jpg img2.jpg  # Compare images
  
FOR HELP: mcp-screenshot quick-ref               # Agent cheat sheet
         mcp-screenshot schema <command>        # JSON schemas""",
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
        help="URL to capture (mutually exclusive with --region). Format: https://example.com",
        callback=validate_url
    ),
    quality: int = typer.Option(
        IMAGE_SETTINGS["DEFAULT_QUALITY"],
        "--quality", "-q",
        help="JPEG quality (30-90). Higher = better quality, larger file",
        callback=validate_quality_option
    ),
    region: Optional[str] = typer.Option(
        None,
        "--region", "-r",
        help="Screen region (mutually exclusive with --url). Options: full, left-half, right-half, top-half, bottom-half, center",
        callback=validate_region_option
    ),
    output: Optional[str] = typer.Option(
        None,
        "--output", "-o",
        help="Output filename (default: screenshot_20240120_143022.jpg format)"
    ),
    output_dir: str = typer.Option(
        "./",
        "--output-dir", "-d",
        help="Directory to save screenshot (default: current directory)"
    ),
    wait_time: int = typer.Option(
        3,
        "--wait", "-w",
        help="Seconds to wait for page load (URL captures only)"
    ),
    zoom_center: Optional[str] = typer.Option(
        None,
        "--zoom-center", "-z",
        help="Zoom center as 'x,y' (e.g., '640,480'). Must use with --zoom-factor"
    ),
    zoom_factor: float = typer.Option(
        1.0,
        "--zoom-factor", "-zf",
        help="Zoom factor: 1.0-10.0 (e.g., 2.0 = 2x zoom, 0.5 = zoom out)",
        callback=validate_zoom_factor
    ),
    full_page: bool = typer.Option(
        False,
        "--full-page", "-fp",
        help="Capture full scrollable page (URL captures only, uses Playwright)"
    ),
    chunks: bool = typer.Option(
        False,
        "--chunks",
        help="Capture page in chunks for very tall pages (URL captures only)"
    ),
    chunk_height: int = typer.Option(
        1080,
        "--chunk-height",
        help="Height of each chunk in pixels (default: viewport height)"
    ),
    max_chunks: int = typer.Option(
        20,
        "--max-chunks",
        help="Maximum number of chunks to capture"
    )
):
    """
    Capture a screenshot of the screen or a specific region.
    
    EXAMPLES:
      mcp-screenshot capture                          # Full screen
      mcp-screenshot capture --region left-half       # Left half of screen  
      mcp-screenshot capture --url https://site.com   # Web page
      mcp-screenshot capture --zoom-center 640,480 --zoom-factor 2.0  # 2x zoom
    
    REGIONS: full, left-half, right-half, top-half, bottom-half, center
    OUTPUT: Creates JPEG file with timestamp or custom name
    RETURNS: JSON with 'file' path, 'region' used, 'dimensions', 'quality'
    ERRORS: Returns 'error' field with message on failure
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
            
            # Use chunked capture for very tall pages
            if chunks:
                import asyncio
                async def capture_chunks():
                    return await capture_page_chunks_async(
                        url=url,
                        output_dir=output_dir,
                        wait_time=wait_time,
                        quality=quality,
                        chunk_height=chunk_height,
                        max_chunks=max_chunks
                    )
                result = asyncio.run(capture_chunks())
            # Use Playwright for full-page captures
            elif full_page:
                result = capture_browser_screenshot_playwright(
                    url=url,
                    output_dir=output_dir,
                    wait_time=wait_time,
                    quality=quality,
                    full_page=True
                )
            else:
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
        help="URL to capture and describe (e.g., https://example.com)"
    ),
    file: Optional[str] = typer.Option(
        None,
        "--file", "-f",
        help="Image file to describe (JPEG/PNG). Required if no --url",
        callback=validate_file_exists
    ),
    region: Optional[str] = typer.Option(
        None,
        "--region", "-r",
        help="Screen region to capture and describe. Options: full, left_half, right_half, top_half, bottom_half, center"
    ),
    prompt: str = typer.Option(
        "Describe this image in detail",
        "--prompt", "-p",
        help="Custom prompt for AI (e.g., 'List all UI elements')"
    ),
    model: str = typer.Option(
        DEFAULT_MODEL,
        "--model", "-m",
        help="AI model: vertex_ai/gemini-2.5-flash-preview-04-17|vertex_ai/gemini-2.0-flash-exp"
    ),
    quality: int = typer.Option(
        IMAGE_SETTINGS["DEFAULT_QUALITY"],
        "--quality", "-q",
        help="JPEG quality for URL captures (30-90)",
        callback=validate_quality_option
    ),
    enable_cache: bool = typer.Option(
        True,
        "--cache/--no-cache",
        help="Enable/disable response caching (saves API costs)"
    ),
    cache_ttl: int = typer.Option(
        3600,
        "--cache-ttl",
        help="Cache duration in seconds (default: 3600 = 1 hour)"
    )
):
    """
    Describe an image using AI vision model.
    
    USAGE: Requires ONE of: --url, --file, or --region
    
    EXAMPLES:
      mcp-screenshot describe --file image.jpg
      mcp-screenshot describe --url https://site.com --prompt "List all buttons"
      mcp-screenshot describe --region right_half --prompt "What's on this side?"
      mcp-screenshot describe --file chart.png --model vertex_ai/gemini-2.0-flash-exp
    
    REGIONS: full, left_half, right_half, top_half, bottom_half, center
    MODELS: vertex_ai/gemini-2.5-flash-preview-04-17 (default)
            vertex_ai/gemini-2.0-flash-exp
            
    RETURNS: JSON with 'description', 'filename', 'confidence' (1-5), 'model'
    CACHING: Results cached to reduce API costs (use --no-cache to disable)
    """
    json_output = ctx.obj.get("json_output", False)
    
    try:
        # Validate inputs
        if not url and not file and not region:
            raise typer.BadParameter("Must provide either --url, --file, or --region")
        
        # Count provided options
        provided_options = sum(bool(x) for x in [url, file, region])
        if provided_options > 1:
            raise typer.BadParameter("Cannot use multiple capture options together. Use only one of: --url, --file, or --region")
        
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
        # Capture if region provided
        elif region:
            print_info(f"Capturing {region} region of screen...")
            capture_result = capture_screenshot(
                quality=quality,
                region=region,
                output_dir="./tmp"
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
            model=model,
            enable_cache=enable_cache,
            cache_ttl=cache_ttl
        )
        
        result["filename"] = os.path.basename(image_path)
        
        if json_output:
            print_json(result)
        else:
            print_description_result(result)
            
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
        help="Expert mode: d3|chart|graph|data-viz|custom (or custom expertise string)"
    ),
    expected_features: Optional[str] = typer.Option(
        None,
        "--features", "-f",
        help="Expected features to check, comma-separated (e.g., 'axes,legend,title')"
    ),
    custom_prompt: Optional[str] = typer.Option(
        None,
        "--prompt", "-p",
        help="Custom verification prompt (overrides expert mode)"
    ),
    model: str = typer.Option(
        DEFAULT_MODEL,
        "--model", "-m",
        help="AI model: vertex_ai/gemini-2.5-flash-preview-04-17|vertex_ai/gemini-2.0-flash-exp"
    ),
    quality: int = typer.Option(
        IMAGE_SETTINGS["DEFAULT_QUALITY"],
        "--quality", "-q",
        help="JPEG quality for URL captures (30-90)",
        callback=validate_quality_option
    ),
    wait_time: int = typer.Option(
        3,
        "--wait", "-w",
        help="Seconds to wait for page load (URL captures only)"
    )
):
    """
    Verify a visualization against expectations using AI analysis.
    
    TARGET: Can be URL or file path
    
    EXAMPLES:
      mcp-screenshot verify chart.png --expert chart
      mcp-screenshot verify https://d3js.org --expert d3 --wait 5
      mcp-screenshot verify ui.png --features "header,sidebar,footer"
      mcp-screenshot verify dashboard.png --prompt "Check accessibility"
    
    EXPERTS: d3, chart, graph, data-viz, custom
    FEATURES: Comma-separated list (e.g., "axes,legend,title")
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
    """
    Show available screen regions and their dimensions.
    
    OUTPUT: Table of regions with coordinates
    JSON: Use --json for machine-readable format
    
    REGIONS: full, left-half, right-half, top-half, bottom-half, center
    """
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
def compare(
    ctx: typer.Context,
    image1: str = typer.Argument(
        ...,
        help="Path to first image file (JPEG/PNG)",
        callback=validate_file_exists
    ),
    image2: str = typer.Argument(
        ...,
        help="Path to second image file (JPEG/PNG)", 
        callback=validate_file_exists
    ),
    threshold: float = typer.Option(
        0.95,
        "--threshold", "-t",
        help="Similarity threshold: 0.0-1.0 (0.95 = 95% similar)"
    ),
    highlight_color: str = typer.Option(
        "255,0,0",
        "--highlight-color", "-c",
        help="RGB color for differences (e.g., '255,0,0' for red)"
    )
):
    """
    Compare two screenshots and detect differences.
    
    EXAMPLES:
      mcp-screenshot compare before.jpg after.jpg
      mcp-screenshot compare img1.png img2.png --threshold 0.90
      mcp-screenshot compare old.jpg new.jpg --highlight-color 0,255,0
    
    OUTPUT: Similarity score, difference image (if not identical)
    COLORS: RGB format (e.g., '255,0,0' for red)
    """
    json_output = ctx.obj.get("json_output", False)
    
    try:
        # Parse highlight color
        try:
            rgb = [int(x) for x in highlight_color.split(',')]
            if len(rgb) != 3 or any(x < 0 or x > 255 for x in rgb):
                raise ValueError
            highlight_tuple = tuple(rgb)
        except (ValueError, IndexError):
            raise typer.BadParameter("Invalid color format. Use 'R,G,B' (e.g., '255,0,0' for red)")
        
        result = compare_screenshots(image1, image2, threshold, highlight_color=highlight_tuple)
        
        if json_output:
            print_json(result)
        else:
            from rich.panel import Panel
            from rich.table import Table
            
            # Create a table for results
            table = Table(title="Screenshot Comparison Results")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            
            table.add_row("Similarity", f"{result['similarity']:.2%}")
            table.add_row("Identical", "Yes" if result['identical'] else "No")
            table.add_row("Difference", f"{result.get('diff_percentage', 0):.2f}%")
            table.add_row("Different Pixels", f"{result.get('diff_pixels', 0):,}")
            table.add_row("Total Pixels", f"{result.get('total_pixels', 0):,}")
            
            if 'diff_image' in result:
                table.add_row("Diff Image", result['diff_image'])
            
            console.print(table)
            
            if result['identical']:
                print_success("Images are identical (within threshold)")
            else:
                print_warning("Images differ")
                if 'diff_image' in result:
                    print_info(f"Difference visualization saved to: {result['diff_image']}")
                    
    except Exception as e:
        error_result = {"error": str(e)}
        if json_output:
            print_json(error_result)
        else:
            print_error(f"Comparison failed: {str(e)}")
        raise typer.Exit(code=1)


@app.command()
def annotate(
    ctx: typer.Context,
    image: str = typer.Argument(
        ...,
        help="Path to image to annotate (JPEG/PNG)",
        callback=validate_file_exists
    ),
    annotations_file: Optional[str] = typer.Option(
        None,
        "--file", "-f",
        help="JSON file with annotations array (see examples)"
    ),
    rectangle: Optional[str] = typer.Option(
        None,
        "--rect", "-r",
        help="Draw rectangle: 'x,y,width,height' (e.g., '100,100,200,150')"
    ),
    circle: Optional[str] = typer.Option(
        None,
        "--circle", "-c",
        help="Draw circle: 'center_x,center_y,radius' (e.g., '300,300,50')"
    ),
    arrow: Optional[str] = typer.Option(
        None,
        "--arrow", "-a",
        help="Draw arrow: 'start_x,start_y,end_x,end_y' (e.g., '100,100,200,200')"
    ),
    text: Optional[str] = typer.Option(
        None,
        "--text", "-t",
        help="Add text label (use with --position)"
    ),
    position: Optional[str] = typer.Option(
        None,
        "--position", "-p",
        help="Text position: 'x,y' (e.g., '150,150'). Required with --text"
    ),
    color: str = typer.Option(
        "error",
        "--color",
        help="Color name: highlight|error|success|info (yellow|red|green|blue)"
    ),
    output: Optional[str] = typer.Option(
        None,
        "--output", "-o",
        help="Output filename (default: adds _annotated suffix)"
    ),
    font_size: int = typer.Option(
        16,
        "--font-size", "-fs",
        help="Font size for text labels"
    )
):
    """
    Annotate a screenshot with shapes and text.
    
    DIRECT OPTIONS:
      mcp-screenshot annotate img.jpg --rect 10,10,100,50 --color error
      mcp-screenshot annotate img.jpg --circle 200,200,30 --color success
      mcp-screenshot annotate img.jpg --arrow 50,50,150,150 --color info
      mcp-screenshot annotate img.jpg --text "Note" --position 100,100
    
    FILE FORMAT:
      [{"type": "rectangle", "coordinates": [x,y,w,h], "color": "error"},
       {"type": "circle", "coordinates": [cx,cy,r], "color": "success"},
       {"type": "arrow", "coordinates": [x1,y1,x2,y2], "color": "info"},
       {"type": "text", "coordinates": [x,y], "text": "Label", "color": "highlight"}]
    
    COLORS: highlight (yellow), error (red), success (green), info (blue)
    """
    json_output = ctx.obj.get("json_output", False)
    
    try:
        annotations = []
        
        # Build annotations from direct options
        if rectangle:
            coords = [int(x.strip()) for x in rectangle.split(',')]
            if len(coords) != 4:
                raise typer.BadParameter("Rectangle format: 'x,y,width,height'")
            annotations.append({
                "type": "rectangle",
                "coordinates": coords,
                "color": color,
                "text": text if text and not position else None
            })
        
        if circle:
            coords = [int(x.strip()) for x in circle.split(',')]
            if len(coords) != 3:
                raise typer.BadParameter("Circle format: 'center_x,center_y,radius'")
            annotations.append({
                "type": "circle",
                "coordinates": coords,
                "color": color,
                "text": text if text and not position else None
            })
        
        if arrow:
            coords = [int(x.strip()) for x in arrow.split(',')]
            if len(coords) != 4:
                raise typer.BadParameter("Arrow format: 'start_x,start_y,end_x,end_y'")
            annotations.append({
                "type": "arrow",
                "coordinates": coords,
                "color": color,
                "text": text if text and not position else None
            })
        
        if text and position:
            coords = [int(x.strip()) for x in position.split(',')]
            if len(coords) != 2:
                raise typer.BadParameter("Text position format: 'x,y'")
            annotations.append({
                "type": "text",
                "coordinates": coords,
                "text": text,
                "color": color
            })
        elif text and not position:
            raise typer.BadParameter("--text requires --position")
        
        # Load from file if provided (overrides direct options)
        if annotations_file:
            with open(annotations_file, 'r') as f:
                annotations = json.load(f)
        
        # Validate we have some annotations
        if not annotations:
            raise typer.BadParameter("No annotations provided. Use direct options or --file")
                
        result = annotate_screenshot(
            image_path=image,
            annotations=annotations,
            output_path=output,
            font_size=font_size
        )
        
        if json_output:
            print_json(result)
        else:
            if result['success']:
                print_success(f"Annotated image saved to: {result['annotated_path']}")
                print_info(f"Applied {result['annotation_count']} annotations")
            else:
                print_error(result.get('error', 'Unknown error'))
                
    except Exception as e:
        error_result = {"error": str(e)}
        if json_output:
            print_json(error_result)
        else:
            print_error(f"Annotation failed: {str(e)}")
        raise typer.Exit(code=1)


@app.command()
def cache_info(ctx: typer.Context):
    """Show cache status and configuration."""
    json_output = ctx.obj.get("json_output", False)
    
    try:
        # Initialize cache and get status
        is_redis = ensure_cache_initialized()
        cache_type = "Redis" if is_redis else "In-memory"
        
        cache_info = {
            "cache_type": cache_type,
            "redis_available": is_redis,
            "redis_host": os.getenv("REDIS_HOST", "localhost"),
            "redis_port": os.getenv("REDIS_PORT", "6379"),
            "cache_enabled": True
        }
        
        if json_output:
            print_json(cache_info)
        else:
            print_info(f"Cache Type: {cache_type}")
            if is_redis:
                print_success(f"Redis cache enabled at {cache_info['redis_host']}:{cache_info['redis_port']}")
            else:
                print_warning("Using in-memory cache (Redis not available)")
                
    except Exception as e:
        error_result = {"error": str(e)}
        if json_output:
            print_json(error_result)
        else:
            print_error(f"Cache info failed: {str(e)}")
        raise typer.Exit(code=1)


@app.command()
def batch(
    ctx: typer.Context,
    config_file: str = typer.Argument(
        ...,
        help="JSON config file with batch operations"
    ),
    operation: str = typer.Option(
        "capture",
        "--operation", "-o",
        help="Operation type: capture, describe, or both"
    ),
    max_concurrent: int = typer.Option(
        5,
        "--max-concurrent", "-c",
        help="Maximum concurrent operations"
    ),
    output_dir: str = typer.Option(
        "./batch_output",
        "--output-dir", "-d",
        help="Output directory for results"
    )
):
    """
    Batch process multiple screenshots or descriptions.
    
    CONFIG FILE FORMAT (JSON array):
    
    CAPTURE MODE:
    [
      {"url": "https://example.com", "id": "example1", "quality": 90},
      {"region": "center", "id": "screen_center"},
      {"region": "full", "zoom_center": [640, 480], "zoom_factor": 2}
    ]
    
    DESCRIBE MODE:
    [
      {"path": "image1.jpg", "prompt": "List all UI elements", "id": "ui_analysis"},
      {"path": "image2.jpg", "prompt": "Describe the colors"},
      "image3.jpg"  // Will use default prompt
    ]
    
    BOTH MODE (capture + describe):
    [
      {"url": "https://site.com", "prompt": "Analyze the layout", "id": "site1"},
      {"region": "center", "prompt": "Describe this section"}
    ]
    
    Valid capture fields: url, region, quality, zoom_center, zoom_factor, id
    Valid describe fields: path, prompt, model, id
    
    PERFORMANCE: Progress bar shows completion. ~2-5 seconds per operation
    RETURNS: JSON with 'results' array, 'total', 'successful', 'failed' counts
    OUTPUT: Results saved to --output-dir/batch_results_{operation}.json
    """
    json_output = ctx.obj.get("json_output", False)
    
    try:
        import json
        import asyncio
        from pathlib import Path
        
        # Read config file
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        # Ensure output directory exists
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Run batch operations
        async def run_batch():
            if operation == "capture":
                return await batch_capture(config, max_concurrent=max_concurrent)
            elif operation == "describe":
                return await batch_describe(config, max_concurrent=max_concurrent)
            elif operation == "both":
                # For "both", config should have capture targets
                processor = BatchProcessor(max_concurrent=max_concurrent)
                return await processor.process_capture_and_describe(config)
            else:
                raise ValueError(f"Unknown operation: {operation}")
        
        # Run the async batch operation
        results = asyncio.run(run_batch())
        
        # Save results
        output_file = Path(output_dir) / f"batch_results_{operation}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Output results
        success_count = sum(1 for r in results if r.get("success", False))
        
        if json_output:
            print_json({
                "total": len(results),
                "successful": success_count,
                "failed": len(results) - success_count,
                "output_file": str(output_file),
                "results": results
            })
        else:
            print_success(f"Batch {operation} completed:")
            print_info(f"  Total: {len(results)}")
            print_info(f"  Successful: {success_count}")
            print_info(f"  Failed: {len(results) - success_count}")
            print_info(f"  Results saved to: {output_file}")
            
            # Show first few results
            for i, result in enumerate(results[:3]):
                if result.get("success"):
                    print_success(f"  [{i+1}] {result.get('target_id', result.get('image_id', 'Unknown'))}: Success")
                else:
                    print_error(f"  [{i+1}] {result.get('target_id', result.get('image_id', 'Unknown'))}: {result.get('error', 'Failed')}")
            
            if len(results) > 3:
                print_info(f"  ... and {len(results) - 3} more")
    
    except Exception as e:
        error_result = {"error": str(e)}
        if json_output:
            print_json(error_result)
        else:
            print_error(f"Batch operation failed: {str(e)}")
        raise typer.Exit(code=1)


@app.command()
def schema(
    ctx: typer.Context,
    command: str = typer.Argument(
        ...,
        help="Command to show schema for: batch|capture|describe|annotate|compare|verify"
    )
):
    """
    Show JSON schema for command inputs.
    
    Displays the complete JSON schema for batch config files
    or parameter specifications for other commands.
    """
    json_output = ctx.obj.get("json_output", False)
    
    schemas = {
        "batch": {
            "capture": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "URL to capture"},
                        "region": {"type": "string", "enum": ["full", "left-half", "right-half", "top-half", "bottom-half", "center"]},
                        "quality": {"type": "integer", "minimum": 30, "maximum": 90},
                        "zoom_center": {"type": "array", "items": {"type": "integer"}, "minItems": 2, "maxItems": 2},
                        "zoom_factor": {"type": "number", "minimum": 0.5, "maximum": 10.0},
                        "id": {"type": "string", "description": "Custom identifier"}
                    }
                }
            },
            "describe": {
                "type": "array",
                "items": {
                    "oneOf": [
                        {"type": "string", "description": "Image file path"},
                        {
                            "type": "object",
                            "properties": {
                                "path": {"type": "string", "description": "Image file path"},
                                "prompt": {"type": "string", "description": "AI prompt"},
                                "model": {"type": "string", "enum": ["vertex_ai/gemini-2.5-flash-preview-04-17", "vertex_ai/gemini-2.0-flash-exp"]},
                                "id": {"type": "string", "description": "Custom identifier"}
                            },
                            "required": ["path"]
                        }
                    ]
                }
            }
        },
        "capture": {
            "parameters": {
                "url": "URL to capture (optional)",
                "region": "full|left-half|right-half|top-half|bottom-half|center",
                "quality": "30-90 (JPEG quality)",
                "zoom_center": "x,y coordinates (e.g., '640,480')",
                "zoom_factor": "1.0-10.0 (zoom multiplier)",
                "output": "filename (default: timestamped)",
                "output_dir": "directory path",
                "wait": "seconds to wait for page load"
            }
        },
        "describe": {
            "parameters": {
                "url": "URL to capture and describe (either url or file required)",
                "file": "Image file path (either url or file required)",
                "prompt": "AI prompt (default: 'Describe this image in detail')",
                "model": "vertex_ai/gemini-2.5-flash-preview-04-17|vertex_ai/gemini-2.0-flash-exp",
                "quality": "30-90 (for URL captures)",
                "cache": "Enable/disable caching",
                "cache_ttl": "Cache duration in seconds"
            }
        },
        "annotate": {
            "file_format": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string", "enum": ["rectangle", "circle", "arrow", "text"]},
                        "coordinates": {"type": "array", "items": {"type": "integer"}},
                        "text": {"type": "string"},
                        "color": {"type": "string", "enum": ["highlight", "error", "success", "info"]}
                    },
                    "required": ["type", "coordinates"]
                }
            },
            "direct_options": {
                "rect": "x,y,width,height",
                "circle": "center_x,center_y,radius",
                "arrow": "start_x,start_y,end_x,end_y",
                "text": "Text content (requires --position)",
                "position": "x,y",
                "color": "highlight|error|success|info"
            }
        },
        "compare": {
            "parameters": {
                "image1": "Path to first image (required)",
                "image2": "Path to second image (required)",
                "threshold": "0.0-1.0 (default: 0.95)",
                "highlight_color": "R,G,B (e.g., '255,0,0')"
            }
        },
        "verify": {
            "parameters": {
                "target": "URL or file path (required)",
                "expert": "d3|chart|graph|data-viz|custom",
                "features": "Comma-separated expected features",
                "prompt": "Custom verification prompt",
                "model": "AI model to use",
                "quality": "30-90 (for URL captures)",
                "wait": "Seconds to wait for page load"
            }
        }
    }
    
    try:
        if command not in schemas:
            available = ", ".join(schemas.keys())
            raise typer.BadParameter(f"Unknown command. Available: {available}")
        
        schema = schemas[command]
        
        if json_output:
            print_json(schema)
        else:
            print_info(f"Schema for '{command}' command:")
            console.print_json(data=schema)
    
    except Exception as e:
        error_result = {"error": str(e)}
        if json_output:
            print_json(error_result)
        else:
            print_error(f"Schema lookup failed: {str(e)}")
        raise typer.Exit(code=1)


@app.command()
def quick_ref(ctx: typer.Context):
    """
    Show quick reference for common agent tasks.
    
    Essential commands for AI agents in one place.
    """
    json_output = ctx.obj.get("json_output", False)
    
    quick_reference = {
        "common_tasks": {
            "capture_screen": "mcp-screenshot --json capture",
            "capture_region": "mcp-screenshot --json capture --region center",
            "capture_url": "mcp-screenshot --json capture --url https://example.com",
            "describe_file": "mcp-screenshot --json describe --file image.jpg",
            "describe_region": "mcp-screenshot --json describe --region right_half",
            "describe_ui": "mcp-screenshot --json describe --file ui.jpg --prompt 'List all UI elements'",
            "compare_images": "mcp-screenshot --json compare before.jpg after.jpg",
            "batch_process": "mcp-screenshot --json batch config.json --operation both"
        },
        "key_patterns": {
            "coordinates": "Always use 'x,y' format (e.g., '640,480')",
            "colors": "Always use 'R,G,B' format (e.g., '255,0,0')",
            "regions": "full|left-half|right-half|top-half|bottom-half|center",
            "quality": "30-90 (higher = better quality)"
        },
        "json_responses": {
            "capture": {"file": "path/to/image.jpg", "region": "full", "dimensions": [1920, 1080]},
            "describe": {"description": "text", "confidence": 5, "model": "gemini"},
            "compare": {"similarity": 0.95, "identical": True, "diff_image": "path/to/diff.jpg"}
        },
        "tips": [
            "Always use --json for machine-readable output",
            "Check 'error' field in JSON responses",
            "Use schema command for detailed format info",
            "Cache is automatic for descriptions (saves API costs)"
        ]
    }
    
    if json_output:
        print_json(quick_reference)
    else:
        print_info("MCP Screenshot Quick Reference for Agents")
        print_info("=" * 40)
        
        print_success("\nCommon Tasks:")
        for task, cmd in quick_reference["common_tasks"].items():
            print_info(f"  {task}: {cmd}")
        
        print_success("\nKey Patterns:")
        for pattern, format in quick_reference["key_patterns"].items():
            print_info(f"  {pattern}: {format}")
        
        print_success("\nJSON Response Examples:")
        console.print_json(data=quick_reference["json_responses"])
        
        print_success("\nTips:")
        for tip in quick_reference["tips"]:
            print_info(f"  • {tip}")


@app.command()
def version():
    """Show version information."""
    from mcp_screenshot import __version__
    print_info(f"mcp-screenshot version {__version__}")


@app.command()
def analyze_page(
    ctx: typer.Context,
    url: str = typer.Argument(
        ...,
        help="URL to capture and analyze in chunks"
    ),
    output_dir: str = typer.Option(
        "./page_analysis",
        "--output-dir", "-d",
        help="Directory to save chunks and analysis"
    ),
    wait_time: int = typer.Option(
        5,
        "--wait", "-w",
        help="Seconds to wait for page load"
    ),
    chunk_height: int = typer.Option(
        1080,
        "--chunk-height", "-ch",
        help="Height of each chunk in pixels"
    ),
    max_chunks: int = typer.Option(
        20,
        "--max-chunks", "-mc",
        help="Maximum number of chunks to capture"
    ),
    quality: int = typer.Option(
        IMAGE_SETTINGS["DEFAULT_QUALITY"],
        "--quality", "-q",
        help="JPEG quality (30-90)",
        callback=validate_quality_option
    )
):
    """
    Analyze a tall webpage by capturing it in chunks and describing each section.
    
    This command:
    1. Captures the page in viewport-sized chunks
    2. Describes each chunk individually
    3. Provides an overall summary of the entire page
    
    EXAMPLES:
      mcp-screenshot analyze-page https://docs.site.com/long-page
      mcp-screenshot analyze-page https://api.docs.com --max-chunks 30
      mcp-screenshot --json analyze-page https://example.com/docs
    """
    json_output = ctx.obj.get("json_output", False)
    
    try:
        print_info(f"Analyzing page: {url}")
        print_info(f"Chunk height: {chunk_height}px, Max chunks: {max_chunks}")
        
        # Define async wrapper
        async def analyze():
            return await capture_and_describe_chunks(
                url=url,
                output_dir=output_dir,
                wait_time=wait_time,
                quality=quality,
                chunk_height=chunk_height,
                max_chunks=max_chunks
            )
        
        # Run the async function properly
        import asyncio
        result = asyncio.run(analyze())
        
        if result.get("success"):
            if json_output:
                print_json(result)
            else:
                # Pretty print the results
                from rich.panel import Panel
                from rich.table import Table
                
                # Summary panel
                summary_panel = Panel(
                    result["overall_summary"],
                    title=f"Page Analysis: {url}",
                    subtitle=f"{result['num_chunks']} chunks analyzed"
                )
                console.print(summary_panel)
                
                # Chunks table
                table = Table(title="Chunk Details")
                table.add_column("Chunk", style="cyan")
                table.add_column("Description", style="white")
                table.add_column("Confidence", style="green")
                
                for desc in result["chunk_descriptions"]:
                    table.add_row(
                        f"#{desc['chunk_number'] + 1}",
                        desc['description'][:100] + "..." if len(desc['description']) > 100 else desc['description'],
                        f"{desc['confidence']}/5"
                    )
                
                console.print(table)
                
                print_success(f"Analysis complete. {result['num_chunks']} chunks saved to {output_dir}")
        else:
            error_msg = result.get("error", "Unknown error")
            if json_output:
                print_json({"error": error_msg})
            else:
                print_error(f"Analysis failed: {error_msg}")
            raise typer.Exit(code=1)
            
    except Exception as e:
        error_result = {"error": str(e)}
        if json_output:
            print_json(error_result)
        else:
            print_error(f"Page analysis failed: {str(e)}")
        raise typer.Exit(code=1)


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
            parts = center.strip().split(",")
            if len(parts) != 2:
                raise ValueError("Expected 2 coordinates")
            x = int(parts[0].strip())
            y = int(parts[1].strip())
            zoom_center_tuple = (x, y)
        except (ValueError, IndexError):
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