#!/usr/bin/env python3
"""
AI-powered Image Description

This module provides AI-powered image description capabilities using LiteLLM
with support for multiple vision models including Google's Gemini and OpenAI's GPT-4V.

Key features:
  - Multi-model support (Gemini, GPT-4, Claude)
  - Automatic fallback to alternative models
  - Structured JSON responses
  - Built-in LiteLLM caching (Redis or in-memory)

This module is part of the Core Layer.

Returns JSON with:
  - description: Detailed text description
  - filename: Image filename
  - confidence: Score (1-5) indicating description accuracy
  - model: Model used for description
  - On error: error message
"""

import os
import json
import base64
from typing import Dict, Any, Optional, Union

from loguru import logger
from PIL import Image
from litellm import completion

from mcp_screenshot.core.constants import (
    IMAGE_SETTINGS, 
    DEFAULT_MODEL, 
    DEFAULT_MODEL_FALLBACK,
    DEFAULT_PROMPT
)
from mcp_screenshot.core.utils import get_vertex_credentials
from mcp_screenshot.core.litellm_cache import ensure_cache_initialized


# Define the response schema for image description
DESCRIPTION_SCHEMA = {
    "type": "object",
    "properties": {
        "description": {
            "type": "string",
            "description": "Detailed description of the image content"
        },
        "filename": {
            "type": "string",
            "description": "The name of the image file"
        },
        "confidence": {
            "type": "integer",
            "description": "Confidence score (1-5) on accuracy of description given image quality and possible compression artifacts",
            "minimum": 1,
            "maximum": 5
        }
    },
    "required": ["description", "filename", "confidence"]
}


def prepare_image_for_multimodal(
    image_path: str, 
    max_width: int = IMAGE_SETTINGS["MAX_WIDTH"],
    quality: int = IMAGE_SETTINGS["DEFAULT_QUALITY"]
) -> str:
    """
    Prepare an image for multimodal input. Resize if needed and encode to base64.
    
    Args:
        image_path: Path to the image file
        max_width: Maximum width for resize (maintains aspect ratio)
        quality: JPEG compression quality (1-100)
        
    Returns:
        Base64 encoded string of the processed image
    """
    logger.debug(f"Preparing image for multimodal: {image_path}")
    
    try:
        # Open the image
        with Image.open(image_path) as img:
            # Convert RGBA to RGB if needed
            if img.mode == 'RGBA':
                rgb_image = Image.new('RGB', img.size, (255, 255, 255))
                rgb_image.paste(img, mask=img.split()[3])
                img = rgb_image
            
            # Calculate resize dimensions if needed
            width, height = img.size
            if width > max_width:
                ratio = max_width / width
                new_width = max_width
                new_height = int(height * ratio)
                logger.debug(f"Resizing image from {width}x{height} to {new_width}x{new_height}")
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Convert to JPEG and encode to base64
            import io
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=quality)
            image_bytes = buffer.getvalue()
            
            # Encode to base64
            image_b64 = base64.b64encode(image_bytes).decode('utf-8')
            logger.debug(f"Image prepared: {len(image_b64)} bytes (base64)")
            
            return image_b64
            
    except Exception as e:
        logger.error(f"Failed to prepare image: {str(e)}")
        raise


def describe_image_content(
    image_path: str,
    model: str = DEFAULT_MODEL,
    prompt: str = DEFAULT_PROMPT,
    credentials_file: Optional[str] = None,
    enable_cache: bool = True,
    cache_ttl: int = 3600
) -> Dict[str, Any]:
    """
    Describe the content of an image using AI vision models with LiteLLM caching.
    
    Args:
        image_path: Path to the image file
        model: AI model to use
        prompt: Text prompt for image description
        credentials_file: Path to credentials file for API authentication
        enable_cache: Whether to enable LiteLLM caching
        cache_ttl: Cache TTL in seconds (default 1 hour)
        
    Returns:
        dict: Description results with 'description', 'filename', 'confidence'
              or 'error' if description fails
    """
    logger.info(f"Describing image: {image_path} with model: {model}")
    
    # Initialize LiteLLM cache if requested
    if enable_cache:
        ensure_cache_initialized(ttl=cache_ttl)
    
    try:
        # Prepare the image
        image_b64 = prepare_image_for_multimodal(image_path)
        
        # Extract the filename from the path
        filename = os.path.basename(image_path)
        
        # Get credentials
        vertex_credentials = get_vertex_credentials(credentials_file)
        
        # Construct messages with multimodal content
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text", 
                        "text": f"{prompt} Respond with a JSON object that includes: "
                               f"1) a 'description' field with your detailed description, "
                               f"2) a 'filename' field with the value '{filename}', and "
                               f"3) a 'confidence' field with a number from 1-5 (5 being highest) "
                               f"indicating your confidence in the accuracy of your description "
                               f"considering image quality and compression artifacts."
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}
                    }
                ]
            }
        ]
        
        try:
            # Try with primary model
            # LiteLLM will automatically use cache if enabled
            response = completion(
                model=model,
                messages=messages,
                vertex_credentials=vertex_credentials,
                temperature=0.1,
                max_tokens=2000,
                caching=enable_cache  # Enable caching for this call
            )
            
            # Parse the response
            result = response.choices[0].message.content
            
        except Exception as e:
            if "model" in str(e).lower() and DEFAULT_MODEL_FALLBACK:
                # Try fallback model
                logger.warning(f"Primary model failed, trying fallback: {DEFAULT_MODEL_FALLBACK}")
                
                response = completion(
                    model=DEFAULT_MODEL_FALLBACK,
                    messages=messages,
                    vertex_credentials=vertex_credentials,
                    temperature=0.1,
                    max_tokens=2000,
                    caching=enable_cache
                )
                
                result = response.choices[0].message.content
                model = DEFAULT_MODEL_FALLBACK
            else:
                raise
        
        # Try to parse as JSON
        try:
            parsed_result = json.loads(result)
        except json.JSONDecodeError:
            # If JSON parsing fails, create a basic response
            parsed_result = {
                "description": result,
                "filename": filename,
                "confidence": 3
            }
        
        # Add model information
        parsed_result["model"] = model
        
        # Check if this was a cache hit
        if hasattr(response, '_hidden_params'):
            cache_hit = response._hidden_params.get('cache_hit', None)
            if cache_hit:
                logger.info("Using cached image description")
        
        logger.info(f"Successfully described image with confidence: {parsed_result.get('confidence', 'N/A')}")
        return parsed_result
        
    except Exception as e:
        logger.error(f"Image description failed: {str(e)}", exc_info=True)
        return {"error": f"Image description failed: {str(e)}"}


def generate_image_embedding(
    image_path: str,
    model: str = DEFAULT_MODEL,
    prompt: str = DEFAULT_PROMPT,
    credentials_file: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate embeddings/analysis for an image using vision models.
    
    This is an alias for describe_image_content for compatibility.
    
    Args:
        image_path: Path to the image file
        model: AI model to use
        prompt: Text prompt for image analysis
        credentials_file: Path to credentials file
        
    Returns:
        dict: Analysis results or error
    """
    return describe_image_content(image_path, model, prompt, credentials_file)


if __name__ == "__main__":
    """Validate image description functionality with sample image"""
    import sys
    import tempfile
    from PIL import Image, ImageDraw
    
    # List to track all validation failures
    validation_errors = []
    
    logger.info("=== Validating Image Description Module ===")
    
    # Create a test image
    try:
        logger.info("Creating test image...")
        test_image = Image.new('RGB', (400, 300), 'white')
        draw = ImageDraw.Draw(test_image)
        draw.rectangle([50, 50, 150, 150], fill='red')
        draw.ellipse([200, 100, 300, 200], fill='blue')
        draw.text((100, 250), "Test Image", fill='black')
        
        # Save test image
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            test_image.save(tmp.name, 'JPEG')
            test_image_path = tmp.name
            logger.success(f"Test image created: {test_image_path}")
    except Exception as e:
        validation_errors.append(f"Failed to create test image: {str(e)}")
        logger.error(validation_errors[-1])
    
    # Test 1: Basic image preparation
    try:
        logger.info("Test 1: Image preparation...")
        image_b64 = prepare_image_for_multimodal(test_image_path)
        if len(image_b64) > 0:
            logger.success("✅ Image preparation successful")
        else:
            raise ValueError("Empty base64 string")
    except Exception as e:
        validation_errors.append(f"Image preparation failed: {str(e)}")
        logger.error(validation_errors[-1])
    
    # Test 2: Image description with cache
    try:
        logger.info("Test 2: Image description with caching...")
        result = describe_image_content(
            test_image_path,
            prompt="Describe the shapes and colors in this test image"
        )
        
        if "error" not in result:
            logger.success("✅ Image description successful")
            logger.info(f"Description: {result.get('description', '')[:100]}...")
            logger.info(f"Confidence: {result.get('confidence', 'N/A')}")
        else:
            raise ValueError(result["error"])
    except Exception as e:
        validation_errors.append(f"Image description failed: {str(e)}")
        logger.error(validation_errors[-1])
    
    # Test 3: Test caching functionality
    try:
        logger.info("Test 3: Testing cache functionality...")
        # Second call should hit cache
        result2 = describe_image_content(
            test_image_path,
            prompt="Describe the shapes and colors in this test image"  # Same prompt
        )
        
        if "error" not in result2:
            logger.success("✅ Second description successful (should use cache)")
        else:
            raise ValueError(result2["error"])
    except Exception as e:
        validation_errors.append(f"Cache test failed: {str(e)}")
        logger.error(validation_errors[-1])
    
    # Clean up
    try:
        os.unlink(test_image_path)
        logger.debug("Test image cleaned up")
    except:
        pass
    
    # Report results
    logger.info("\n=== Validation Summary ===")
    if not validation_errors:
        logger.success("✅ All tests passed!")
        sys.exit(0)
    else:
        logger.error(f"❌ {len(validation_errors)} test(s) failed:")
        for error in validation_errors:
            logger.error(f"  - {error}")
        sys.exit(1)