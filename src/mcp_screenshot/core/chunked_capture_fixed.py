#!/usr/bin/env python3
"""
Fixed chunked screenshot capture for very tall pages.

This module provides functionality to capture tall pages in chunks
and analyze each chunk separately for better readability.
"""

import os
import time
import asyncio
import io
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

from loguru import logger
from PIL import Image

from mcp_screenshot.core.constants import IMAGE_SETTINGS, BROWSER_SETTINGS
from mcp_screenshot.core.utils import validate_quality, ensure_directory
from mcp_screenshot.core.description import describe_image_content


async def capture_page_chunks_async(
    url: str,
    output_dir: str = "./screenshots",
    wait_time: int = 3,
    quality: int = IMAGE_SETTINGS["DEFAULT_QUALITY"],
    width: int = 1920,
    height: int = 1080,
    chunk_height: int = 1080,
    max_chunks: int = 20
) -> Dict[str, Any]:
    """
    Capture a webpage in viewport-sized chunks for better readability.
    
    Args:
        url: URL to capture
        output_dir: Directory to save screenshots
        wait_time: Seconds to wait for page load
        quality: JPEG compression quality
        width: Browser viewport width
        height: Browser viewport height
        chunk_height: Height of each chunk
        max_chunks: Maximum number of chunks to capture
        
    Returns:
        dict: Result with list of chunk files and metadata
    """
    if not PLAYWRIGHT_AVAILABLE:
        return {"error": "Playwright not available"}
    
    logger.info(f"Chunked capture for {url}")
    ensure_directory(output_dir)
    
    chunks = []
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=BROWSER_SETTINGS.get("HEADLESS", True),
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            
            context = await browser.new_context(
                viewport={'width': width, 'height': height}
            )
            
            page = await context.new_page()
            
            # Navigate to URL
            logger.info(f"Loading page: {url}")
            await page.goto(url, wait_until='networkidle')
            await page.wait_for_timeout(wait_time * 1000)
            
            # Get total page height
            total_height = await page.evaluate("() => document.body.scrollHeight")
            logger.info(f"Total page height: {total_height}px")
            
            # Calculate number of chunks
            num_chunks = min(
                max_chunks,
                (total_height + chunk_height - 1) // chunk_height
            )
            
            logger.info(f"Capturing {num_chunks} chunks")
            
            # Capture each chunk
            for i in range(num_chunks):
                scroll_y = i * chunk_height
                
                # Scroll to position
                await page.evaluate(f"window.scrollTo(0, {scroll_y})")
                await page.wait_for_timeout(500)  # Let content load
                
                # Take screenshot
                timestamp = int(time.time() * 1000)
                filename = f"chunk_{i}_{timestamp}.jpeg"
                filepath = os.path.join(output_dir, filename)
                
                screenshot = await page.screenshot()
                
                # Convert to JPEG
                img = Image.open(io.BytesIO(screenshot))
                img.save(filepath, format="JPEG", quality=quality, optimize=True)
                
                chunk_info = {
                    "chunk_number": i,
                    "file": filepath,
                    "scroll_position": scroll_y,
                    "dimensions": {"width": width, "height": height}
                }
                
                chunks.append(chunk_info)
                logger.info(f"Captured chunk {i} at y={scroll_y}")
            
            await browser.close()
            
            return {
                "url": url,
                "chunks": chunks,
                "total_height": total_height,
                "num_chunks": num_chunks,
                "chunk_height": chunk_height,
                "success": True
            }
            
    except Exception as e:
        logger.error(f"Chunked capture failed: {str(e)}", exc_info=True)
        return {"error": str(e), "success": False}


async def capture_and_describe_chunks(
    url: str,
    output_dir: str = "./screenshots",
    wait_time: int = 3,
    quality: int = IMAGE_SETTINGS["DEFAULT_QUALITY"],
    chunk_height: int = 1080,
    max_chunks: int = 20,
    description_prompt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Capture page in chunks and describe each chunk, then summarize.
    
    Args:
        url: URL to capture
        output_dir: Directory for screenshots
        wait_time: Page load wait time
        quality: JPEG quality
        chunk_height: Height of each chunk
        max_chunks: Maximum chunks to capture
        description_prompt: Custom prompt for descriptions
        
    Returns:
        dict: Result with chunks, descriptions, and overall summary
    """
    # First capture all chunks
    capture_result = await capture_page_chunks_async(
        url=url,
        output_dir=output_dir,
        wait_time=wait_time,
        quality=quality,
        chunk_height=chunk_height,
        max_chunks=max_chunks
    )
    
    if not capture_result.get("success"):
        return capture_result
    
    chunks = capture_result["chunks"]
    descriptions = []
    
    # Describe each chunk
    for i, chunk in enumerate(chunks):
        chunk_prompt = description_prompt or f"""
        This is chunk {i+1} of {len(chunks)} from a long webpage.
        Describe what you see in this section, focusing on:
        - Main headings and sections
        - Code examples if present
        - Key information and details
        - Navigation elements if visible
        
        Be specific about the content in this particular section.
        """
        
        try:
            # Use sync function in executor to avoid async issues
            loop = asyncio.get_event_loop()
            description = await loop.run_in_executor(
                None,
                describe_image_content,
                chunk["file"],
                chunk_prompt,
                None,  # model
                True,  # enable_cache
                3600   # cache_ttl
            )
            
            descriptions.append({
                "chunk_number": i,
                "description": description.get("description", ""),
                "confidence": description.get("confidence", 0)
            })
            
        except Exception as e:
            logger.error(f"Failed to describe chunk {i}: {str(e)}")
            descriptions.append({
                "chunk_number": i,
                "description": f"Error describing chunk: {str(e)}",
                "confidence": 0
            })
    
    # Create overall summary
    summary_prompt = f"""
    Based on these {len(descriptions)} chunk descriptions from a webpage,
    provide a comprehensive summary of the entire page content.
    
    Chunk descriptions:
    {chr(10).join([f"Chunk {d['chunk_number']+1}: {d['description']}" for d in descriptions])}
    
    Synthesize all chunks into a cohesive overview that includes:
    1. The main topic and purpose of the page
    2. Key sections and their content
    3. Important code examples or configurations
    4. Overall structure and navigation
    """
    
    # Use the first chunk image for summary (could be improved)
    try:
        loop = asyncio.get_event_loop()
        summary_result = await loop.run_in_executor(
            None,
            describe_image_content,
            chunks[0]["file"],
            summary_prompt,
            None,  # model
            True,  # enable_cache
            3600   # cache_ttl
        )
        
        overall_summary = summary_result.get("description", "Unable to generate summary")
    except Exception as e:
        overall_summary = f"Error generating summary: {str(e)}"
    
    return {
        "url": url,
        "chunks": chunks,
        "chunk_descriptions": descriptions,
        "overall_summary": overall_summary,
        "total_height": capture_result["total_height"],
        "num_chunks": len(chunks),
        "success": True
    }