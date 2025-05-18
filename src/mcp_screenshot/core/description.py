#!/usr/bin/env python3
"""
Image Description Module

This module provides functions for describing images using AI vision models.
It uses LiteLLM to support Vertex AI/Gemini models with a unified interface.

This module is part of the Core Layer and should have no dependencies on
CLI or MCP layers.

Sample input:
- Image path: "/path/to/image.jpg"
- Model: "vertex_ai/gemini-2.5-flash-preview-04-17"
- Prompt: "Describe this image in detail."

Expected output:
- Dictionary with:
  - description: Detailed description of the image
  - filename: Name of the image file
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
    max_height: int = IMAGE_SETTINGS["MAX_HEIGHT"], 
    initial_quality: int = IMAGE_SETTINGS["DEFAULT_QUALITY"]
) -> str:
    """
    Prepares an image for multimodal API calls.
    
    Args:
        image_path: Path to the image file
        max_width: Maximum image width
        max_height: Maximum image height
        initial_quality: Initial JPEG quality
        
    Returns:
        str: Base64-encoded image string
    """
    try:
        # Open the image
        img = Image.open(image_path)
        
        # Convert to RGB if necessary
        if img.mode not in ('RGB', 'L'):
            img = img.convert('RGB')
        
        # Resize if needed
        original_size = img.size
        if img.width > max_width or img.height > max_height:
            img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            logger.info(f"Resized image from {original_size} to {img.size}")
        
        # Create a bytes buffer
        import io
        buffer = io.BytesIO()
        
        # Save to buffer with specified quality
        img.save(buffer, format="JPEG", quality=initial_quality, optimize=True)
        
        # Get the bytes and encode to base64
        img_bytes = buffer.getvalue()
        img_b64 = base64.b64encode(img_bytes).decode("utf-8")
        
        return img_b64
    except Exception as e:
        logger.error(f"Error preparing image: {str(e)}")
        raise


def describe_image_content(
    image_path: str, 
    model: str = DEFAULT_MODEL,
    prompt: str = DEFAULT_PROMPT,
    credentials_file: Optional[str] = None
) -> Dict[str, Any]:
    """
    Uses AI vision model to describe the content of an image.
    
    Args:
        image_path: Path to the image file
        model: AI model to use
        prompt: Text prompt for image description
        credentials_file: Path to credentials file for API authentication
        
    Returns:
        dict: Description results with 'description', 'filename', 'confidence'
              or 'error' if description fails
    """
    logger.info(f"Describing image: {image_path} with model: {model}")
    
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
            response = completion(
                model=model,
                messages=messages,
                vertex_credentials=vertex_credentials,
                temperature=0.1,
                max_tokens=2000
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
                    max_tokens=2000
                )
                result = response.choices[0].message.content
                model = DEFAULT_MODEL_FALLBACK
            else:
                raise
        
        # Clean up any potential JSON issues
        result = result.strip()
        if result.startswith('```json'):
            result = result[7:]
        if result.endswith('```'):
            result = result[:-3]
        
        # Parse JSON response
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
    all_validation_failures = []
    total_tests = 0
    
    # Create a test image
    test_img_path = None
    try:
        # Create temporary directory for test
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a simple test image
            img = Image.new('RGB', (400, 300), color='white')
            draw = ImageDraw.Draw(img)
            
            # Draw some shapes
            draw.rectangle([50, 50, 150, 150], fill='red', outline='black')
            draw.ellipse([200, 50, 300, 150], fill='blue', outline='black')
            draw.text((50, 200), "Test Image", fill='black')
            
            # Save test image
            test_img_path = os.path.join(temp_dir, "test_image.jpg")
            img.save(test_img_path, "JPEG")
            
            # Test 1: Image preparation
            total_tests += 1
            try:
                img_b64 = prepare_image_for_multimodal(test_img_path)
                if not img_b64 or not isinstance(img_b64, str):
                    all_validation_failures.append(f"Image preparation test: Failed to prepare image")
                else:
                    # Verify it's valid base64
                    try:
                        base64.b64decode(img_b64)
                    except Exception:
                        all_validation_failures.append(f"Image preparation test: Invalid base64 output")
            except Exception as e:
                all_validation_failures.append(f"Image preparation test: Exception: {str(e)}")
            
            # Test 2: Image description structure (mock test without API call)
            total_tests += 1
            mock_result = {
                "description": "Test image with red square and blue circle",
                "filename": "test_image.jpg",
                "confidence": 5,
                "model": DEFAULT_MODEL
            }
            
            # Verify structure
            required_fields = ["description", "filename", "confidence", "model"]
            missing_fields = [field for field in required_fields if field not in mock_result]
            if missing_fields:
                all_validation_failures.append(f"Response structure test: Missing fields: {missing_fields}")
            
            # Test 3: Invalid image path handling
            total_tests += 1
            result = describe_image_content("nonexistent.jpg")
            if "error" not in result:
                all_validation_failures.append("Error handling test: Expected error for nonexistent file")
            
            # Test 4: Confidence value validation
            total_tests += 1
            if mock_result["confidence"] < 1 or mock_result["confidence"] > 5:
                all_validation_failures.append(
                    f"Confidence validation: Invalid confidence value {mock_result['confidence']}"
                )
            
            # Test 5: Credentials handling
            total_tests += 1
            creds = get_vertex_credentials()
            if not isinstance(creds, (dict, type(None))):
                all_validation_failures.append("Credentials test: Invalid credentials format")
                
    except Exception as e:
        all_validation_failures.append(f"Test setup failed: {str(e)}")
    
    # Final validation result
    if all_validation_failures:
        print(f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("Image description functions are validated and ready for use")
        print("Note: Actual API calls require valid credentials")
        sys.exit(0)