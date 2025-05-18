#!/usr/bin/env python3
"""
Test script for MCP Screenshot Tool

This script tests the basic functionality of the screenshot tool.
"""

import os
import sys
import tempfile
from PIL import Image, ImageDraw

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from mcp_screenshot.core.capture import capture_screenshot, get_screen_regions
from mcp_screenshot.core.description import describe_image_content, prepare_image_for_multimodal
from mcp_screenshot.core.d3_verification import get_d3_prompt, check_expected_features
from mcp_screenshot.core.utils import validate_quality, get_vertex_credentials


def test_core_functions():
    """Test core functionality"""
    print("Testing MCP Screenshot Tool...")
    
    # List to track all validation failures
    all_validation_failures = []
    total_tests = 0
    
    # Test 1: Quality validation
    total_tests += 1
    print("\n1. Testing quality validation...")
    try:
        assert validate_quality(50) == 50
        assert validate_quality(0) == 30  # Should clamp to minimum
        assert validate_quality(150) == 90  # Should clamp to maximum
        print("   ✓ Quality validation works")
    except Exception as e:
        all_validation_failures.append(f"Quality validation: {str(e)}")
        print(f"   ✗ Error: {str(e)}")
    
    # Test 2: Screen regions
    total_tests += 1
    print("\n2. Testing screen regions...")
    try:
        regions = get_screen_regions()
        assert isinstance(regions, dict)
        assert "full" in regions
        print(f"   ✓ Found {len(regions)} screen regions")
    except Exception as e:
        all_validation_failures.append(f"Screen regions: {str(e)}")
        print(f"   ✗ Error: {str(e)}")
    
    # Test 3: D3.js prompts
    total_tests += 1
    print("\n3. Testing D3.js prompts...")
    try:
        prompt = get_d3_prompt("bar-chart")
        assert "bar" in prompt.lower()
        print("   ✓ D3.js prompts available")
    except Exception as e:
        all_validation_failures.append(f"D3.js prompts: {str(e)}")
        print(f"   ✗ Error: {str(e)}")
    
    # Test 4: Feature checking
    total_tests += 1
    print("\n4. Testing feature detection...")
    try:
        description = "This bar chart shows sales data with blue bars and x-axis labels"
        features = check_expected_features(description, ["bars", "labels", "legend"])
        assert "bars" in features["found"]
        assert "labels" in features["found"]
        assert "legend" in features["missing"]
        print("   ✓ Feature detection works")
    except Exception as e:
        all_validation_failures.append(f"Feature detection: {str(e)}")
        print(f"   ✗ Error: {str(e)}")
    
    # Test 5: Screenshot capture
    total_tests += 1
    print("\n5. Testing screenshot capture...")
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = capture_screenshot(quality=50, output_dir=temp_dir)
            assert "error" not in result
            assert os.path.exists(result["file"])
            print(f"   ✓ Screenshot saved to: {result['file']}")
    except Exception as e:
        all_validation_failures.append(f"Screenshot capture: {str(e)}")
        print(f"   ✗ Error: {str(e)}")
    
    # Test 6: Image preparation
    total_tests += 1
    print("\n6. Testing image preparation...")
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test image
            img = Image.new('RGB', (200, 100), color='white')
            draw = ImageDraw.Draw(img)
            draw.rectangle([50, 25, 150, 75], fill='blue')
            
            test_path = os.path.join(temp_dir, "test.jpg")
            img.save(test_path)
            
            # Prepare for multimodal
            img_b64 = prepare_image_for_multimodal(test_path)
            assert isinstance(img_b64, str)
            assert len(img_b64) > 0
            print("   ✓ Image preparation works")
    except Exception as e:
        all_validation_failures.append(f"Image preparation: {str(e)}")
        print(f"   ✗ Error: {str(e)}")
    
    # Test 7: Vertex AI credentials
    total_tests += 1
    print("\n7. Testing Vertex AI credentials...")
    try:
        creds = get_vertex_credentials()
        if creds:
            print("   ✓ Vertex AI credentials found")
        else:
            print("   ⚠ Vertex AI credentials not found (API calls will fail)")
    except Exception as e:
        all_validation_failures.append(f"Credentials check: {str(e)}")
        print(f"   ✗ Error: {str(e)}")
    
    # Summary
    print("\n" + "="*50)
    if all_validation_failures:
        print(f"❌ TESTS FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        return False
    else:
        print(f"✅ ALL TESTS PASSED - {total_tests} tests completed successfully")
        return True


def test_cli():
    """Test CLI functionality"""
    print("\n\nTesting CLI Commands...")
    
    # Test help
    print("\n1. Testing help command...")
    result = os.system("python -m mcp_screenshot.cli.main --help > /dev/null 2>&1")
    if result == 0:
        print("   ✓ CLI help works")
    else:
        print("   ✗ CLI help failed")
        return False
    
    # Test capture
    print("\n2. Testing capture command...")
    with tempfile.TemporaryDirectory() as temp_dir:
        output_file = os.path.join(temp_dir, "test.jpg")
        cmd = f"python -m mcp_screenshot.cli.main capture --quality 50 --output {output_file}"
        result = os.system(cmd + " > /dev/null 2>&1")
        
        if result == 0 and os.path.exists(output_file):
            print(f"   ✓ CLI capture works - saved to {output_file}")
        else:
            print("   ✗ CLI capture failed")
            return False
    
    # Test regions
    print("\n3. Testing regions command...")
    result = os.system("python -m mcp_screenshot.cli.main regions > /dev/null 2>&1")
    if result == 0:
        print("   ✓ CLI regions works")
    else:
        print("   ✗ CLI regions failed")
        return False
    
    print("\n✅ All CLI tests passed")
    return True


if __name__ == "__main__":
    print("MCP Screenshot Tool Test Suite")
    print("="*50)
    
    # Test core functions
    core_success = test_core_functions()
    
    # Test CLI
    cli_success = test_cli()
    
    # Overall result
    print("\n" + "="*50)
    if core_success and cli_success:
        print("✅ ALL TESTS PASSED - MCP Screenshot Tool is working correctly")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED - Please check the errors above")
        sys.exit(1)