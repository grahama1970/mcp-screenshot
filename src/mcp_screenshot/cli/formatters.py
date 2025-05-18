#!/usr/bin/env python3
"""
Output Formatters for CLI

This module provides rich formatting functions for CLI output,
including tables, colored text, and structured data display.

This module is part of the CLI Layer.
"""

import json
from typing import Dict, Any, List

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.syntax import Syntax

# Initialize console for rich output
console = Console()


def print_screenshot_result(result: Dict[str, Any]) -> None:
    """Print formatted screenshot capture result."""
    if "error" in result:
        print_error(result["error"])
        return
    
    # Create panel with screenshot info
    content = []
    content.append(f"[green]Screenshot saved to:[/green] {result['file']}")
    
    if "dimensions" in result:
        dims = result["dimensions"]
        content.append(f"[cyan]Dimensions:[/cyan] {dims['width']}x{dims['height']}")
    
    if "quality" in result:
        content.append(f"[cyan]Quality:[/cyan] {result['quality']}")
    
    if "zoom_applied" in result and result["zoom_applied"]:
        content.append(f"[cyan]Zoom Applied:[/cyan] {result.get('zoom_factor', 'Unknown')}x at ({result.get('zoom_center', ['?','?'])[0]}, {result.get('zoom_center', ['?','?'])[1]})")
    
    if "raw_file" in result:
        content.append(f"[green]Raw PNG saved to:[/green] {result['raw_file']}")
    
    panel = Panel("\n".join(content), title="Screenshot Captured", border_style="green")
    console.print(panel)


def print_description_result(result: Dict[str, Any]) -> None:
    """Print formatted image description result."""
    if "error" in result:
        print_error(result["error"])
        return
    
    # Create panel with description
    content = []
    
    # Description
    desc = result.get("description", "No description available")
    content.append(f"[bold]Description:[/bold]\n{desc}")
    
    # Metadata
    content.append("")
    content.append(f"[cyan]Confidence:[/cyan] {result.get('confidence', 'N/A')}/5")
    content.append(f"[cyan]Model:[/cyan] {result.get('model', 'Unknown')}")
    
    if "image_path" in result:
        content.append(f"[cyan]Image:[/cyan] {result['image_path']}")
    
    if "url" in result:
        content.append(f"[cyan]URL:[/cyan] {result['url']}")
    
    title = f"Image Analysis - {result.get('filename', 'Unknown')}"
    panel = Panel("\n".join(content), title=title, border_style="blue")
    console.print(panel)


def print_verification_result(result: Dict[str, Any]) -> None:
    """Print formatted D3.js verification result."""
    if "error" in result:
        print_error(result["error"])
        return
    
    # Determine status color
    status_color = "green" if result.get("success", False) else "red"
    status_text = "PASSED" if result.get("success", False) else "FAILED"
    
    # Create content
    content = []
    content.append(f"[{status_color}]Status:[/{status_color}] [{status_color}]{status_text}[/{status_color}]")
    content.append("")
    
    # Chart type
    content.append(f"[cyan]Chart Type:[/cyan] {result.get('chart_type', 'Unknown')}")
    content.append(f"[cyan]Confidence:[/cyan] {result.get('confidence', 0)}/5")
    
    # Features
    if result.get("features_found"):
        content.append("\n[green]Features Found:[/green]")
        for feature in result["features_found"]:
            content.append(f"  ✓ {feature}")
    
    if result.get("missing_features"):
        content.append("\n[red]Missing Features:[/red]")
        for feature in result["missing_features"]:
            content.append(f"  ✗ {feature}")
    
    # Description
    if "description" in result:
        content.append(f"\n[bold]Analysis:[/bold]\n{result['description']}")
    
    # File info
    content.append("")
    if "screenshot_path" in result:
        content.append(f"[cyan]Screenshot:[/cyan] {result['screenshot_path']}")
    if "url" in result:
        content.append(f"[cyan]URL:[/cyan] {result['url']}")
    
    title = "D3.js Verification Result"
    panel = Panel("\n".join(content), title=title, border_style=status_color)
    console.print(panel)


def print_regions_table(regions: Dict[str, Dict[str, int]]) -> None:
    """Print available screen regions in a table."""
    table = Table(title="Available Screen Regions")
    
    table.add_column("Region", style="cyan", no_wrap=True)
    table.add_column("Left", justify="right")
    table.add_column("Top", justify="right")
    table.add_column("Width", justify="right")
    table.add_column("Height", justify="right")
    
    for name, region in regions.items():
        table.add_row(
            name,
            str(region.get("left", 0)),
            str(region.get("top", 0)),
            str(region.get("width", 0)),
            str(region.get("height", 0))
        )
    
    console.print(table)


def print_error(message: str) -> None:
    """Print error message in red."""
    console.print(f"[red]Error:[/red] {message}")


def print_info(message: str) -> None:
    """Print info message in blue."""
    console.print(f"[blue]Info:[/blue] {message}")


def print_success(message: str) -> None:
    """Print success message in green."""
    console.print(f"[green]Success:[/green] {message}")


def print_warning(message: str) -> None:
    """Print warning message in yellow."""
    console.print(f"[yellow]Warning:[/yellow] {message}")


def print_json(data: Dict[str, Any]) -> None:
    """Print formatted JSON output."""
    json_str = json.dumps(data, indent=2)
    syntax = Syntax(json_str, "json", theme="monokai", line_numbers=False)
    console.print(syntax)


if __name__ == "__main__":
    """Test formatters with sample data"""
    import sys
    
    # Test screenshot result
    print_info("Testing screenshot result formatter...")
    screenshot_result = {
        "file": "/path/to/screenshot.jpg",
        "dimensions": {"width": 1920, "height": 1080},
        "quality": 70
    }
    print_screenshot_result(screenshot_result)
    
    # Test description result
    print_info("\nTesting description result formatter...")
    description_result = {
        "description": "This is a bar chart showing sales data with blue bars.",
        "confidence": 4,
        "model": "vertex_ai/gemini-2.5-flash-preview-04-17",
        "filename": "chart.jpg"
    }
    print_description_result(description_result)
    
    # Test verification result
    print_info("\nTesting verification result formatter...")
    verification_result = {
        "success": True,
        "chart_type": "bar-chart",
        "confidence": 5,
        "features_found": ["bars", "axes", "labels"],
        "missing_features": ["legend"],
        "description": "A well-structured bar chart with clear data visualization.",
        "screenshot_path": "/path/to/screenshot.jpg"
    }
    print_verification_result(verification_result)
    
    # Test regions table
    print_info("\nTesting regions table formatter...")
    regions = {
        "full": {"left": 0, "top": 0, "width": 1920, "height": 1080},
        "center": {"left": 480, "top": 270, "width": 960, "height": 540}
    }
    print_regions_table(regions)
    
    # Test error and success
    print_info("\nTesting message formatters...")
    print_error("This is an error message")
    print_success("This is a success message")
    print_warning("This is a warning message")
    
    print_info("\n✅ All formatters tested successfully")
    sys.exit(0)