#!/usr/bin/env python3
"""
Batch Processing Module

This module provides asynchronous batch processing capabilities for handling
multiple screenshots and descriptions efficiently with progress tracking.

This module is part of the Core Layer.
"""

import asyncio
from typing import List, Dict, Any, Optional, Callable, Union
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import time

from loguru import logger
from tqdm.asyncio import tqdm
import litellm

from mcp_screenshot.core.capture import capture_screenshot, capture_browser_screenshot
from mcp_screenshot.core.description import describe_image_content, prepare_image_for_multimodal, DESCRIPTION_SCHEMA
from mcp_screenshot.core.constants import DEFAULT_MODEL, IMAGE_SETTINGS


class BatchProcessor:
    """Handles batch processing of screenshots with progress tracking."""
    
    def __init__(self, max_concurrent: int = 5):
        """
        Initialize batch processor.
        
        Args:
            max_concurrent: Maximum number of concurrent operations
        """
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.results = []
        
    async def process_batch_captures(
        self,
        targets: List[Dict[str, Any]],
        progress_callback: Optional[Callable] = None
    ) -> List[Dict[str, Any]]:
        """
        Batch capture screenshots from URLs or screens.
        
        Args:
            targets: List of capture targets with parameters
            progress_callback: Optional callback for progress updates
            
        Returns:
            List of capture results
        """
        logger.info(f"Starting batch capture of {len(targets)} targets")
        
        async def capture_one(target: Dict[str, Any], pbar: tqdm) -> Dict[str, Any]:
            """Capture a single screenshot."""
            async with self.semaphore:
                try:
                    # Determine capture type
                    if "url" in target:
                        # Web capture - run in thread to avoid blocking
                        result = await asyncio.to_thread(
                            capture_browser_screenshot,
                            url=target["url"],
                            quality=target.get("quality", IMAGE_SETTINGS["DEFAULT_QUALITY"]),
                            wait_time=target.get("wait_time", 3),
                            output_dir=target.get("output_dir", "./screenshots")
                        )
                    else:
                        # Screen capture
                        result = await asyncio.to_thread(
                            capture_screenshot,
                            quality=target.get("quality", IMAGE_SETTINGS["DEFAULT_QUALITY"]),
                            region=target.get("region"),
                            zoom_center=target.get("zoom_center"),
                            zoom_factor=target.get("zoom_factor", 1.0)
                        )
                    
                    result["target_id"] = target.get("id", str(id(target)))
                    pbar.update(1)
                    
                    if progress_callback:
                        await progress_callback(result)
                        
                    return result
                    
                except Exception as e:
                    logger.error(f"Batch capture error: {str(e)}")
                    pbar.update(1)
                    return {
                        "error": str(e),
                        "target_id": target.get("id", str(id(target))),
                        "success": False
                    }
        
        # Create progress bar
        with tqdm(total=len(targets), desc="Capturing screenshots") as pbar:
            # Create tasks
            tasks = [capture_one(target, pbar) for target in targets]
            
            # Execute all tasks
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
        # Process results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "error": str(result),
                    "target_id": targets[i].get("id", str(id(targets[i]))),
                    "success": False
                })
            else:
                processed_results.append(result)
                
        logger.info(f"Completed batch capture: {len(processed_results)} results")
        return processed_results
    
    async def process_batch_descriptions(
        self,
        images: List[Union[str, Dict[str, Any]]],
        prompt: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        progress_callback: Optional[Callable] = None
    ) -> List[Dict[str, Any]]:
        """
        Batch describe images using AI.
        
        Args:
            images: List of image paths or dicts with path and custom prompt
            prompt: Default prompt for all images
            model: AI model to use
            progress_callback: Optional callback for progress updates
            
        Returns:
            List of description results
        """
        logger.info(f"Starting batch description of {len(images)} images")
        
        async def describe_one(image_data: Union[str, Dict[str, Any]], pbar: tqdm) -> Dict[str, Any]:
            """Describe a single image."""
            async with self.semaphore:
                try:
                    # Extract image path and prompt
                    if isinstance(image_data, str):
                        image_path = image_data
                        image_prompt = prompt or "Describe this image in detail"
                        image_id = image_path
                    else:
                        image_path = image_data["path"]
                        image_prompt = image_data.get("prompt", prompt) or "Describe this image in detail"
                        image_id = image_data.get("id", image_path)
                    
                    # Prepare image for AI
                    image_content = prepare_image_for_multimodal(image_path)
                    
                    # Create messages for LiteLLM
                    messages = [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": image_prompt},
                                {"type": "image_url", "image_url": f"data:image/jpeg;base64,{image_content}"}
                            ]
                        }
                    ]
                    
                    # Use async completion
                    response = await litellm.acompletion(
                        model=model,
                        messages=messages,
                        response_format={
                            "type": "json_schema",
                            "json_schema": {
                                "name": "image_description",
                                "schema": DESCRIPTION_SCHEMA
                            }
                        }
                    )
                    
                    # Parse response
                    result = response.model_dump()
                    description_data = result["choices"][0]["message"]["content"]
                    
                    if isinstance(description_data, str):
                        import json
                        description_data = json.loads(description_data)
                    
                    description_data["image_id"] = image_id
                    description_data["model"] = model
                    description_data["success"] = True
                    
                    pbar.update(1)
                    
                    if progress_callback:
                        await progress_callback(description_data)
                        
                    return description_data
                    
                except Exception as e:
                    logger.error(f"Batch description error: {str(e)}")
                    pbar.update(1)
                    return {
                        "error": str(e),
                        "image_id": image_id if 'image_id' in locals() else str(image_data),
                        "success": False
                    }
        
        # Create progress bar
        with tqdm(total=len(images), desc="Describing images") as pbar:
            # Create tasks
            tasks = [describe_one(img, pbar) for img in images]
            
            # Execute all tasks
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                image_id = images[i] if isinstance(images[i], str) else images[i].get("id", images[i]["path"])
                processed_results.append({
                    "error": str(result),
                    "image_id": image_id,
                    "success": False
                })
            else:
                processed_results.append(result)
                
        logger.info(f"Completed batch description: {len(processed_results)} results")
        return processed_results
    
    async def process_capture_and_describe(
        self,
        targets: List[Dict[str, Any]],
        prompt: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        progress_callback: Optional[Callable] = None
    ) -> List[Dict[str, Any]]:
        """
        Capture screenshots and describe them in one batch operation.
        
        Args:
            targets: List of capture targets
            prompt: Description prompt
            model: AI model to use
            progress_callback: Optional progress callback
            
        Returns:
            List of combined capture and description results
        """
        logger.info(f"Starting combined capture and describe for {len(targets)} targets")
        
        # First, capture all screenshots
        capture_results = await self.process_batch_captures(targets, progress_callback)
        
        # Filter successful captures and prepare for description
        successful_captures = []
        combined_results = []
        
        for i, capture_result in enumerate(capture_results):
            if capture_result.get("success", False) and "file" in capture_result:
                successful_captures.append({
                    "path": capture_result["file"],
                    "id": capture_result.get("target_id", i),
                    "prompt": targets[i].get("prompt", prompt)
                })
                combined_results.append(capture_result)
            else:
                combined_results.append(capture_result)
        
        # Describe successful captures
        if successful_captures:
            description_results = await self.process_batch_descriptions(
                successful_captures,
                prompt=prompt,
                model=model,
                progress_callback=progress_callback
            )
            
            # Merge results
            desc_by_id = {desc["image_id"]: desc for desc in description_results}
            
            for i, result in enumerate(combined_results):
                if result.get("success", False):
                    target_id = result.get("target_id", i)
                    if target_id in desc_by_id:
                        result["description"] = desc_by_id[target_id]
        
        return combined_results


# Convenience functions for direct use
async def batch_capture(
    targets: List[Dict[str, Any]],
    max_concurrent: int = 5
) -> List[Dict[str, Any]]:
    """
    Convenience function for batch capture.
    
    Args:
        targets: List of capture targets
        max_concurrent: Maximum concurrent operations
        
    Returns:
        List of capture results
    """
    processor = BatchProcessor(max_concurrent=max_concurrent)
    return await processor.process_batch_captures(targets)


async def batch_describe(
    images: List[Union[str, Dict[str, Any]]],
    prompt: Optional[str] = None,
    model: str = DEFAULT_MODEL,
    max_concurrent: int = 3
) -> List[Dict[str, Any]]:
    """
    Convenience function for batch description.
    
    Args:
        images: List of image paths or configs
        prompt: Description prompt
        model: AI model to use
        max_concurrent: Maximum concurrent operations
        
    Returns:
        List of description results
    """
    processor = BatchProcessor(max_concurrent=max_concurrent)
    return await processor.process_batch_descriptions(
        images,
        prompt=prompt,
        model=model
    )


if __name__ == "__main__":
    """Self-validation tests for batch processing."""
    async def test_batch_processing():
        # Test batch capture
        targets = [
            {"region": "center", "id": "test1"},
            {"region": "full", "id": "test2"}
        ]
        
        results = await batch_capture(targets, max_concurrent=2)
        assert len(results) == 2
        print(f"✓ Batch capture test passed: {len(results)} results")
        
        # Test batch description
        if results[0].get("file"):
            images = [r["file"] for r in results if "file" in r]
            desc_results = await batch_describe(images, max_concurrent=2)
            print(f"✓ Batch description test passed: {len(desc_results)} results")
    
    asyncio.run(test_batch_processing())