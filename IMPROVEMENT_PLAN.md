# MCP Screenshot Tool Improvement Plan

Based on 2024 best practices for screenshot tools and MCP development, here are improvements that will significantly enhance the project without adding confusing complexity:

## 1. Add Caching for AI Responses

**Why**: Reduce API costs and improve response times for repeated image analysis
**Implementation**: Simple in-memory or file-based cache with TTL

```python
# In core/description.py
from functools import lru_cache
import hashlib
import json
import time

class ImageDescriptionCache:
    def __init__(self, ttl_seconds=3600):
        self.cache = {}
        self.ttl = ttl_seconds
    
    def get_cache_key(self, image_path: str, prompt: str) -> str:
        """Generate cache key from image content and prompt"""
        with open(image_path, 'rb') as f:
            image_hash = hashlib.md5(f.read()).hexdigest()
        return f"{image_hash}_{hashlib.md5(prompt.encode()).hexdigest()}"
    
    def get(self, key: str) -> Optional[Dict]:
        """Get cached result if not expired"""
        if key in self.cache:
            item = self.cache[key]
            if time.time() - item['timestamp'] < self.ttl:
                return item['data']
        return None
    
    def set(self, key: str, data: Dict):
        """Cache the result"""
        self.cache[key] = {
            'data': data,
            'timestamp': time.time()
        }
```

## 2. Add Screenshot Comparison Mode

**Why**: Agents often need to detect UI changes between screenshots
**Implementation**: Simple pixel diff and structural similarity

```python
# In core/compare.py
from PIL import Image, ImageChops
import numpy as np

def compare_screenshots(
    image1_path: str, 
    image2_path: str,
    threshold: float = 0.95
) -> Dict[str, Any]:
    """Compare two screenshots and return similarity metrics"""
    img1 = Image.open(image1_path)
    img2 = Image.open(image2_path)
    
    # Ensure same size
    if img1.size != img2.size:
        img2 = img2.resize(img1.size, Image.LANCZOS)
    
    # Pixel difference
    diff = ImageChops.difference(img1, img2)
    
    # Calculate similarity score
    diff_array = np.array(diff)
    similarity = 1 - (np.count_nonzero(diff_array) / diff_array.size)
    
    # Highlight differences
    if similarity < threshold:
        diff_highlight = Image.blend(img1, diff, alpha=0.3)
        diff_path = image1_path.replace('.jpg', '_diff.jpg')
        diff_highlight.save(diff_path)
        
    return {
        "similarity": similarity,
        "identical": similarity >= threshold,
        "diff_image": diff_path if similarity < threshold else None
    }
```

## 3. Add OCR Text Extraction

**Why**: Agents often need to read text from screenshots
**Implementation**: Use pytesseract for simple OCR

```python
# In core/ocr.py
import pytesseract
from PIL import Image

def extract_text(
    image_path: str,
    region: Optional[Tuple[int, int, int, int]] = None
) -> Dict[str, Any]:
    """Extract text from screenshot using OCR"""
    img = Image.open(image_path)
    
    if region:
        img = img.crop(region)
    
    try:
        text = pytesseract.image_to_string(img)
        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
        
        # Get bounding boxes for text
        boxes = []
        for i in range(len(data['text'])):
            if data['conf'][i] > 0:
                boxes.append({
                    'text': data['text'][i],
                    'box': (data['left'][i], data['top'][i], 
                           data['width'][i], data['height'][i]),
                    'confidence': data['conf'][i]
                })
        
        return {
            "text": text.strip(),
            "boxes": boxes,
            "word_count": len(text.split())
        }
    except Exception as e:
        return {"error": str(e)}
```

## 4. Add Batch Processing Support

**Why**: Agents often need to process multiple screenshots
**Implementation**: Simple async batch processing

```python
# In core/batch.py
import asyncio
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor

async def batch_capture(
    targets: List[Dict[str, Any]],
    max_concurrent: int = 5
) -> List[Dict[str, Any]]:
    """Batch capture screenshots"""
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def capture_one(target):
        async with semaphore:
            return await asyncio.to_thread(
                capture_screenshot,
                **target
            )
    
    tasks = [capture_one(t) for t in targets]
    return await asyncio.gather(*tasks)

async def batch_describe(
    images: List[str],
    prompt: str = None,
    max_concurrent: int = 3
) -> List[Dict[str, Any]]:
    """Batch describe images"""
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def describe_one(image_path):
        async with semaphore:
            return await asyncio.to_thread(
                describe_image_content,
                image_path=image_path,
                prompt=prompt
            )
    
    tasks = [describe_one(img) for img in images]
    return await asyncio.gather(*tasks)
```

## 5. Add Screenshot Annotation

**Why**: Agents need to mark UI elements for human review
**Implementation**: Simple drawing utilities

```python
# In core/annotate.py
from PIL import Image, ImageDraw, ImageFont

def annotate_screenshot(
    image_path: str,
    annotations: List[Dict[str, Any]]
) -> str:
    """Add annotations to screenshot"""
    img = Image.open(image_path)
    draw = ImageDraw.Draw(img)
    
    for ann in annotations:
        if ann['type'] == 'box':
            draw.rectangle(ann['coords'], outline=ann.get('color', 'red'), width=3)
        elif ann['type'] == 'arrow':
            draw.line(ann['coords'], fill=ann.get('color', 'red'), width=3)
        elif ann['type'] == 'text':
            draw.text(ann['coords'], ann['text'], fill=ann.get('color', 'red'))
        elif ann['type'] == 'highlight':
            overlay = Image.new('RGBA', img.size, ann.get('color', 'yellow') + (128,))
            mask = Image.new('L', img.size, 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.rectangle(ann['coords'], fill=255)
            img = Image.composite(overlay, img.convert('RGBA'), mask).convert('RGB')
    
    output_path = image_path.replace('.jpg', '_annotated.jpg')
    img.save(output_path)
    return output_path
```

## 6. Add MCP Resource Provider

**Why**: Allow AI to browse available screenshots as resources
**Implementation**: Expose screenshots directory as MCP resources

```python
# In mcp/resources.py
@mcp.resource()
async def list_screenshots():
    """List available screenshots as MCP resources"""
    screenshots_dir = "./screenshots"
    screenshots = []
    
    for file in os.listdir(screenshots_dir):
        if file.endswith(('.jpg', '.png')):
            path = os.path.join(screenshots_dir, file)
            screenshots.append({
                "uri": f"screenshot://{file}",
                "name": file,
                "mimeType": "image/jpeg",
                "size": os.path.getsize(path),
                "created": os.path.getctime(path)
            })
    
    return {"resources": screenshots}

@mcp.resource()
async def get_screenshot(uri: str):
    """Get a specific screenshot as base64"""
    filename = uri.replace("screenshot://", "")
    path = os.path.join("./screenshots", filename)
    
    if os.path.exists(path):
        with open(path, 'rb') as f:
            return {
                "content": base64.b64encode(f.read()).decode(),
                "mimeType": "image/jpeg"
            }
    return {"error": "Screenshot not found"}
```

## 7. Add Prompts for Common Tasks

**Why**: Provide pre-configured prompts for common agent tasks
**Implementation**: MCP prompt templates

```python
# In mcp/prompts.py
@mcp.prompt()
async def ui_verification_prompt():
    """Prompt for UI verification tasks"""
    return {
        "name": "UI Verification",
        "description": "Verify UI elements match specifications",
        "template": """
Analyze this screenshot and verify:
1. All UI elements are present as specified
2. Text is readable and correctly positioned
3. Colors match the design system
4. Interactive elements are clearly visible
5. Layout is responsive and aligned

Report any discrepancies found.
"""
    }

@mcp.prompt()
async def error_detection_prompt():
    """Prompt for error detection"""
    return {
        "name": "Error Detection",
        "description": "Detect errors or issues in UI",
        "template": """
Examine this screenshot for:
1. Error messages or warnings
2. Broken layouts or misaligned elements
3. Missing images or icons
4. Incorrect data display
5. Accessibility issues

List all issues found with their locations.
"""
    }
```

## 8. Add Simple Monitoring

**Why**: Track tool usage and performance
**Implementation**: Basic metrics collection

```python
# In core/metrics.py
import time
from collections import defaultdict
from datetime import datetime

class SimpleMetrics:
    def __init__(self):
        self.counters = defaultdict(int)
        self.timings = defaultdict(list)
    
    def increment(self, name: str):
        """Increment a counter"""
        self.counters[name] += 1
    
    def time_operation(self, name: str):
        """Context manager for timing operations"""
        class Timer:
            def __enter__(timer_self):
                timer_self.start = time.time()
                return timer_self
            
            def __exit__(timer_self, *args):
                duration = time.time() - timer_self.start
                self.timings[name].append(duration)
        
        return Timer()
    
    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary"""
        summary = {
            "counters": dict(self.counters),
            "timings": {}
        }
        
        for name, times in self.timings.items():
            summary["timings"][name] = {
                "count": len(times),
                "avg": sum(times) / len(times),
                "min": min(times),
                "max": max(times)
            }
        
        return summary

# Global metrics instance
metrics = SimpleMetrics()
```

## Implementation Priority

1. **High Priority** (Easy wins):
   - Caching for AI responses
   - Screenshot comparison
   - Annotation support
   - MCP prompts

2. **Medium Priority** (More value):
   - OCR text extraction
   - Batch processing
   - MCP resources

3. **Low Priority** (Nice to have):
   - Monitoring/metrics

These improvements provide significant value without adding complexity that would confuse agents. Each feature is self-contained and follows the existing three-layer architecture.