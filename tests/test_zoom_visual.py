#!/usr/bin/env python3
"""Visual verification of zoom functionality"""

from PIL import Image, ImageDraw, ImageFont
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from mcp_screenshot.core.capture import _apply_zoom

def create_grid_image(width=800, height=600, grid_size=50):
    """Create a test image with a grid and labels"""
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    
    # Draw grid
    for x in range(0, width, grid_size):
        draw.line([(x, 0), (x, height)], fill='lightgray', width=1)
        draw.text((x+2, 2), str(x), fill='black')
    
    for y in range(0, height, grid_size):
        draw.line([(0, y), (width, y)], fill='lightgray', width=1)
        draw.text((2, y+2), str(y), fill='black')
    
    # Draw some colored markers at specific points
    markers = [
        ((200, 150), 'red', 'A'),
        ((400, 300), 'blue', 'CENTER'),
        ((600, 450), 'green', 'C'),
    ]
    
    for (x, y), color, label in markers:
        draw.ellipse([x-20, y-20, x+20, y+20], fill=color)
        draw.text((x-10, y-5), label, fill='white')
    
    return img

# Create test image
fixtures_dir = os.path.join(os.path.dirname(__file__), 'fixtures')
os.makedirs(fixtures_dir, exist_ok=True)

# Create grid image
grid_img = create_grid_image()
grid_path = os.path.join(fixtures_dir, 'test_grid.jpg')
grid_img.save(grid_path)
print(f"Created grid image: {grid_path}")

# Test zoom on the grid
zoom_tests = [
    ((400, 300), 1.0, "no_zoom"),      # No zoom
    ((400, 300), 2.0, "center_2x"),    # 2x zoom on center
    ((200, 150), 3.0, "point_a_3x"),   # 3x zoom on point A
    ((600, 450), 4.0, "point_c_4x"),   # 4x zoom on point C
]

for center, factor, name in zoom_tests:
    zoomed = _apply_zoom(grid_img, center, factor)
    zoom_path = os.path.join(fixtures_dir, f"test_grid_zoom_{name}.jpg")
    zoomed.save(zoom_path)
    print(f"Created zoom test: {zoom_path}")
    print(f"  Center: {center}, Factor: {factor}x")
    print(f"  Original size: {grid_img.size}")
    print(f"  Result size: {zoomed.size}")

print("\nZoom visual test completed!")
print("Check the files in tests/fixtures/ to see the zoom effect visually")