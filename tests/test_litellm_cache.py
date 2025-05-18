#!/usr/bin/env python3
"""Tests for LiteLLM caching functionality"""

import pytest
import os
import tempfile
from PIL import Image, ImageDraw

from mcp_screenshot.core.litellm_cache import (
    initialize_litellm_cache,
    ensure_cache_initialized,
    test_cache_functionality
)
from mcp_screenshot.core.description import describe_image_content


def check_auth_error(result):
    """Check if result has authentication error and skip if needed"""
    if "error" in result and "AuthenticationError" in result["error"]:
        pytest.skip("Skipping test due to missing API credentials")


class TestLiteLLMCache:
    """Test LiteLLM caching functionality"""
    
    @pytest.fixture
    def test_image(self):
        """Create a test image"""
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            img = Image.new('RGB', (400, 300), 'white')
            draw = ImageDraw.Draw(img)
            draw.rectangle([50, 50, 150, 150], fill='red')
            draw.ellipse([200, 100, 300, 200], fill='blue')
            img.save(f.name)
            yield f.name
            os.unlink(f.name)
    
    def test_cache_initialization(self):
        """Test cache initialization"""
        # Test without Redis (should fall back to in-memory)
        is_redis = initialize_litellm_cache(
            redis_host="nonexistent",
            redis_port=6379
        )
        assert is_redis is False  # Should use in-memory cache
    
    def test_ensure_cache_singleton(self):
        """Test that cache initialization is singleton"""
        # First call initializes
        result1 = ensure_cache_initialized()
        # Second call should return same result
        result2 = ensure_cache_initialized()
        
        # Both should have same type (either both Redis or both in-memory)
        assert result1 == result2
    
    def test_cache_functionality_check(self):
        """Test the cache functionality test"""
        result = test_cache_functionality()
        
        assert "success" in result
        
        # If test failed due to authentication, skip the test
        if not result["success"] and "AuthenticationError" in result.get("error", ""):
            pytest.skip("Skipping test due to missing API credentials")
        
        assert "first_call_hit" in result
        assert "second_call_hit" in result
        assert "cache_working" in result
        
        # If successful, check cache behavior
        if result["success"]:
            # First call should be miss (False or None)
            assert result["first_call_hit"] in [False, None]
            # Second call should be hit (True) if cache is working
            if result["cache_working"]:
                assert result["second_call_hit"] is True
    
    def test_image_description_caching(self, test_image):
        """Test that image descriptions are cached"""
        prompt = "Test prompt for caching"
        
        # First call - should not be cached
        result1 = describe_image_content(
            test_image,
            prompt=prompt,
            enable_cache=True
        )
        
        check_auth_error(result1)
        assert "error" not in result1
        
        # Second call with same parameters - should use cache
        result2 = describe_image_content(
            test_image,
            prompt=prompt,
            enable_cache=True
        )
        assert "error" not in result2
        
        # Results should be identical if cache is working
        assert result1["description"] == result2["description"]
    
    def test_cache_disabled(self, test_image):
        """Test that caching can be disabled"""
        prompt = "Test prompt without caching"
        
        # Both calls with cache disabled
        result1 = describe_image_content(
            test_image,
            prompt=prompt,
            enable_cache=False
        )
        
        check_auth_error(result1)
        assert "error" not in result1
        
        result2 = describe_image_content(
            test_image,
            prompt=prompt,
            enable_cache=False
        )
        assert "error" not in result2
        
        # Both calls should work but not necessarily return identical results
        assert result1.get("filename") == result2.get("filename")
    
    def test_cache_with_different_prompts(self, test_image):
        """Test that different prompts don't share cache"""
        # First prompt
        result1 = describe_image_content(
            test_image,
            prompt="Describe the colors",
            enable_cache=True
        )
        
        check_auth_error(result1)
        assert "error" not in result1
        
        # Different prompt - should not use cache
        result2 = describe_image_content(
            test_image,
            prompt="Describe the shapes",
            enable_cache=True
        )
        assert "error" not in result2
        
        # Results should be different
        assert result1["description"] != result2["description"]
    
    def test_cache_ttl_parameter(self, test_image):
        """Test cache with custom TTL"""
        # Initialize with short TTL
        ensure_cache_initialized(ttl=60)  # 1 minute
        
        result = describe_image_content(
            test_image,
            prompt="Test TTL",
            enable_cache=True,
            cache_ttl=60
        )
        
        check_auth_error(result)
        assert "error" not in result