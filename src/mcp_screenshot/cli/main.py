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
from mcp_screenshot.core.history import get_history
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
        
        # Save to history if successful
        if not result.get("error"):
            try:
                history = get_history()
                history.add_screenshot(
                    file_path=result["file"],
                    url=url,
                    region=region,
                    metadata={"source": "capture_command"}
                )
            except Exception as e:
                logger.warning(f"Failed to save to history: {str(e)}")
        
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
        
        # Save description to history
        if not result.get("error"):
            try:
                history = get_history()
                history.add_screenshot(
                    file_path=image_path,
                    description=result.get("description"),
                    extracted_text=result.get("description"),  # Use description as extracted text
                    url=url,
                    region=region,
                    metadata={"source": "describe_command", "prompt": prompt}
                )
            except Exception as e:
                logger.warning(f"Failed to save to history: {str(e)}")
        
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
        schemas["combined"] = {
            "parameters": {
                "text": "Text to search for (optional if --image is provided)",
                "image": "Reference image path (optional if --text is provided)",
                "text_weight": "Weight for text search (any positive number, default: 1.0)",
                "image_weight": "Weight for image similarity (any positive number, default: 1.0)",
                "limit": "Maximum results (default: 10)",
                "region": "Filter by screen region"
            },
            "notes": "At least one of --text or --image must be provided. Weights are automatically normalized."
        }
        
        schemas["similar"] = {
            "parameters": {
                "image": "Reference image path (required)",
                "threshold": "Similarity threshold 0.0-1.0 (default: 0.8)",
                "limit": "Maximum results (default: 10)",
                "region": "Filter by screen region"
            }
        }
        
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
            "view_history": "mcp-screenshot --json history",
            "search_text": "mcp-screenshot --json search 'error message'",
            "search_similar": "mcp-screenshot --json similar image.jpg",
            "search_combined": "mcp-screenshot --json combined --text 'login form' --image image.jpg --text-weight 7 --image-weight 3",
            "search_text_only": "mcp-screenshot --json combined --text 'error message'",
            "search_image_only": "mcp-screenshot --json combined --image reference.jpg",
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
            "compare": {"similarity": 0.95, "identical": True, "diff_image": "path/to/diff.jpg"},
            "search": {"query": "text", "results": [{"id": 1, "storage_path": "path", "rank": 0.85}]},
            "similar": {"query_image": "image.jpg", "results": [{"id": 1, "similarity": 0.92}]},
            "combined": {"results": [{"id": 1, "text_score": 0.8, "image_score": 0.9, "combined_score": 0.85}]}
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
        
        # Save to history if successful
        if not result.get("error"):
            try:
                history = get_history()
                history.add_screenshot(
                    file_path=result["file"],
                    url=url,
                    region=region,
                    metadata={"source": "capture_command"}
                )
            except Exception as e:
                logger.warning(f"Failed to save to history: {str(e)}")
        
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


@app.command()
def history(
    ctx: typer.Context,
    limit: int = typer.Option(
        10,
        "--limit", "-l",
        help="Number of recent screenshots to show"
    ),
    region: Optional[str] = typer.Option(
        None,
        "--region", "-r",
        help="Filter by screen region"
    )
):
    """
    Show screenshot history.
    
    Lists recent screenshots with metadata and descriptions.
    
    EXAMPLES:
      mcp-screenshot history                    # Show last 10 screenshots
      mcp-screenshot history --limit 20         # Show last 20 screenshots
      mcp-screenshot history --region left_half # Show captures of left half
    """
    json_output = ctx.obj.get("json_output", False)
    
    try:
        history = get_history()
        screenshots = history.get_recent(limit=limit, region=region)
        
        if json_output:
            print_json({
                "screenshots": [
                    {
                        "id": s["id"],
                        "filename": s["filename"],
                        "storage_path": s["storage_path"],
                        "url": s["url"],
                        "region": s["region"],
                        "timestamp": s["timestamp"].isoformat(),
                        "dimensions": f"{s['width']}x{s['height']}",
                        "size_bytes": s["size_bytes"],
                        "description": s.get("description", ""),
                        "extracted_text": s.get("extracted_text", "")[:100] + "..." if s.get("extracted_text") else ""
                    }
                    for s in screenshots
                ]
            })
        else:
            from rich.table import Table
            
            table = Table(title=f"Screenshot History (Last {limit})")
            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("Filename", style="magenta")
            table.add_column("Time", style="green")
            table.add_column("Source", style="yellow")
            table.add_column("Size", style="blue")
            table.add_column("Description", style="white")
            
            for s in screenshots:
                time_str = s["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
                source = s["url"] or s["region"] or "screen"
                size_str = f"{s['width']}x{s['height']}"
                desc = s.get("description", "")[:50] + "..." if s.get("description") else ""
                
                table.add_row(
                    str(s["id"]),
                    s["filename"],
                    time_str,
                    source,
                    size_str,
                    desc
                )
            
            console.print(table)
    
    except Exception as e:
        error_result = {"error": str(e)}
        if json_output:
            print_json(error_result)
        else:
            print_error(f"History retrieval failed: {str(e)}")
        raise typer.Exit(code=1)


@app.command()
def search(
    ctx: typer.Context,
    query: str = typer.Argument(
        ...,
        help="Search query for screenshot content"
    ),
    limit: int = typer.Option(
        10,
        "--limit", "-l",
        help="Maximum number of results"
    ),
    region: Optional[str] = typer.Option(
        None,
        "--region", "-r",
        help="Filter by screen region"
    ),
    date_from: Optional[str] = typer.Option(
        None,
        "--from",
        help="Filter from date (YYYY-MM-DD)"
    ),
    date_to: Optional[str] = typer.Option(
        None,
        "--to",
        help="Filter to date (YYYY-MM-DD)"
    )
):
    """
    Search screenshot history.
    
    Uses BM25 full-text search to find screenshots by content,
    descriptions, or extracted text.
    
    EXAMPLES:
      mcp-screenshot search "error message"
      mcp-screenshot search "login form" --limit 5
      mcp-screenshot search "dashboard" --from 2024-01-01
      mcp-screenshot search "button" --region right_half
    """
    json_output = ctx.obj.get("json_output", False)
    
    try:
        history = get_history()
        
        # Parse dates if provided
        from datetime import datetime
        date_from_dt = datetime.strptime(date_from, "%Y-%m-%d") if date_from else None
        date_to_dt = datetime.strptime(date_to, "%Y-%m-%d") if date_to else None
        
        # Perform search
        results = history.search(
            query=query,
            limit=limit,
            date_from=date_from_dt,
            date_to=date_to_dt,
            region=region
        )
        
        if json_output:
            print_json({
                "query": query,
                "results": [
                    {
                        "id": r["id"],
                        "filename": r["filename"],
                        "storage_path": r["storage_path"],
                        "url": r["url"],
                        "region": r["region"],
                        "timestamp": r["timestamp"].isoformat(),
                        "rank": r["rank"],
                        "description": r.get("description", ""),
                        "extracted_text": r.get("extracted_text", "")[:100] + "..." if r.get("extracted_text") else ""
                    }
                    for r in results
                ]
            })
        else:
            from rich.table import Table
            from rich.text import Text
            
            table = Table(title=f"Search Results for '{query}'")
            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("Filename", style="magenta")
            table.add_column("Time", style="green")
            table.add_column("Score", style="red")
            table.add_column("Match", style="yellow")
            
            for r in results:
                time_str = r["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
                score_str = f"{r['rank']:.2f}"
                
                # Show relevant text snippet
                desc = r.get("description", "")
                text = r.get("extracted_text", "")
                
                # Find the matching snippet
                match_text = ""
                if query.lower() in desc.lower():
                    match_text = desc[:100] + "..."
                elif query.lower() in text.lower():
                    match_text = text[:100] + "..."
                else:
                    match_text = (desc or text)[:100] + "..."
                
                # Highlight the query
                match_display = Text(match_text)
                for word in query.split():
                    match_display.highlight_words([word], style="bold underline")
                
                table.add_row(
                    str(r["id"]),
                    r["filename"],
                    time_str,
                    score_str,
                    match_display
                )
            
            console.print(table)
            console.print(f"\nFound {len(results)} results")
    
    except Exception as e:
        error_result = {"error": str(e)}
        if json_output:
            print_json(error_result)
        else:
            print_error(f"Search failed: {str(e)}")
        raise typer.Exit(code=1)


@app.command()
def cleanup(
    ctx: typer.Context,
    days: int = typer.Option(
        30,
        "--days", "-d",
        help="Delete screenshots older than this many days"
    ),
    force: bool = typer.Option(
        False,
        "--force", "-f",
        help="Skip confirmation prompt"
    )
):
    """
    Clean up old screenshots.
    
    Removes screenshots older than specified days from history and storage.
    
    EXAMPLES:
      mcp-screenshot cleanup                # Delete screenshots older than 30 days
      mcp-screenshot cleanup --days 7       # Delete screenshots older than 7 days
      mcp-screenshot cleanup --days 7 -f    # Skip confirmation
    """
    json_output = ctx.obj.get("json_output", False)
    
    try:
        history = get_history()
        
        # Get count of screenshots to delete
        stats = history.get_stats()
        total = stats["total_screenshots"]
        
        if not force and not json_output:
            confirm = typer.confirm(
                f"Delete screenshots older than {days} days? This may affect up to {total} screenshots."
            )
            if not confirm:
                print_info("Cleanup cancelled")
                return
        
        count = history.cleanup_old_screenshots(days=days)
        
        if json_output:
            print_json({
                "deleted": count,
                "days": days
            })
        else:
            print_success(f"Deleted {count} screenshots older than {days} days")
    
    except Exception as e:
        error_result = {"error": str(e)}
        if json_output:
            print_json(error_result)
        else:
            print_error(f"Cleanup failed: {str(e)}")
        raise typer.Exit(code=1)


@app.command()
def similar(ctx: typer.Context,
               image: str = typer.Argument(
                   ...,
                   help="Path to image to find similar screenshots",
                   callback=validate_file_exists
               ),
               threshold: float = typer.Option(
                   0.8,
                   "--threshold", "-t",
                   help="Similarity threshold (0.0-1.0, higher requires more similarity)"
               ),
               limit: int = typer.Option(
                   10,
                   "--limit", "-l",
                   help="Maximum number of results"
               ),
               region: Optional[str] = typer.Option(
                   None,
                   "--region", "-r",
                   help="Filter by screen region"
               )):
    """
    Find visually similar screenshots using perceptual hashing.
    
    Uses perceptual hashing to find images that look similar, regardless of minor
    variations in color, scaling, or cropping.
    
    EXAMPLES:
      mcp-screenshot similar image.jpg                # Find similar images
      mcp-screenshot similar image.jpg --threshold 0.9  # Higher similarity
      mcp-screenshot similar logo.png --limit 5      # Only top 5 matches
    """
    json_output = ctx.obj.get("json_output", False)
    
    try:
        history = get_history()
        results = history.find_similar_images(
            image_path=image,
            threshold=threshold,
            limit=limit,
            region=region
        )
        
        if json_output:
            print_json({
                "query_image": image,
                "threshold": threshold,
                "results": [
                    {
                        "id": r["id"],
                        "filename": r["filename"],
                        "storage_path": r["storage_path"],
                        "similarity": r["similarity"],
                        "description": r.get("description", "")
                    }
                    for r in results
                ]
            })
        else:
            from rich.table import Table
            
            table = Table(title=f"Similar Images to {os.path.basename(image)}")
            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("Filename", style="magenta")
            table.add_column("Similarity", style="green")
            table.add_column("Description", style="yellow")
            
            for r in results:
                similarity_str = f"{r['similarity']:.2%}"
                desc = r.get("description", "")[:50] + "..." if r.get("description") else ""
                
                table.add_row(
                    str(r["id"]),
                    r["filename"],
                    similarity_str,
                    desc
                )
            
            console.print(table)
            console.print(f"\nFound {len(results)} similar images")
    
    except Exception as e:
        error_result = {"error": str(e)}
        if json_output:
            print_json(error_result)
        else:
            print_error(f"Similar image search failed: {str(e)}")
        raise typer.Exit(code=1)


@app.command()
def combined(ctx: typer.Context,
                 text_query: Optional[str] = typer.Option(
                     None,
                     "--text", "-t",
                     help="Text to search for"
                 ),
                 image: Optional[str] = typer.Option(
                     None,
                     "--image", "-i",
                     help="Image to find similar screenshots",
                     callback=validate_file_exists
                 ),
                 text_weight: float = typer.Option(
                     1.0,
                     "--text-weight", "-tw",
                     help="Weight for text search (any positive number)"
                 ),
                 image_weight: float = typer.Option(
                     1.0,
                     "--image-weight", "-iw",
                     help="Weight for image similarity (any positive number)"
                 ),
                 limit: int = typer.Option(
                     10,
                     "--limit", "-l",
                     help="Maximum number of results"
                 ),
                 region: Optional[str] = typer.Option(
                     None,
                     "--region", "-r",
                     help="Filter by screen region"
                 )):
    """
    Search by text content and/or visual similarity.
    
    Performs a flexible search using BM25 text ranking and/or
    perceptual image hashing to find the most relevant screenshots.
    At least one of --text or --image must be provided.
    Weights are automatically normalized, so any positive numbers can be used.
    
    EXAMPLES:
      # Search by both text and image (equal weights)
      mcp-screenshot combined --text "login form" --image login.jpg
      
      # Text-only search
      mcp-screenshot combined --text "error message"
      
      # Image-only search
      mcp-screenshot combined --image reference.jpg
      
      # Adjust weights (70% text, 30% image)
      mcp-screenshot combined --text "error" --image error.jpg --text-weight 7 --image-weight 3
      
      # For agents (get JSON output)
      mcp-screenshot --json combined --text "button" --image button.png
    """
    json_output = ctx.obj.get("json_output", False)
    
    try:
        # Verify at least one search parameter
        if text_query is None and image is None:
            raise typer.BadParameter("At least one of --text or --image must be provided")
            
        # Verify weights for each modality
        if text_query is not None and text_weight <= 0:
            raise typer.BadParameter("Text weight must be positive when using text search")
            
        if image is not None and image_weight <= 0:
            raise typer.BadParameter("Image weight must be positive when using image search")
        
        history = get_history()
        results = history.combined_search(
            text_query=text_query,
            image_path=image,
            text_weight=text_weight,
            image_weight=image_weight,
            limit=limit,
            region=region
        )
        
        if json_output:
            print_json({
                "text_query": text_query,
                "image_query": image,
                "text_weight": text_weight,
                "image_weight": image_weight,
                "results": [
                    {
                        "id": r["id"],
                        "filename": r["filename"],
                        "storage_path": r["storage_path"],
                        "combined_score": r["combined_score"],
                        "text_score": r["text_score"],
                        "image_score": r["image_score"],
                        "description": r.get("description", "")
                    }
                    for r in results
                ]
            })
        else:
            from rich.table import Table
            
            table = Table(title=f"Combined Search Results for '{text_query}' + {os.path.basename(image)}")
            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("Filename", style="magenta")
            table.add_column("Text", style="green")
            table.add_column("Image", style="blue")
            table.add_column("Combined", style="yellow")
            table.add_column("Description", style="white")
            
            for r in results:
                text_score = f"{r['text_score']:.2f}"
                image_score = f"{r['image_score']:.2f}"
                combined_score = f"{r['combined_score']:.2f}"
                desc = r.get("description", "")[:50] + "..." if r.get("description") else ""
                
                table.add_row(
                    str(r["id"]),
                    r["filename"],
                    text_score,
                    image_score,
                    combined_score,
                    desc
                )
            
            console.print(table)
            console.print(f"\nFound {len(results)} matching screenshots")
    
    except Exception as e:
        error_result = {"error": str(e)}
        if json_output:
            print_json(error_result)
        else:
            print_error(f"Combined search failed: {str(e)}")
        raise typer.Exit(code=1)


@app.command()
def stats(ctx: typer.Context):
    """
    Show screenshot history statistics.
    
    Displays total count, storage usage, and search history.
    """
    json_output = ctx.obj.get("json_output", False)
    
    try:
        history = get_history()
        stats = history.get_stats()
        
        if json_output:
            print_json(stats)
        else:
            from rich.panel import Panel
            from rich.table import Table
            
            # Main stats
            main_stats = Table.grid(padding=1)
            main_stats.add_column()
            main_stats.add_column()
            
            main_stats.add_row("Total Screenshots:", str(stats["total_screenshots"]))
            main_stats.add_row("Total Size:", f"{stats['total_size_mb']} MB")
            
            console.print(Panel(main_stats, title="Screenshot Statistics", border_style="cyan"))
            
            # By region
            if stats["by_region"]:
                region_table = Table(title="Screenshots by Region")
                region_table.add_column("Region", style="yellow")
                region_table.add_column("Count", style="green")
                
                for region, count in stats["by_region"].items():
                    region_table.add_row(region or "full", str(count))
                
                console.print(region_table)
            
            # Recent searches
            if stats["recent_searches"]:
                search_table = Table(title="Recent Searches")
                search_table.add_column("Query", style="cyan")
                search_table.add_column("Results", style="magenta")
                search_table.add_column("Time", style="green")
                
                for search in stats["recent_searches"]:
                    search_table.add_row(
                        search["query"],
                        str(search["results"]),
                        search["timestamp"]
                    )
                
                console.print(search_table)
    
    except Exception as e:
        error_result = {"error": str(e)}
        if json_output:
            print_json(error_result)
        else:
            print_error(f"Stats retrieval failed: {str(e)}")
        raise typer.Exit(code=1)



if __name__ == "__main__":
    app()