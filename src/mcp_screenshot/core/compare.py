"""
Module: compare.py
Description: Functions for compare operations

External Dependencies:
- numpy: https://numpy.org/doc/
- PIL: [Documentation URL]
- loguru: [Documentation URL]
- tempfile: [Documentation URL]

Sample Input:
>>> # Add specific examples based on module functionality

Expected Output:
>>> # Add expected output examples

Example Usage:
>>> # Add usage examples
"""

#!/usr/bin/env python3
"""
Screenshot Comparison Module

This module provides functions for comparing screenshots to detect changes
and calculate similarity scores.

This module is part of the Core Layer.
"""

import os
from typing import Dict, Any, Tuple, Optional
import numpy as np
from PIL import Image, ImageChops, ImageDraw
from loguru import logger


def compare_screenshots(
    image1_path: str, 
    image2_path: str,
    threshold: float = 0.95,
    highlight_color: Tuple[int, int, int] = (255, 0, 0)
) -> Dict[str, Any]:
    """
    Compare two screenshots and return similarity metrics.
    
    Args:
        image1_path: Path to first image
        image2_path: Path to second image
        threshold: Similarity threshold (0.0 to 1.0)
        highlight_color: RGB color for highlighting differences
        
    Returns:
        dict: Comparison results with:
            - similarity: Float score (0.0 to 1.0)
            - identical: Boolean indicating if images are similar enough
            - diff_percentage: Percentage of pixels that differ
            - diff_image: Path to difference visualization (if not identical)
            - error: Error message if comparison fails
    """
    try:
        logger.info(f"Comparing {image1_path} with {image2_path}")
        
        # Load images
        img1 = Image.open(image1_path).convert('RGB')
        img2 = Image.open(image2_path).convert('RGB')
        
        # Ensure same size
        if img1.size != img2.size:
            logger.warning(f"Image sizes differ: {img1.size} vs {img2.size}")
            img2 = img2.resize(img1.size, Image.Resampling.LANCZOS)
        
        # Calculate pixel difference
        diff = ImageChops.difference(img1, img2)
        
        # Convert to numpy for analysis
        diff_array = np.array(diff)
        img1_array = np.array(img1)
        
        # Calculate similarity metrics
        # Count pixels that are different (any channel)
        diff_pixels = np.any(diff_array > 0, axis=2)
        diff_count = np.count_nonzero(diff_pixels)
        total_pixels = diff_array.shape[0] * diff_array.shape[1]
        
        similarity = 1 - (diff_count / total_pixels)
        diff_percentage = (diff_count / total_pixels) * 100
        
        identical = similarity >= threshold
        
        result = {
            "similarity": round(similarity, 4),
            "identical": identical,
            "diff_percentage": round(diff_percentage, 2),
            "total_pixels": total_pixels,
            "diff_pixels": diff_count
        }
        
        # Create difference visualization if not identical
        if not identical:
            diff_path = create_diff_visualization(
                img1, img2, diff, diff_pixels, 
                image1_path, highlight_color
            )
            result["diff_image"] = diff_path
            logger.info(f"Created difference visualization: {diff_path}")
        
        logger.info(f"Comparison complete: {similarity:.2%} similar")
        return result
        
    except Exception as e:
        logger.error(f"Error comparing screenshots: {str(e)}")
        return {"error": f"Comparison failed: {str(e)}"}


def create_diff_visualization(
    img1: Image.Image,
    img2: Image.Image,
    diff: Image.Image,
    diff_pixels: np.ndarray,
    base_path: str,
    highlight_color: Tuple[int, int, int]
) -> str:
    """
    Create a visualization highlighting the differences between images.
    
    Args:
        img1: First image
        img2: Second image  
        diff: Raw difference image
        diff_pixels: Boolean array of different pixels
        base_path: Base path for output file
        highlight_color: RGB color for highlighting
        
    Returns:
        str: Path to difference visualization
    """
    # Create a highlighted version
    highlight = Image.new('RGB', img1.size, (0, 0, 0))
    
    # Create mask from diff_pixels
    mask = Image.fromarray((diff_pixels * 255).astype(np.uint8))
    
    # Create highlighted overlay
    overlay = Image.new('RGB', img1.size, highlight_color)
    
    # Blend the images
    result = Image.composite(overlay, img1, mask.convert('L'))
    
    # Create side-by-side comparison
    width = img1.width * 3
    height = img1.height
    comparison = Image.new('RGB', (width, height))
    
    # Original, highlighted, and pure diff
    comparison.paste(img1, (0, 0))
    comparison.paste(result, (img1.width, 0))
    comparison.paste(diff, (img1.width * 2, 0))
    
    # Add labels
    draw = ImageDraw.Draw(comparison)
    try:
        # Use default font - will fallback to basic if not available
        draw.text((10, 10), "Original", fill=(255, 255, 255))
        draw.text((img1.width + 10, 10), "Differences", fill=(255, 255, 255))
        draw.text((img1.width * 2 + 10, 10), "Raw Diff", fill=(255, 255, 255))
    except:
        pass  # Ignore font errors
    
    # Save the comparison
    diff_path = base_path.replace('.jpg', '_diff.jpg').replace('.png', '_diff.png')
    comparison.save(diff_path, quality=90)
    
    return diff_path


def get_region_similarity(
    image1_path: str,
    image2_path: str,
    region: Tuple[int, int, int, int]
) -> Dict[str, Any]:
    """
    Compare a specific region between two screenshots.
    
    Args:
        image1_path: Path to first image
        image2_path: Path to second image
        region: Tuple of (left, top, right, bottom) coordinates
        
    Returns:
        dict: Comparison results for the region
    """
    try:
        # Load and crop images
        img1 = Image.open(image1_path).convert('RGB')
        img2 = Image.open(image2_path).convert('RGB')
        
        region_img1 = img1.crop(region)
        region_img2 = img2.crop(region)
        
        # Save temporary files for comparison
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp1:
            region_img1.save(tmp1.name)
            temp1_path = tmp1.name
            
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp2:
            region_img2.save(tmp2.name)
            temp2_path = tmp2.name
        
        # Compare the regions
        result = compare_screenshots(temp1_path, temp2_path)
        
        # Clean up temp files
        os.unlink(temp1_path)
        os.unlink(temp2_path)
        
        # Add region info to result
        result["region"] = region
        
        return result
        
    except Exception as e:
        logger.error(f"Error comparing regions: {str(e)}")
        return {"error": f"Region comparison failed: {str(e)}"}


if __name__ == "__main__":
    """Self-validation tests"""
    import sys
    
    # Test basic comparison
    print("Testing screenshot comparison module...")
    
    # Create test images
    img1 = Image.new('RGB', (100, 100), 'white')
    img2 = Image.new('RGB', (100, 100), 'white')
    
    # Add some differences
    draw2 = ImageDraw.Draw(img2)
    draw2.rectangle([40, 40, 60, 60], fill='red')
    
    # Save test images
    img1.save('test_compare_1.jpg')
    img2.save('test_compare_2.jpg')
    
    # Test comparison
    result = compare_screenshots('test_compare_1.jpg', 'test_compare_2.jpg')
    
    # Validate result
    assert 'similarity' in result
    assert 'identical' in result
    assert result['similarity'] < 1.0
    assert not result['identical']
    assert 'diff_image' in result
    
    # Clean up
    os.unlink('test_compare_1.jpg')
    os.unlink('test_compare_2.jpg')
    if 'diff_image' in result and os.path.exists(result['diff_image']):
        os.unlink(result['diff_image'])
    
    print(" All comparison tests passed!")
    sys.exit(0)