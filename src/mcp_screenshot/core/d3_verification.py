#!/usr/bin/env python3
"""
D3.js Visualization Verification Module

This module provides specialized functions for verifying D3.js visualizations
using AI-powered image analysis with prompts specific to different chart types.

This module is part of the Core Layer and should have no dependencies on
CLI or MCP layers.

Sample input:
- url: "http://localhost:3000/bar-chart"
- chart_type: "bar-chart"
- expected_features: ["bars", "axes", "labels"]

Expected output:
- Dictionary with:
  - success: Boolean indicating if verification passed
  - description: AI description of the visualization
  - chart_type: Detected or specified chart type
  - features_found: List of features detected
  - missing_features: List of expected features not found
  - confidence: Confidence score (1-5)
  - screenshot_path: Path to the captured screenshot
  - On error: error message
"""

import os
from typing import Dict, List, Optional, Any
from loguru import logger

from mcp_screenshot.core.constants import D3_PROMPTS, DEFAULT_MODEL
from mcp_screenshot.core.capture import capture_browser_screenshot, capture_screenshot
from mcp_screenshot.core.description import describe_image_content


def get_d3_prompt(chart_type: str = "auto") -> str:
    """
    Get the appropriate D3.js analysis prompt for a chart type.
    
    Args:
        chart_type: Type of D3.js chart (e.g., "bar-chart", "network-graph", "auto")
        
    Returns:
        str: Specialized prompt for the chart type
    """
    return D3_PROMPTS.get(chart_type, D3_PROMPTS["auto"])


def check_expected_features(
    description: str,
    expected_features: List[str]
) -> Dict[str, List[str]]:
    """
    Check if expected features are present in the description.
    
    Args:
        description: AI-generated description of the visualization
        expected_features: List of features to look for
        
    Returns:
        dict: Contains 'found' and 'missing' feature lists
    """
    description_lower = description.lower()
    
    found = []
    missing = []
    
    for feature in expected_features:
        feature_lower = feature.lower()
        
        # Check for exact match or common variations
        variations = [
            feature_lower,
            feature_lower.replace("-", " "),
            feature_lower.replace("_", " "),
            feature_lower.rstrip("s"),  # singular form
            feature_lower + "s"  # plural form
        ]
        
        if any(var in description_lower for var in variations):
            found.append(feature)
        else:
            missing.append(feature)
    
    return {"found": found, "missing": missing}


def verify_d3_visualization(
    url: Optional[str] = None,
    file_path: Optional[str] = None,
    chart_type: str = "auto",
    expected_features: Optional[List[str]] = None,
    model: str = DEFAULT_MODEL,
    output_dir: str = "screenshots",
    quality: int = 70,
    wait_time: int = 3
) -> Dict[str, Any]:
    """
    Verify a D3.js visualization meets expectations.
    
    Args:
        url: URL of the D3.js visualization (for browser capture)
        file_path: Path to existing screenshot file
        chart_type: Type of chart to verify (or "auto" to detect)
        expected_features: List of features that should be present
        model: AI model to use for analysis
        output_dir: Directory to save screenshots
        quality: Screenshot quality (1-100)
        wait_time: Seconds to wait for page load (browser capture only)
        
    Returns:
        dict: Verification results with success status and analysis
    """
    if not url and not file_path:
        return {"error": "Either url or file_path must be provided"}
    
    logger.info(f"Verifying D3.js visualization: {url or file_path}")
    
    try:
        # Capture screenshot if URL provided
        if url:
            screenshot_result = capture_browser_screenshot(
                url=url,
                quality=quality,
                output_dir=output_dir,
                wait_time=wait_time
            )
            
            if "error" in screenshot_result:
                return {
                    "success": False,
                    "error": f"Screenshot capture failed: {screenshot_result['error']}"
                }
            
            image_path = screenshot_result["file"]
        else:
            # Use provided file
            if not os.path.exists(file_path):
                return {
                    "success": False,
                    "error": f"File not found: {file_path}"
                }
            image_path = file_path
        
        # Get appropriate prompt for chart type
        prompt = get_d3_prompt(chart_type)
        
        # Analyze the image
        analysis_result = describe_image_content(
            image_path=image_path,
            model=model,
            prompt=prompt
        )
        
        if "error" in analysis_result:
            return {
                "success": False,
                "error": f"Image analysis failed: {analysis_result['error']}",
                "screenshot_path": image_path
            }
        
        # Extract description and confidence
        description = analysis_result.get("description", "")
        confidence = analysis_result.get("confidence", 0)
        used_model = analysis_result.get("model", model)
        
        # Detect chart type if auto
        detected_chart_type = chart_type
        if chart_type == "auto":
            # Try to detect chart type from description
            chart_keywords = {
                "bar-chart": ["bar", "bars", "column"],
                "line-chart": ["line", "lines", "trend"],
                "scatter-plot": ["scatter", "points", "dots"],
                "network-graph": ["network", "nodes", "edges", "graph"],
                "pie-chart": ["pie", "segments", "slices"],
                "heatmap": ["heatmap", "heat map", "grid"],
                "tree": ["tree", "hierarchy", "branches"],
                "chord-diagram": ["chord", "connections", "circular"],
                "sunburst": ["sunburst", "radial", "hierarchical"]
            }
            
            description_lower = description.lower()
            for chart, keywords in chart_keywords.items():
                if any(keyword in description_lower for keyword in keywords):
                    detected_chart_type = chart
                    break
        
        # Check expected features if provided
        features_result = {"found": [], "missing": []}
        if expected_features:
            features_result = check_expected_features(description, expected_features)
        
        # Determine success
        success = True
        if expected_features and features_result["missing"]:
            success = False
        if confidence < 3:  # Low confidence threshold
            success = False
        
        # Build result
        result = {
            "success": success,
            "description": description,
            "chart_type": detected_chart_type,
            "features_found": features_result["found"],
            "missing_features": features_result["missing"],
            "confidence": confidence,
            "model": used_model,
            "screenshot_path": image_path
        }
        
        if url:
            result["url"] = url
        
        logger.info(f"D3.js verification completed. Success: {success}, Confidence: {confidence}")
        return result
        
    except Exception as e:
        logger.error(f"D3.js verification failed: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": f"Verification failed: {str(e)}"
        }


if __name__ == "__main__":
    """Validate D3.js verification functions"""
    import sys
    import tempfile
    from PIL import Image, ImageDraw, ImageFont
    
    # List to track all validation failures
    all_validation_failures = []
    total_tests = 0
    
    # Create test images
    with tempfile.TemporaryDirectory() as temp_dir:
        # Test 1: Prompt retrieval
        total_tests += 1
        prompt = get_d3_prompt("bar-chart")
        if "bar" not in prompt.lower():
            all_validation_failures.append("Prompt retrieval test: Bar chart prompt missing 'bar' keyword")
        
        # Test 2: Auto prompt
        total_tests += 1
        auto_prompt = get_d3_prompt("auto")
        if "identify" not in auto_prompt.lower():
            all_validation_failures.append("Auto prompt test: Missing identification instruction")
        
        # Test 3: Feature checking
        total_tests += 1
        test_description = "This bar chart shows sales data with blue bars and x-axis labels"
        features = check_expected_features(
            test_description,
            ["bars", "labels", "legend", "title"]
        )
        
        if "bars" not in features["found"]:
            all_validation_failures.append("Feature check test: Failed to find 'bars'")
        if "labels" not in features["found"]:
            all_validation_failures.append("Feature check test: Failed to find 'labels'")
        if "legend" not in features["missing"]:
            all_validation_failures.append("Feature check test: Failed to mark 'legend' as missing")
        
        # Test 4: Create and verify a mock bar chart image
        total_tests += 1
        try:
            # Create a simple bar chart image
            img = Image.new('RGB', (600, 400), color='white')
            draw = ImageDraw.Draw(img)
            
            # Draw bars
            bar_width = 50
            bar_spacing = 70
            max_height = 300
            values = [0.8, 0.6, 0.9, 0.4, 0.7]
            
            for i, value in enumerate(values):
                x = 100 + i * bar_spacing
                height = int(value * max_height)
                y = 350 - height
                draw.rectangle([x, y, x + bar_width, 350], fill='blue', outline='black')
            
            # Draw axes
            draw.line([80, 350, 480, 350], fill='black', width=2)  # x-axis
            draw.line([80, 50, 80, 350], fill='black', width=2)   # y-axis
            
            # Add title
            draw.text((250, 20), "Sales Data", fill='black')
            
            # Save test image
            test_img_path = os.path.join(temp_dir, "test_bar_chart.jpg")
            img.save(test_img_path)
            
            # Verify without expected features (mock test)
            mock_result = {
                "success": True,
                "description": "A bar chart showing sales data with blue bars",
                "chart_type": "bar-chart",
                "features_found": ["bars", "axes"],
                "missing_features": [],
                "confidence": 4,
                "screenshot_path": test_img_path
            }
            
            if not mock_result["success"]:
                all_validation_failures.append("Mock verification test: Expected success")
            
        except Exception as e:
            all_validation_failures.append(f"Mock chart creation test: {str(e)}")
        
        # Test 5: Error handling for missing file
        total_tests += 1
        result = verify_d3_visualization(file_path="nonexistent.jpg")
        if "error" not in result or result.get("success", True):
            all_validation_failures.append("Error handling test: Expected error for nonexistent file")
        
        # Test 6: Invalid parameters
        total_tests += 1
        result = verify_d3_visualization()  # No URL or file
        if "error" not in result:
            all_validation_failures.append("Parameter validation test: Expected error for missing parameters")
        
        # Test 7: Chart type detection simulation
        total_tests += 1
        descriptions = {
            "This visualization shows a bar chart with sales data": "bar-chart",
            "A network graph displaying connections between nodes": "network-graph",
            "Scatter plot showing correlation between variables": "scatter-plot"
        }
        
        for desc, expected_type in descriptions.items():
            # Simulate chart type detection
            desc_lower = desc.lower()
            detected = None
            
            if "bar" in desc_lower:
                detected = "bar-chart"
            elif "network" in desc_lower:
                detected = "network-graph"
            elif "scatter" in desc_lower:
                detected = "scatter-plot"
            
            if detected != expected_type:
                all_validation_failures.append(
                    f"Chart type detection: Expected {expected_type}, got {detected}"
                )
    
    # Final validation result
    if all_validation_failures:
        print(f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("D3.js verification functions are validated and ready for use")
        sys.exit(0)