#!/usr/bin/env python3
"""
Constants for MCP Screenshot Tool

This module defines constants used throughout the screenshot functionality,
ensuring consistent configuration across the application.

This module is part of the Core Layer and should have no dependencies on
CLI or MCP layers.

Sample input:
- None (module contains only constants)

Expected output:
- None (module contains only constants)
"""

import os
from typing import Dict, Any

# Environment configuration
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "vertex_ai/gemini-2.5-flash-preview-04-17")
DEFAULT_MODEL_FALLBACK = os.getenv("DEFAULT_MODEL_FALLBACK", "vertex_ai/gemini-2.0-flash-exp")

# Image settings for capture and processing
IMAGE_SETTINGS: Dict[str, Any] = {
    "MAX_WIDTH": int(os.getenv("MAX_WIDTH", "1280")),
    "MAX_HEIGHT": int(os.getenv("MAX_HEIGHT", "1024")),
    "MIN_QUALITY": int(os.getenv("MIN_QUALITY", "30")),
    "MAX_QUALITY": int(os.getenv("MAX_QUALITY", "90")),
    "DEFAULT_QUALITY": int(os.getenv("DEFAULT_QUALITY", "70")),
    "MAX_FILE_SIZE": 500_000,  # 500kB
}

# Regional capture presets
REGION_PRESETS = {
    "full": None,
    "right_half": "right_half",
    "left_half": "left_half",
    "top_half": "top_half",
    "bottom_half": "bottom_half",
    "center": "center",
}

# Browser settings
BROWSER_SETTINGS = {
    "HEADLESS": os.getenv("HEADLESS", "true").lower() == "true",
    "TIMEOUT": int(os.getenv("BROWSER_TIMEOUT", "30000")),
    "WIDTH": 1920,
    "HEIGHT": 1080,
}

# Default prompt for image description
DEFAULT_PROMPT = "Describe this screenshot in detail."

# D3.js specific prompts
D3_PROMPTS = {
    "bar-chart": """
    Analyze this D3.js bar chart visualization. Focus on:
    1. Number of bars and their relative heights
    2. Axis labels and values
    3. Color coding if present
    4. Data patterns or trends
    5. Any legends or titles
    """,
    
    "line-chart": """
    Analyze this D3.js line chart. Identify:
    1. Number of lines and data series
    2. Axis labels and scales
    3. Trends and patterns in the data
    4. Any notable points or anomalies
    5. Legend and color coding
    """,
    
    "scatter-plot": """
    Analyze this D3.js scatter plot. Look for:
    1. Distribution of points
    2. Axis ranges and labels
    3. Correlations or clusters
    4. Outliers or patterns
    5. Any size or color variations in points
    """,
    
    "network-graph": """
    Analyze this D3.js network graph visualization. Identify:
    1. Number of nodes and edges
    2. Node labels and relationships
    3. Graph layout and clustering
    4. Any notable patterns in connections
    5. Color coding or node sizes
    """,
    
    "pie-chart": """
    Analyze this D3.js pie chart. Describe:
    1. Number of segments
    2. Relative sizes of segments
    3. Labels and percentages
    4. Color scheme used
    5. Any legends or annotations
    """,
    
    "heatmap": """
    Analyze this D3.js heatmap. Focus on:
    1. Data dimensions (rows and columns)
    2. Color scale and what it represents
    3. Patterns or clusters in the data
    4. Axis labels and categories
    5. Any notable hot or cold spots
    """,
    
    "tree": """
    Analyze this D3.js tree visualization. Identify:
    1. Number of levels in the hierarchy
    2. Branch structure and relationships
    3. Node labels and information
    4. Layout style (e.g., radial, horizontal)
    5. Any color coding or node sizes
    """,
    
    "chord-diagram": """
    Analyze this D3.js chord diagram. Describe:
    1. Number of entities around the circle
    2. Connections between entities
    3. Thickness of connections (flow volume)
    4. Color coding scheme
    5. Any patterns in relationships
    """,
    
    "sunburst": """
    Analyze this D3.js sunburst chart. Focus on:
    1. Hierarchical structure
    2. Size of segments (angular width)
    3. Depth of hierarchy levels
    4. Color coding scheme
    5. Labels and navigation
    """,
    
    "auto": """
    Analyze this D3.js visualization. First identify the chart type, then describe:
    1. The type of visualization (bar chart, line chart, network graph, etc.)
    2. Main data elements and their relationships
    3. Axes, scales, or dimensions used
    4. Color schemes and what they represent
    5. Any patterns, trends, or notable features
    """
}

# Logging settings
LOG_MAX_STR_LEN: int = 100

# Vertex AI settings
VERTEX_PROJECT = os.getenv("VERTEX_PROJECT", "")
VERTEX_LOCATION = os.getenv("VERTEX_LOCATION", "us-central1")


if __name__ == "__main__":
    """Validate module constants"""
    import sys
    
    # List to track all validation failures
    all_validation_failures = []
    total_tests = 0
    
    # Test 1: Verify IMAGE_SETTINGS contains all required keys
    total_tests += 1
    required_keys = ["MAX_WIDTH", "MAX_HEIGHT", "MIN_QUALITY", "MAX_QUALITY", 
                     "DEFAULT_QUALITY", "MAX_FILE_SIZE"]
    missing_keys = [key for key in required_keys if key not in IMAGE_SETTINGS]
    if missing_keys:
        all_validation_failures.append(f"IMAGE_SETTINGS missing keys: {missing_keys}")
    
    # Test 2: Verify all numeric constants are positive
    total_tests += 1
    for key, value in IMAGE_SETTINGS.items():
        if not isinstance(value, (int, float)) or value <= 0:
            all_validation_failures.append(f"IMAGE_SETTINGS[{key}] should be positive number, got {value}")
    
    # Test 3: Verify quality range is valid
    total_tests += 1
    if not (1 <= IMAGE_SETTINGS["MIN_QUALITY"] <= IMAGE_SETTINGS["MAX_QUALITY"] <= 100):
        all_validation_failures.append(
            f"Invalid quality range: MIN_QUALITY={IMAGE_SETTINGS['MIN_QUALITY']}, "
            f"MAX_QUALITY={IMAGE_SETTINGS['MAX_QUALITY']}"
        )
    
    # Test 4: Verify D3_PROMPTS has expected chart types
    total_tests += 1
    expected_charts = ["bar-chart", "line-chart", "scatter-plot", "network-graph", "auto"]
    missing_charts = [chart for chart in expected_charts if chart not in D3_PROMPTS]
    if missing_charts:
        all_validation_failures.append(f"D3_PROMPTS missing chart types: {missing_charts}")
    
    # Test 5: Verify browser settings
    total_tests += 1
    if not isinstance(BROWSER_SETTINGS["HEADLESS"], bool):
        all_validation_failures.append(f"BROWSER_SETTINGS['HEADLESS'] should be boolean")
    if BROWSER_SETTINGS["TIMEOUT"] <= 0:
        all_validation_failures.append(f"BROWSER_SETTINGS['TIMEOUT'] should be positive")
    
    # Test 6: Verify model configuration
    total_tests += 1
    if not DEFAULT_MODEL:
        all_validation_failures.append("DEFAULT_MODEL is not set")
    if not DEFAULT_MODEL.startswith("vertex_ai/"):
        all_validation_failures.append(f"DEFAULT_MODEL should start with 'vertex_ai/', got {DEFAULT_MODEL}")
    
    # Final validation result
    if all_validation_failures:
        print(f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("Constants are valid and ready for use")
        sys.exit(0)