#!/usr/bin/env python3
"""Test zoom functionality with a dummy image"""

from PIL import Image, ImageDraw
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from mcp_screenshot.core.capture import _apply_zoom

# Create a test image
img = Image.new('RGB', (800, 600), 'white')
draw = ImageDraw.Draw(img)

# Draw some shapes to make zoom visible
draw.rectangle([100, 100, 200, 200], fill='red')
draw.rectangle([300, 200, 500, 400], fill='blue')
draw.rectangle([600, 300, 700, 500], fill='green')
draw.ellipse([350, 350, 450, 450], fill='yellow')

# Save original
img.save('test_original.jpg')
print("Saved original image: test_original.jpg")

# Test zoom at different points
zoom_tests = [
    ((400, 300), 2.0, "center_2x"),
    ((150, 150), 3.0, "red_square_3x"),
    ((650, 400), 4.0, "green_rect_4x"),
]

for center, factor, name in zoom_tests:
    zoomed = _apply_zoom(img, center, factor)
    filename = f"test_zoom_{name}.jpg"
    zoomed.save(filename)
    print(f"Saved zoomed image: {filename} (center={center}, factor={factor})")
    print(f"  Original size: {img.size}")
    print(f"  Zoomed size: {zoomed.size}")

print("\nZoom test completed successfully!")