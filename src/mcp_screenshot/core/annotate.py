"""Screenshot annotation functionality"""
Module: annotate.py
Description: Functions for annotate operations

from typing import Dict, Any, List, Tuple, Optional
from PIL import Image, ImageDraw, ImageFont
import os
from pathlib import Path

# Default colors for annotations
DEFAULT_COLORS = {
    'highlight': (255, 255, 0, 128),  # Yellow with transparency
    'error': (255, 0, 0, 128),        # Red with transparency
    'success': (0, 255, 0, 128),      # Green with transparency
    'info': (0, 0, 255, 128),         # Blue with transparency
}

# Font settings
DEFAULT_FONT_SIZE = 16
FONT_CACHE = {}


def get_font(size: int = DEFAULT_FONT_SIZE) -> Optional[ImageFont.FreeTypeFont]:
    """Get a font instance with caching"""
    if size in FONT_CACHE:
        return FONT_CACHE[size]
    
    try:
        # Try to load a default system font
        fonts_to_try = [
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "C:\\Windows\\Fonts\\Arial.ttf"
        ]
        
        for font_path in fonts_to_try:
            if os.path.exists(font_path):
                font = ImageFont.truetype(font_path, size)
                FONT_CACHE[size] = font
                return font
                
        # Fall back to default font
        font = ImageFont.load_default()
        FONT_CACHE[size] = font
        return font
    except Exception:
        return None


def annotate_screenshot(
    image_path: str,
    annotations: List[Dict[str, Any]],
    output_path: Optional[str] = None,
    font_size: int = DEFAULT_FONT_SIZE
) -> Dict[str, Any]:
    """
    Annotate a screenshot with rectangles, arrows, and text labels
    
    Args:
        image_path: Path to the screenshot image
        annotations: List of annotation dictionaries with:
            - type: 'rectangle', 'arrow', 'text', 'circle'
            - coordinates: [x1, y1, x2, y2] for rectangles, [x, y] for text
            - text: Optional text label
            - color: Optional color name or RGBA tuple
            - thickness: Optional line thickness
        output_path: Optional path to save annotated image (defaults to _annotated suffix)
        font_size: Font size for text labels
        
    Returns:
        dict: Result with path to annotated image
    """
    try:
        # Load the image
        image = Image.open(image_path)
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        # Create overlay for semi-transparent annotations
        overlay = Image.new('RGBA', image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        font = get_font(font_size)
        
        # Process each annotation
        for annotation in annotations:
            ann_type = annotation.get('type', 'rectangle')
            coords = annotation.get('coordinates', [])
            text = annotation.get('text', '')
            color = annotation.get('color', 'highlight')
            thickness = annotation.get('thickness', 3)
            
            # Get color value
            if isinstance(color, str) and color in DEFAULT_COLORS:
                color = DEFAULT_COLORS[color]
            elif isinstance(color, str):
                color = DEFAULT_COLORS['highlight']  # Default color
            
            # Draw based on type
            if ann_type == 'rectangle' and len(coords) >= 4:
                x1, y1, x2, y2 = coords[:4]
                draw.rectangle([x1, y1, x2, y2], outline=color, width=thickness)
                
                # Add text label if provided
                if text and font:
                    text_x = x1
                    text_y = y1 - font_size - 5
                    if text_y < 0:
                        text_y = y2 + 5
                    draw.text((text_x, text_y), text, fill=color[:3] + (255,), font=font)
            
            elif ann_type == 'circle' and len(coords) >= 3:
                x, y, radius = coords[:3]
                draw.ellipse([x-radius, y-radius, x+radius, y+radius], 
                           outline=color, width=thickness)
                
                # Add text label if provided
                if text and font:
                    draw.text((x + radius + 5, y), text, fill=color[:3] + (255,), font=font)
            
            elif ann_type == 'arrow' and len(coords) >= 4:
                x1, y1, x2, y2 = coords[:4]
                # Draw line
                draw.line([x1, y1, x2, y2], fill=color, width=thickness)
                
                # Draw arrowhead
                import math
                angle = math.atan2(y2 - y1, x2 - x1)
                arrow_length = 15
                arrow_angle = math.radians(30)
                
                # Left side of arrow
                x3 = x2 - arrow_length * math.cos(angle - arrow_angle)
                y3 = y2 - arrow_length * math.sin(angle - arrow_angle)
                draw.line([x2, y2, x3, y3], fill=color, width=thickness)
                
                # Right side of arrow
                x4 = x2 - arrow_length * math.cos(angle + arrow_angle)
                y4 = y2 - arrow_length * math.sin(angle + arrow_angle)
                draw.line([x2, y2, x4, y4], fill=color, width=thickness)
                
                # Add text label if provided
                if text and font:
                    mid_x = (x1 + x2) // 2
                    mid_y = (y1 + y2) // 2
                    draw.text((mid_x + 5, mid_y), text, fill=color[:3] + (255,), font=font)
            
            elif ann_type == 'text' and len(coords) >= 2 and text:
                x, y = coords[:2]
                if font:
                    draw.text((x, y), text, fill=color[:3] + (255,), font=font)
        
        # Composite the overlay onto the original image
        annotated = Image.alpha_composite(image, overlay)
        
        # Save the annotated image
        if not output_path:
            path = Path(image_path)
            output_path = str(path.with_name(f"{path.stem}_annotated{path.suffix}"))
        
        annotated.save(output_path, 'PNG')
        
        return {
            "success": True,
            "message": "Screenshot annotated successfully",
            "annotated_path": output_path,
            "annotation_count": len(annotations)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to annotate screenshot: {str(e)}"
        }


if __name__ == "__main__":
    """Self-validation tests"""
    print("Testing annotation functionality...")
    
    # Test color parsing
    assert DEFAULT_COLORS['highlight'] == (255, 255, 0, 128)
    assert DEFAULT_COLORS['error'] == (255, 0, 0, 128)
    
    # Test font loading
    font = get_font(16)
    assert font is not None
    
    print("All tests passed!")